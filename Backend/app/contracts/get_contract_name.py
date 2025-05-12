import httpx
from typing import Optional
import json
from app.core.config import settings


class ContractVerificationError(Exception):
    """Исключение для статуса верификации контракта."""
    pass

class NetworkAccessError(Exception):
    """Исключение для сетевых ошибок при обращении к API."""
    pass

async def _get_etherscan_name(client: httpx.AsyncClient, base_url: str, address: str, api_key: str) -> Optional[str]:
    params = {
        'module': 'contract',
        'action': 'getsourcecode',
        'address': address,
        'apikey': api_key,
    }
    try:
        resp = await client.get(base_url, params=params, timeout=10.0)
        resp.raise_for_status()
        
        try:
            data = resp.json()
        except json.JSONDecodeError:
            return None

        if not isinstance(data, dict):
            return None

        if data.get('status') != '1':
            return None 
                
        result_data = data.get('result')
            
        if isinstance(result_data, list) and result_data and isinstance(result_data[0], dict):
            first_item = result_data[0]
            source_code = first_item.get('SourceCode')

            if source_code:
                contract_name = first_item.get('ContractName')
                if contract_name and isinstance(contract_name, str) and contract_name.strip():
                    return contract_name.strip()
                else:
                    return "noname"
            else:
                raise ContractVerificationError(f"Контракт не верифицирован.")
        else:
            return None

    except (httpx.RequestError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        raise NetworkAccessError(f"Network/Timeout/HTTP Error fetching Etherscan data for {address}: {e}")
    except ContractVerificationError:
        raise
    except Exception as e:
        return None

async def get_contract_name(address: str, network: str) -> Optional[str]:
    address = address.strip()

    base_url = settings.NETWORK_URLS.get(network)
    if not base_url:
        raise ValueError(f"URL для сети '{network}' не найден в конфигурации.")

    async with httpx.AsyncClient() as client:

        etherscan_like_networks = {
            'ethereum', 'mainnet', 'base', 'arbitrum',
        }

        if network in etherscan_like_networks:
            api_key = settings.NETWORK_API_KEYS.get(network)
            if not api_key:
                 raise ValueError(f"API ключ для сети '{network}' не найден или не настроен в конфигурации (settings.NETWORK_API_KEYS).")
            return await _get_etherscan_name(client, base_url, address, api_key)
        else:
            raise ValueError(f"Сеть '{network}' не поддерживается или не сконфигурирована для получения имени контракта.")


__all__ = ['get_contract_name', 'ContractVerificationError', 'NetworkAccessError']
