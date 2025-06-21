"""
Configuration module for BeanFlow
"""

from .config_manager import ConfigManager

# Create a global config instance
CONFIG = ConfigManager()

__all__ = ['ConfigManager', 'CONFIG'] 