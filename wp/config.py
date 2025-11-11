"""
配置管理模块
支持多环境配置（开发、测试、生产）
"""
import os
from typing import Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """基础配置"""
    
    # 应用基础配置
    APP_NAME = os.getenv('APP_NAME', 'BaiduPan Automation Server')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')
    
    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # API安全配置
    API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'default_insecure_key')
    
    # CORS配置
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    # 速率限制配置
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'True').lower() in ('true', '1', 'yes')
    RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
    RATE_LIMIT_STORAGE_URL = os.getenv('RATE_LIMIT_STORAGE_URL', 'memory://')
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_ENABLED = os.getenv('LOG_FILE_ENABLED', 'True').lower() in ('true', '1', 'yes')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', 'logs/app.log')
    LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', 10485760))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', 5))
    LOG_FORMAT = os.getenv(
        'LOG_FORMAT',
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # 数据库配置
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'sqlite')  # sqlite, mysql, postgresql
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/baidu_pan.db')  # SQLite路径
    DATABASE_URL = os.getenv('DATABASE_URL', '')  # MySQL/PostgreSQL连接字符串
    
    # MySQL配置（如果使用MySQL）
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'baidu_pan')
    
    # PostgreSQL配置（如果使用PostgreSQL）
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'baidu_pan')
    
    # 数据目录
    DATA_DIR = os.getenv('DATA_DIR', 'data')
    
    # 节流配置（Throttle）
    THROTTLE_JITTER_MS_MIN = int(os.getenv('THROTTLE_JITTER_MS_MIN', 500))
    THROTTLE_JITTER_MS_MAX = int(os.getenv('THROTTLE_JITTER_MS_MAX', 1500))
    THROTTLE_OPS_PER_WINDOW = int(os.getenv('THROTTLE_OPS_PER_WINDOW', 50))
    THROTTLE_WINDOW_SEC = int(os.getenv('THROTTLE_WINDOW_SEC', 60))
    THROTTLE_WINDOW_REST_SEC = int(os.getenv('THROTTLE_WINDOW_REST_SEC', 20))
    THROTTLE_MAX_CONSECUTIVE_FAILURES = int(os.getenv('THROTTLE_MAX_CONSECUTIVE_FAILURES', 5))
    THROTTLE_PAUSE_SEC_ON_FAILURE = int(os.getenv('THROTTLE_PAUSE_SEC_ON_FAILURE', 60))
    THROTTLE_BACKOFF_FACTOR = float(os.getenv('THROTTLE_BACKOFF_FACTOR', 1.5))
    THROTTLE_COOLDOWN_ON_ERRNO_62_SEC = int(os.getenv('THROTTLE_COOLDOWN_ON_ERRNO_62_SEC', 120))
    
    # 账户配置
    DEFAULT_ACCOUNT = os.getenv('DEFAULT_ACCOUNT', 'main')
    
    # 工作线程配置
    MAX_TRANSFER_WORKERS = int(os.getenv('MAX_TRANSFER_WORKERS', 1))
    MAX_SHARE_WORKERS = int(os.getenv('MAX_SHARE_WORKERS', 1))
    
    # 性能监控配置
    ENABLE_PERFORMANCE_MONITORING = os.getenv('ENABLE_PERFORMANCE_MONITORING', 'False').lower() in ('true', '1', 'yes')
    
    @classmethod
    def get_throttle_config(cls) -> Dict[str, Any]:
        """获取节流配置字典"""
        return {
            'throttle': {
                'jitter_ms_min': cls.THROTTLE_JITTER_MS_MIN,
                'jitter_ms_max': cls.THROTTLE_JITTER_MS_MAX,
                'ops_per_window': cls.THROTTLE_OPS_PER_WINDOW,
                'window_sec': cls.THROTTLE_WINDOW_SEC,
                'window_rest_sec': cls.THROTTLE_WINDOW_REST_SEC,
                'max_consecutive_failures': cls.THROTTLE_MAX_CONSECUTIVE_FAILURES,
                'pause_sec_on_failure': cls.THROTTLE_PAUSE_SEC_ON_FAILURE,
                'backoff_factor': cls.THROTTLE_BACKOFF_FACTOR,
                'cooldown_on_errno_-62_sec': cls.THROTTLE_COOLDOWN_ON_ERRNO_62_SEC
            }
        }
    
    @classmethod
    def get_database_url(cls) -> str:
        """获取数据库连接URL"""
        if cls.DATABASE_URL:
            return cls.DATABASE_URL
        
        if cls.DATABASE_TYPE == 'mysql':
            return f"mysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}"
        elif cls.DATABASE_TYPE == 'postgresql':
            return f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DATABASE}"
        else:  # sqlite
            return f"sqlite:///{cls.DATABASE_PATH}"
    
    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        directories = [
            cls.DATA_DIR,
            os.path.dirname(cls.LOG_FILE_PATH) if cls.LOG_FILE_ENABLED else None,
            os.path.dirname(cls.DATABASE_PATH) if cls.DATABASE_TYPE == 'sqlite' else None,
        ]
        
        for directory in directories:
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    LOG_LEVEL = 'DEBUG'
    DATABASE_PATH = 'data/test_baidu_pan.db'


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env: str = None) -> Config:
    """
    获取配置对象
    
    Args:
        env: 环境名称（development, production, testing）
             如果为None，则从环境变量ENV读取，默认为development
    
    Returns:
        配置对象
    """
    if env is None:
        env = os.getenv('ENV', 'development')
    
    config_class = config_map.get(env, DevelopmentConfig)
    return config_class
