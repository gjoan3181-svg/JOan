"""
Configuración del Trading Bot
==============================
Carga y gestiona todas las configuraciones del sistema.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


@dataclass
class ExchangeConfig:
    """Configuración del exchange."""
    api_key: str = ""
    secret_key: str = ""
    use_testnet: bool = True
    testnet_api_key: str = ""
    testnet_secret_key: str = ""


@dataclass
class TradingConfig:
    """Configuración de trading."""
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    max_position_size: float = 0.01  # En unidades de la criptomoneda
    max_risk_per_trade: float = 0.02  # 2% del capital por operación
    stop_loss_percent: float = 0.02  # 2% stop loss
    take_profit_percent: float = 0.04  # 4% take profit


@dataclass
class ModelConfig:
    """Configuración del modelo de IA."""
    model_type: str = "random_forest"  # random_forest, xgboost, lstm
    prediction_threshold: float = 0.6
    lookback_period: int = 100  # Velas para análisis
    retrain_interval: int = 24  # Horas entre re-entrenamientos


@dataclass
class Settings:
    """Configuración principal del sistema."""
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    trading: TradingConfig = field(default_factory=TradingConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    database_url: str = "sqlite:///trading_bot.db"
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Carga la configuración desde variables de entorno."""
        return cls(
            exchange=ExchangeConfig(
                api_key=os.getenv("BINANCE_API_KEY", ""),
                secret_key=os.getenv("BINANCE_SECRET_KEY", ""),
                use_testnet=os.getenv("USE_TESTNET", "true").lower() == "true",
                testnet_api_key=os.getenv("BINANCE_TESTNET_API_KEY", ""),
                testnet_secret_key=os.getenv("BINANCE_TESTNET_SECRET_KEY", ""),
            ),
            trading=TradingConfig(
                symbol=os.getenv("TRADING_SYMBOL", "BTCUSDT"),
                timeframe=os.getenv("TRADING_TIMEFRAME", "1h"),
                max_position_size=float(os.getenv("MAX_POSITION_SIZE", "0.01")),
                max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "0.02")),
            ),
            model=ModelConfig(
                model_type=os.getenv("MODEL_TYPE", "random_forest"),
                prediction_threshold=float(os.getenv("PREDICTION_THRESHOLD", "0.6")),
            ),
            database_url=os.getenv("DATABASE_URL", "sqlite:///trading_bot.db"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Singleton para la configuración global
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Obtiene la configuración global (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
    return _settings
