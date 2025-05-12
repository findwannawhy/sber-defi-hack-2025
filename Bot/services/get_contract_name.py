import aiohttp
import asyncio
from typing import Optional
from utils.config import config


class ContractVerificationError(Exception):
    """Исключение для статуса верификации контракта."""
    pass

class NetworkAccessError(Exception):
    """Исключение для сетевых ошибок при обращении к API."""
    pass

async def _get_etherscan_name(session: aiohttp.ClientSession, base_url: str, address: str, api_key: str) -> Optional[str]:
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': address,
        'apikey': api_key,
    }
    try:
        async with session.get(base_url, params=params, timeout=10) as resp:
            resp.raise_for_status()
            try:
                data = await resp.json()
            except aiohttp.ContentTypeError:
                return None # Не удалось получить JSON

            if not isinstance(data, dict):
                return None # Ответ не словарь

            # Статус 0 -> ошибка,контракт не найден, адрес неверный и т.д.
            if data.get('status') != '1':
                return None 
                
            result_data = data.get('result')
            
            # Проверяем структуру ответа: должен быть список с одним словарем
            if isinstance(result_data, list) and result_data and isinstance(result_data[0], dict):
                first_item = result_data[0]
                source_code = first_item.get('SourceCode')

                # Проверяем наличие исходного кода (признак верификации)
                if source_code:
                    contract_name = first_item.get('ContractName')
                    if contract_name and isinstance(contract_name, str) and contract_name.strip():
                        return contract_name.strip()
                    else:
                        return "noname"
                else:
                    raise ContractVerificationError(f"Контракт <code>{address}</code> не верифицирован.")
            else:
                return None # Считаем, что не удалось определить

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        raise NetworkAccessError(f"Network/Timeout Error fetching Etherscan data for {address}: {e}")
    except ContractVerificationError:
        raise
    except Exception as e:
        return None

    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        raise NetworkAccessError(f"Network/Timeout Error fetching Tronscan data for {address}: {e}")
    except ContractVerificationError:
        raise
    except Exception as e:
        return None

async def get_contract_name(address: str, network: str) -> Optional[str]:
    address = address.strip()
    base_url = config.NETWORK_URLS.get(network)

    async with aiohttp.ClientSession() as session:

        etherscan_like_networks = {
            'ethereum', 'mainnet', 'base', 'arbitrum'
        }

        if network in etherscan_like_networks:
            api_key = config.NETWORK_API_KEYS.get(network)
            if not api_key:
                 raise ValueError(f"API ключ для сети '{network}' не найден или не настроен в конфигурации бота (config.NETWORK_API_KEYS).")
            return await _get_etherscan_name(session, base_url, address, api_key)
        else:
            raise ValueError(f"Сеть '{network}' не поддерживается или не сконфигурирована для получения имени контракта в боте.")

__all__ = ['get_contract_name', 'ContractVerificationError', 'NetworkAccessError']