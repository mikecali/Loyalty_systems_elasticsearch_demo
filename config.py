"""
Configuration module for Jollibee BeeLoyalty System
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class"""
    
    # Elasticsearch Configuration
    ELASTICSEARCH_ENDPOINT = os.getenv('ELASTICSEARCH_ENDPOINT', 'https://localhost:9200')
    ELASTICSEARCH_API_KEY = os.getenv('ELASTICSEARCH_API_KEY')
    
    # Flask Configuration
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Application Configuration
    APP_NAME = os.getenv('APP_NAME', 'Jollibee BeeLoyalty System')
    APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
    
    # Menu Data Source Configuration
    JOLLIBEE_MENU_URL = os.getenv('JOLLIBEE_MENU_URL', 'https://jollibeemenuprice.ph')
    USE_LIVE_MENU_DATA = os.getenv('USE_LIVE_MENU_DATA', 'True').lower() == 'true'
    MENU_CACHE_DURATION = int(os.getenv('MENU_CACHE_DURATION', 3600))  # 1 hour default
    
    # Elasticsearch Indices
    INDEX_MENU = os.getenv('INDEX_MENU', 'jollibee-menu')
    INDEX_CUSTOMERS = os.getenv('INDEX_CUSTOMERS', 'jollibee-customers')
    INDEX_TRANSACTIONS = os.getenv('INDEX_TRANSACTIONS', 'jollibee-transactions')
    INDEX_INVENTORY = os.getenv('INDEX_INVENTORY', 'jollibee-inventory')
    INDEX_STORES = os.getenv('INDEX_STORES', 'jollibee-stores')
    INDEX_WEATHER = os.getenv('INDEX_WEATHER', 'jollibee-weather')
    
    # ELSER Model Configuration
    ELSER_MODEL_ID = os.getenv('ELSER_MODEL_ID', '.elser_model_2_linux-x86_64')
    ELSER_PIPELINE_NAME = os.getenv('ELSER_PIPELINE_NAME', 'jollibee-elser-pipeline')
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = [
            ('ELASTICSEARCH_ENDPOINT', cls.ELASTICSEARCH_ENDPOINT),
            ('ELASTICSEARCH_API_KEY', cls.ELASTICSEARCH_API_KEY)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True
