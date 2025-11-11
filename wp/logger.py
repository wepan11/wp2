"""
日志系统模块
提供统一的日志记录接口，支持文件日志和控制台日志
"""
import os
import logging
import logging.handlers
from typing import Optional
from config import Config


class Logger:
    """日志管理器"""
    
    _loggers = {}
    _initialized = False
    
    @classmethod
    def initialize(cls, config: Config):
        """
        初始化日志系统
        
        Args:
            config: 配置对象
        """
        if cls._initialized:
            return
        
        # 确保日志目录存在
        if config.LOG_FILE_ENABLED:
            log_dir = os.path.dirname(config.LOG_FILE_PATH)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str, config: Optional[Config] = None) -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            config: 配置对象（首次调用时必须提供）
        
        Returns:
            日志记录器
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        if config is None:
            from config import get_config
            config = get_config()
        
        # 初始化日志系统
        if not cls._initialized:
            cls.initialize(config)
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        logger.propagate = False
        
        # 清除已有的处理器
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(config.LOG_FORMAT)
        
        # 添加控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
        logger.addHandler(console_handler)
        
        # 添加文件处理器（如果启用）
        if config.LOG_FILE_ENABLED:
            file_handler = logging.handlers.RotatingFileHandler(
                config.LOG_FILE_PATH,
                maxBytes=config.LOG_MAX_BYTES,
                backupCount=config.LOG_BACKUP_COUNT,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, config.LOG_LEVEL.upper()))
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
    
    Returns:
        日志记录器
    """
    return Logger.get_logger(name)
