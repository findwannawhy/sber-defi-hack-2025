import aiohttp
import asyncio
import logging
from utils.config import config

async def audit_contract(address: str, network: str) -> bytes:
    audit_url = f"{config.BACKEND_URL}/audit/run"
    payload = {
        "network": network,
        "address": address
    }
    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(audit_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                pdf_bytes = await response.read()
                logging.info(f"Successfully retrieved audit PDF for {address} on {network}")
                return pdf_bytes
        except aiohttp.ClientResponseError as e:
            logging.error(f"HTTP error during audit request for {address} on {network}: {e.status} {e.message}")
            raise ConnectionError(f"Ошибка от сервера аудита: {e.status}") from e
        except aiohttp.ClientConnectionError as e:
            logging.error(f"Connection error during audit request for {address} on {network}: {e}")
            raise ConnectionError("Не удалось подключиться к серверу аудита.") from e
        except asyncio.TimeoutError:
            logging.error(f"Timeout during audit request for {address} on {network}")
            raise TimeoutError("Превышено время ожидания от сервера аудита.")
        except Exception as e:
            logging.error(f"Unexpected error during audit for {address} on {network}: {e}")
            raise RuntimeError("Произошла непредвиденная ошибка при аудите.") from e