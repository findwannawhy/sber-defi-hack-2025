import { ethers } from "ethers";
import dotenv from 'dotenv';
import pg from 'pg';
import axios from 'axios';
import FormData from 'form-data';
import fs from 'fs/promises'; // Для создания временного HTML файла
import path from 'path'; // Для работы с путями к файлам
import os from 'os'; // Для получения временной директории

dotenv.config();

const ETHERSCAN_API_KEY = process.env.ETHERSCAN_API_KEY || '';

// --- Типы и Интерфейсы ---
type SupportedNetwork = 'base' | 'mainnet' | 'arbitrum';

interface ChainConfig {
  [key: string]: string;
}

interface EtherscanResponse {
  status: string;
  message: string;
  result: Array<{
      SourceCode: string;
      [key: string]: any;
  }>;
}

interface SourceCodeJson {
  sources: {
      [key: string]: {
          content: string;
      };
  };
}


interface ContractSourceCodeResponse {
  status: string;
  message: string;
  result: Array<{
    SourceCode: string;
    ABI: string;
    ContractName: string;
    CompilerVersion: string;
    OptimizationUsed: string;
    Runs: string;
    ConstructorArguments: string;
    EVMVersion: string;
    Library: string;
    LicenseType: string;
    Proxy: string;
    Implementation: string;
    SwarmSource: string;
  }>;
}

interface ImplementationDetails {
  address: string;
  sourceCode: { [key: string]: { content: string; } } | null;
  network: SupportedNetwork;
}

interface DatabaseContract {
  address: string;
  network: SupportedNetwork;
}

// --- Конфигурация из .env ---
const rpcUrls: Record<SupportedNetwork, string> = {
  base: process.env.ALCHEMY_BASE_URL || '',
  mainnet: process.env.ALCHEMY_ETHEREUM_URL || '',
  arbitrum: process.env.ALCHEMY_ARBITRUM_URL || '',
};

const explorerApiUrls: Record<SupportedNetwork, string> = {
  base: 'https://api.basescan.org/api',
  mainnet: 'https://api.etherscan.io/api',
  arbitrum: 'https://api.arbiscan.io/api',
};

const explorerApiKeys: Record<SupportedNetwork, string> = {
  base: process.env.BASESCAN_API_KEY || '',
  mainnet: process.env.ETHERSCAN_API_KEY || '',
  arbitrum: process.env.ARBISCAN_API_KEY || '',
};

const backendNotificationUrl = process.env.BACKEND_NOTIFICATION_URL || '';
const dbPollIntervalMinutes = parseInt(process.env.DB_POLL_INTERVAL_MINUTES || '5', 10);

if (!rpcUrls.base || !explorerApiKeys.base) {
  console.error("BASE_RPC_URL and BASESCAN_API_KEY must be set in .env");
  process.exit(1);
}
if (!backendNotificationUrl) {
  console.error("BACKEND_NOTIFICATION_URL must be set in .env");
  process.exit(1);
}


// --- PostgreSQL Клиент ---
const pool = new pg.Pool({
  host: process.env.PGHOST,
  user: process.env.PGUSER,
  password: process.env.PGPASSWORD,
  database: process.env.PGDATABASE,
  port: parseInt(process.env.PGPORT || '5432', 10),
});

pool.on('error', (err) => {
  console.error('Unexpected error on idle client', err);
  process.exit(-1);
});

// --- Глобальное состояние ---
const currentImplementations: Map<string, ImplementationDetails> = new Map(); // key: `${address}_${network}`
const activeProxies: Map<string, ethers.Contract> = new Map(); // key: `${address}_${network}`
const ethersProviders: Map<SupportedNetwork, ethers.JsonRpcProvider> = new Map();

const proxyAbi = [
  "event Upgraded(address indexed implementation)",
  "function implementation() view returns (address)"
];

// --- Вспомогательные функции ---

function getEthersProvider(network: SupportedNetwork): ethers.JsonRpcProvider {
  if (!ethersProviders.has(network)) {
    const rpcUrl = rpcUrls[network];
    if (!rpcUrl) {
      throw new Error(`RPC URL for network ${network} is not configured.`);
    }
    ethersProviders.set(network, new ethers.JsonRpcProvider(rpcUrl));
  }
  return ethersProviders.get(network)!;
}

export async function getContractSourceCode(
  contractAddress: string,
  chain: string
): Promise<{ [key: string]: { content: string; } } | null> {
  const chains: ChainConfig = {
      'mainnet': '1',
      'base': '8453',
      'arbitrum': '42161',
  };

  const apiUrl = "https://api.etherscan.io/v2/api";
  const params = {
      chainid: chains[chain],
      module: "contract",
      action: "getsourcecode",
      address: contractAddress,
      apikey: ETHERSCAN_API_KEY
  };

  try {
      const response = await axios.get<EtherscanResponse>(apiUrl, { params });
      const data = response.data;

      if (data.status === "1" && data.message === "OK") {
          const sourceCodeInfo = data.result[0];
          const sourceCode = sourceCodeInfo.SourceCode;

          if (sourceCode && sourceCode.startsWith('{')) {
              if (sourceCode.startsWith('{{') && sourceCode.endsWith('}}')) {
                  const sourceCodeJson = JSON.parse(sourceCode.slice(1, -1)) as SourceCodeJson;
                  return sourceCodeJson.sources;
              } else {
                  const parsedSource = JSON.parse(sourceCode) as SourceCodeJson;
                  return parsedSource.sources;
              }
          } else if (sourceCode) {
              return { [sourceCodeInfo.ContractName]: { content: sourceCode } };
          } else {
              console.log(`Исходный код для контракта ${contractAddress} не найден или не верифицирован.`);
              return null;
          }
      } else {
          console.log(`Ошибка API Etherscan: ${data.message || 'Неизвестная ошибка'} (Result: ${data.result})`);
          return null;
      }
  } catch (error) {
      if (axios.isAxiosError(error)) {
          console.log(`Ошибка сети при запросе к Etherscan API: ${error.message}`);
      } else if (error instanceof SyntaxError) {
          console.log("Ошибка декодирования JSON из поля SourceCode.");
          return null;
      } else {
          console.log(`Неожиданная ошибка: ${error instanceof Error ? error.message : String(error)}`);
      }
      return null;
  }
}

// --- Заглушки для будущей реализации ---
function generateHtmlDiff(
  contractAddress: string, 
  network: SupportedNetwork, 
  oldCode: { [key: string]: { content: string; } } | null, 
  newCode: { [key: string]: { content: string; } } | null, 
  oldImplAddress: string, 
  newImplAddress: string
): string {
  const formatSourceCode = (code: { [key: string]: { content: string; } } | null): string => {
    if (!code) return 'Not available';
    return Object.entries(code)
      .map(([filename, { content }]) => `<h3>${filename}</h3><pre>${content}</pre>`)
      .join('\n');
  };

  const changes = `
    <h1>Contract Upgrade Notification</h1>
    <p><strong>Address:</strong> ${contractAddress}</p>
    <p><strong>Network:</strong> ${network}</p>
    <p><strong>Implementation changed:</strong></p>
    <p>From: ${oldImplAddress}</p>
    <p>To: ${newImplAddress}</p>
    <h2>Old Source Code (Implementation: ${oldImplAddress}):</h2>
    ${formatSourceCode(oldCode)}
    <h2>New Source Code (Implementation: ${newImplAddress}):</h2>
    ${formatSourceCode(newCode)}
    <!-- Место для графа от Владимира -->
  `;
  return `<!DOCTYPE html><html><head><title>Contract Update: ${contractAddress}</title></head><body>${changes}</body></html>`;
}

async function sendNotificationToBackend(
  address: string, 
  network: SupportedNetwork, 
  oldImplementationAddress: string, 
  newImplementationAddress: string, 
  oldCode: { [key: string]: { content: string; } } | null, 
  newCode: { [key: string]: { content: string; } } | null
): Promise<void> {
  console.log(`Preparing notification for ${address} on ${network}. Implementation: ${oldImplementationAddress} -> ${newImplementationAddress}`);
  
  const htmlContent = generateHtmlDiff(address, network, oldCode, newCode, oldImplementationAddress, newImplementationAddress);
  const tempHtmlDir = path.join(os.tmpdir(), 'contract_updates');
  await fs.mkdir(tempHtmlDir, { recursive: true });
  const tempHtmlPath = path.join(tempHtmlDir, `update_${network}_${address}_${Date.now()}.html`);
  
  try {
    await fs.writeFile(tempHtmlPath, htmlContent);

    const formData = new FormData();
    formData.append('address', address);
    formData.append('network', network);
    const fileBuffer = await fs.readFile(tempHtmlPath);
    formData.append('file', fileBuffer, {
        filename: path.basename(tempHtmlPath),
        contentType: 'text/html',
    });
    
    console.log(`Sending notification to backend: ${backendNotificationUrl} for ${address} on ${network}`);
    await axios.post(backendNotificationUrl, formData, {
      headers: formData.getHeaders(),
    });
    console.log(`Notification sent successfully for ${address} on ${network}.`);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      console.error(`Error sending notification for ${address} on ${network} to backend:`, error.response?.data || error.message);
    } else {
      console.error(`Error processing notification for ${address} on ${network}:`, error);
    }
  } finally {
      try {
          await fs.unlink(tempHtmlPath);
      } catch (e) {
          console.warn(`Could not delete temp file ${tempHtmlPath}: `, e)
      }
  }
}


// --- Функции подписки/отписки ---
async function subscribeToContract(dbContract: DatabaseContract): Promise<void> {
  const { address, network } = dbContract;
  const contractKey = `${address}_${network}`;

  if (!ethers.isAddress(address)) {
    console.log(`Invalid address: ${address} on network ${network}`);
    return;
  }
  if (activeProxies.has(contractKey)) {
    console.log(`Already subscribed to ${address} on ${network}.`);
    return;
  }

  try {
    const provider = getEthersProvider(network);
    const proxy = new ethers.Contract(address, proxyAbi, provider);
    
    const initialImplementationAddress = await getImplementation(address, network) || "";
    console.log(`Initial implementation for ${address} on ${network}: ${initialImplementationAddress}`);
    const initialImplementationCode = await getContractSourceCode(initialImplementationAddress, network);
    
    currentImplementations.set(contractKey, { address: initialImplementationAddress, sourceCode: initialImplementationCode, network });
    activeProxies.set(contractKey, proxy);

    proxy.on("Upgraded", async (newImplementationAddress: string) => {
      const oldImplementationDetails = currentImplementations.get(contractKey);
      if (!oldImplementationDetails) {
          console.warn(`Received "Upgraded" event for ${contractKey}, but no prior implementation details found. This should not happen.`);
          // Попытка восстановить информацию, если возможно, или просто обновить
          const newCode = await getContractSourceCode(newImplementationAddress, network);
          currentImplementations.set(contractKey, { address: newImplementationAddress, sourceCode: newCode, network });
          await sendNotificationToBackend(address, network, "unknown", newImplementationAddress, null, newCode);
          return;
      }

      const newImplementationCode = await getContractSourceCode(newImplementationAddress, network);

      console.log(
        `Proxy ${address} on ${network} upgraded! Implementation changed from ${oldImplementationDetails.address} to ${newImplementationAddress}`
      );
      
      await sendNotificationToBackend(
        address, 
        network, 
        oldImplementationDetails.address, 
        newImplementationAddress, 
        oldImplementationDetails.sourceCode, 
        newImplementationCode
      );

      currentImplementations.set(contractKey, { address: newImplementationAddress, sourceCode: newImplementationCode, network });
    });

    console.log(`Successfully subscribed to ${address} on ${network}. Current implementation: ${initialImplementationAddress}`);
  } catch (error) {
    console.error(`Failed to subscribe or get implementation for ${address} on ${network}:`, error);
    if (activeProxies.has(contractKey)) {
        activeProxies.delete(contractKey);
    }
    if (currentImplementations.has(contractKey)){
        currentImplementations.delete(contractKey);
    }
  }
}

function unsubscribeFromContract(address: string, network: SupportedNetwork): void {
  const contractKey = `${address}_${network}`;
  if (!ethers.isAddress(address)) {
    console.log(`Invalid address for unsubscribe: ${address} on ${network}`);
    return;
  }
  if (!activeProxies.has(contractKey)) {
    console.log(`Not currently subscribed to ${address} on ${network}.`);
    return;
  }

  const proxy = activeProxies.get(contractKey);
  if (proxy) {
    proxy.removeAllListeners("Upgraded");
    activeProxies.delete(contractKey);
    currentImplementations.delete(contractKey);
    console.log(`Successfully unsubscribed from ${address} on ${network}.`);
  } else {
    console.warn(`Could not find proxy instance for ${contractKey} during unsubscribe.`);
    activeProxies.delete(contractKey); // Все равно пытаемся очистить
    currentImplementations.delete(contractKey);
  }
}

// --- Функции работы с БД ---
async function getContractsFromDB(): Promise<DatabaseContract[]> {
  try {
    // Убедимся, что network приводится к нашему SupportedNetwork типу
    const res = await pool.query<{ address: string; network: string }>(
      'SELECT DISTINCT address, network FROM contracts'
    );
    const validContracts: DatabaseContract[] = [];
    for (const row of res.rows) {
        const network = row.network.toLowerCase() as SupportedNetwork;
        if (rpcUrls[network] && explorerApiKeys[network]) { // Проверяем, поддерживается ли сеть
            validContracts.push({ address: row.address, network });
        } else {
            console.warn(`Network ${row.network} for contract ${row.address} is not configured or supported. Skipping.`);
        }
    }
    return validContracts;
  } catch (err) {
    console.error('Error fetching contracts from DB:', err);
    return [];
  }
}

// --- Основная логика управления подписками ---
async function manageSubscriptions(): Promise<void> {
  console.log('Checking database for contract updates...');
  const dbContracts = await getContractsFromDB();
  const dbContractKeys = new Set(dbContracts.map(c => `${c.address}_${c.network}`));
  const activeContractKeys = new Set(activeProxies.keys());

  // Новые подписки
  for (const contract of dbContracts) {
    const key = `${contract.address}_${contract.network}`;
    if (!activeContractKeys.has(key)) {
      console.log(`New contract found in DB: ${contract.address} on ${contract.network}. Subscribing...`);
      await subscribeToContract(contract);
      // Добавляем задержку в 1 секунду между подписками
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  }

  // Удаление старых подписок
  for (const activeKey of activeContractKeys) {
    if (!dbContractKeys.has(activeKey)) {
      const [address, network] = activeKey.split('_'); // Предполагаем, что в адресе нет '_'
      console.log(`Contract ${address} on ${network} no longer in DB or not supported. Unsubscribing...`);
      unsubscribeFromContract(address, network as SupportedNetwork);
    }
  }
  console.log(`Subscription management complete. Currently tracking ${activeProxies.size} contracts.`);
}


// --- Запуск скрипта ---
async function main() {
  console.log("Starting contract update monitoring script...");
  
  // Проверка подключения к БД
  try {
    const client = await pool.connect();
    console.log("Successfully connected to PostgreSQL.");
    client.release();
  } catch (err) {
    console.error("Failed to connect to PostgreSQL. Please check your .env configuration.", err);
    process.exit(1);
  }

  // Первоначальный запуск
  await manageSubscriptions();

  // Запуск периодического опроса
  setInterval(manageSubscriptions, dbPollIntervalMinutes * 60 * 1000);

  console.log(`Script initialized. Will check for DB updates every ${dbPollIntervalMinutes} minutes.`);
  console.log(`Monitoring contracts for 'Upgraded' events...`);
}

async function getImplementation(CONTRACT_ADDRESS: string, chain: string): Promise<string | null> {
  const chains = {
    'mainnet': '1',
    'base': '8453',
    'arbitrum': '42161',
  }
  try {
    const API_URL = `https://api.etherscan.io/v2/api?chainid=${chains[chain as keyof typeof chains]}&module=contract&action=getsourcecode&address=${CONTRACT_ADDRESS}&apikey=${ETHERSCAN_API_KEY}`;
    try {
      const response = await fetch(API_URL);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json() as ContractSourceCodeResponse;

      if (data.status === '1' && data.result && data.result.length > 0) {
        console.log(data.result[0].Implementation);
        return data.result[0].Implementation;
      }
    } catch (error) {
      console.error('Failed to fetch or parse contract source code:', error);
      return null;
    }
  } catch (error) {
    console.error('Failed to fetch or parse contract source code:', error);
    return null;
  }
  return null;
}

main().catch(err => {
  console.error("Critical error in script:", err);
  process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log("SIGINT received. Cleaning up and exiting...");
  for (const key of activeProxies.keys()) {
    const [address, network] = key.split('_');
    unsubscribeFromContract(address, network as SupportedNetwork);
  }
  await pool.end();
  console.log("PostgreSQL pool closed. Exiting.");
  process.exit(0);
});