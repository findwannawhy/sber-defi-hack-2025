import os
from dotenv import load_dotenv
from typing import Dict

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv('BOT_TOKEN')
    DATABASE_URL: str = os.getenv('DATABASE_URL')
    BACKEND_URL: str = os.getenv('BACKEND_URL')
    HTTP_SERVER_HOST: str = os.getenv('BOT_HTTP_HOST', '0.0.0.0')
    HTTP_SERVER_PORT: int = int(os.getenv('BOT_HTTP_PORT', 8080))

    # --- Ключи API из .env ---
    ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
    BASESCAN_API_KEY = os.getenv('BASESCAN_API_KEY')
    ARBISCAN_API_KEY = os.getenv('ARBISCAN_API_KEY')

    # --- URL сетей ---
    NETWORK_URLS: Dict[str, str] = {
        'mainnet': 'https://api.etherscan.io/api',
        'ethereum': 'https://api.etherscan.io/api',
        'base': 'https://api.basescan.org/api',
        'arbitrum': 'https://api.arbiscan.io/api',
    }

    # --- Создаем словарь NETWORK_API_KEYS ---
    NETWORK_API_KEYS: Dict[str, str | None] = {
        'mainnet': ETHERSCAN_API_KEY,
        'ethereum': ETHERSCAN_API_KEY,
        'base': BASESCAN_API_KEY,
        'arbitrum': ARBISCAN_API_KEY,
    }
    NETWORK_API_KEYS = {k: v for k, v in NETWORK_API_KEYS.items() if v}

config = Config()