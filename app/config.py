import os


class Config:
    """Базовая конфигурация приложения"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'очень-секретный-ключ'
    DEBUG = False
    TESTING = False

    # Параметры подключения к базе данных
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'postgres'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or '0911'
    DB_NAME = os.environ.get('DB_NAME') or 'hotel_complex'
    DB_PORT = os.environ.get('DB_PORT') or '5432'

    # Строка подключения к БД
    DATABASE_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True


class TestingConfig(Config):
    """Конфигурация для тестирования"""
    TESTING = True
    DEBUG = True
    DB_NAME = 'hotel_complex_test'
    DATABASE_URI = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"


class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False


# Словарь с конфигурациями
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}