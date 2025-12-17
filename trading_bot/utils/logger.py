"""
Configuración del Logger
=========================
Sistema de logging para el trading bot.
"""

import sys
import os
from loguru import logger
from datetime import datetime


def setup_logger(log_level: str = "INFO", log_to_file: bool = True):
    """
    Configura el sistema de logging.
    
    Args:
        log_level: Nivel de log ('DEBUG', 'INFO', 'WARNING', 'ERROR')
        log_to_file: Si se debe guardar logs en archivo
    """
    # Remover configuración por defecto
    logger.remove()
    
    # Formato para consola
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Añadir handler de consola
    logger.add(
        sys.stdout,
        format=console_format,
        level=log_level,
        colorize=True
    )
    
    # Añadir handler de archivo si se solicita
    if log_to_file:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Archivo de log diario
        log_file = os.path.join(
            log_dir, 
            f"trading_bot_{datetime.now().strftime('%Y%m%d')}.log"
        )
        
        file_format = (
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        )
        
        logger.add(
            log_file,
            format=file_format,
            level="DEBUG",  # Siempre debug en archivo
            rotation="00:00",  # Rotar a medianoche
            retention="30 days",  # Mantener 30 días
            compression="gz"  # Comprimir logs antiguos
        )
        
        # Archivo separado para errores
        error_file = os.path.join(log_dir, "errors.log")
        logger.add(
            error_file,
            format=file_format,
            level="ERROR",
            rotation="10 MB",
            retention="90 days"
        )
    
    logger.info(f"Logger configurado con nivel: {log_level}")
    
    return logger
