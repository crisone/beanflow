"""
Configuration manager for BeanFlow
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration for BeanFlow application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to config file. If None, will search for .beanflow/config.yaml
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
    
    def _find_config_file(self) -> str:
        """
        Find the configuration file in the current directory or parent directories.
        
        Returns:
            Path to the configuration file
            
        Raises:
            FileNotFoundError: If no config file is found
        """
        # Start from current working directory
        current_dir = Path.cwd()
        
        # Search in current directory and parent directories
        for directory in [current_dir] + list(current_dir.parents):
            config_file = directory / '.beanflow' / 'config.yaml'
            if config_file.exists():
                return str(config_file)
        
        # If not found, create default config in current directory
        default_config_dir = current_dir / '.beanflow'
        default_config_dir.mkdir(exist_ok=True)
        default_config_file = default_config_dir / 'config.yaml'
        
        # Create default configuration
        self._create_default_config(default_config_file)
        
        return str(default_config_file)
    
    def _create_default_config(self, config_file: Path) -> None:
        """
        Create a default configuration file.
        
        Args:
            config_file: Path to the config file to create
        """
        default_config = {
            'common': {
                'beancount_main': 'beancount/main.bean'
            },
            'price': {
                'data_dir': 'commodity_price',
                'currency_api_key': 'your-api-key'
            },
            'llm_provider': {
                'base_url': 'https://api.deepseek.com/v1',
                'api_key': 'your-api-key',
                'model': 'deepseek-chat'
            },
            'importer': {
                'alipay': {
                    'account_root': 'Assets:EWallet:Alipay',
                    'liability_root': 'Liabilities:Internet:Huabei',
                    'temp_account': 'Assets:Receivables:Alibaba'
                },
                'wechat': {
                    'account_root': 'Assets:EWallet:Wechat'
                },
                'jd': {
                    'account_root': 'Assets:EWallet:JD',
                    'liability_root': 'Liabilities:Internet:JD',
                    'ignored_pay_methods': [
                        '微信支付'
                    ]
                },
                'meituan': {
                    'account_root': 'Assets:EWallet:Meituan',
                    'ignored_pay_methods': [
                        '微信支付'
                    ]
                }
            },
            'classifier': {
                'classify_prompts': [
                    '金额较小的餐饮类订单，一般记在 Expenses:Food:DailyMeal 账户下'
                ]
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from the config file.
        
        Returns:
            Configuration dictionary
            
        Raises:
            yaml.YAMLError: If config file is invalid YAML
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                return config or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in config file {self.config_path}: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'beancount.ledger_file')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'beancount.ledger_file')
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def save(self) -> None:
        """
        Save the current configuration to the config file.
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
    
    def reload(self) -> None:
        """
        Reload configuration from the config file.
        """
        self.config = self._load_config()
    
    @property
    def config_dir(self) -> str:
        """
        Get the directory containing the configuration file.
        
        Returns:
            Configuration directory path
        """
        return str(Path(self.config_path).parent)
    
    def __str__(self) -> str:
        return f"ConfigManager(config_path='{self.config_path}')"
    
    def __repr__(self) -> str:
        return self.__str__() 