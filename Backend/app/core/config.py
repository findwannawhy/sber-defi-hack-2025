from pydantic_settings import BaseSettings
from typing import Dict, List
from pydantic import computed_field

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    JWT_SECRET: str
    DATABASE_URL: str
    TELEGRAM_BOT_USERNAME: str = "SafeDeFi_bot"
    SESSION_SECRET: str
    FRONTEND_BASE_URL: str
    BOT_BASE_URL: str
    ALLOWED_ORIGINS: List[str]
    ENVIRONMENT: str = "development"

    # --- Ключи API для разных сканеров ---
    # Ключ для Etherscan (mainnet)
    ETHERSCAN_API_KEY: str
    # Ключ для Basescan (base)
    BASESCAN_API_KEY: str
    # Ключ для Arbiscan (arbitrum)
    ARBISCAN_API_KEY: str
    # Можно добавить сюда другие ключи по мере необходимости

    # --- Статические URL ---
    NETWORK_URLS: Dict[str, str] = {
        "mainnet": "https://api.etherscan.io/api",
        "ethereum": "https://api.etherscan.io/api",
        "base": "https://api.basescan.org/api",
        "arbitrum": "https://api.arbiscan.io/api",
    }

    # --- Вычисляемое поле для словаря ключей ---
    @computed_field
    @property
    def NETWORK_API_KEYS(self) -> Dict[str, str | None]:
        keys = {
            "mainnet": self.ETHERSCAN_API_KEY,
            "ethereum": self.ETHERSCAN_API_KEY,
            "base": self.BASESCAN_API_KEY,
            "arbitrum": self.ARBISCAN_API_KEY,
        }
        return {
            network: keys.get(network)
            for network in self.NETWORK_URLS
            if network in keys and keys.get(network) is not None
        }

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()