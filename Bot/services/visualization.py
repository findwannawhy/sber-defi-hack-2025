import aiohttp
import asyncio
import logging
from utils.config import config
async def get_contract_graph_url(address: str, network: str) -> str:
    """Получает URL графа контракта, отправляя запрос на внешний API."""
    visualize_url = f"{config.BACKEND_URL}/visualise/run"
    payload = {
        "network": network,
        "address": address,
        "source": "bot"
    }
    headers = {'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(visualize_url, json=payload, headers=headers) as response:
                response.raise_for_status()
                data = await response.json()
                graph_url = data.get("url")
                if not graph_url:
                    logging.error(f"Graph URL not found in response for {address} on {network}. Response: {data}")
                    raise ValueError("Сервер визуализации не вернул URL графа.")
                logging.info(f"Successfully retrieved visualization URL for {address} on {network}: {graph_url}")
                return graph_url
        except aiohttp.ClientResponseError as e:
            logging.error(f"HTTP error during visualization request for {address} on {network}: {e.status} {e.message}")
            raise ConnectionError(f"Ошибка от сервера визуализации: {e.status}") from e
        except aiohttp.ClientConnectionError as e:
            logging.error(f"Connection error during visualization request for {address} on {network}: {e}")
            raise ConnectionError("Не удалось подключиться к серверу визуализации.") from e
        except asyncio.TimeoutError:
            logging.error(f"Timeout during visualization request for {address} on {network}")
            raise TimeoutError("Превышено время ожидания от сервера визуализации.")
        except ValueError as e:
             logging.error(f"Data error during visualization for {address} on {network}: {e}")
             raise ValueError(f"Ошибка данных от сервера визуализации: {e}") from e
        except Exception as e:
            logging.error(f"Unexpected error during visualization for {address} on {network}: {e}")
            raise RuntimeError("Произошла непредвиденная ошибка при визуализации.") from e
