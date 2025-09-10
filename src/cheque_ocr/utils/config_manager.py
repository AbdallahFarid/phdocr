"""Configuration management for cheque OCR system."""

import configparser
from pathlib import Path
from typing import Dict, Any, Optional
import os

from .logging_manager import LoggingManager


class ConfigManager:
    """
    Manages configuration loading and validation for the cheque OCR system.
    
    Supports environment-specific configuration files and environment variable overrides.
    """
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.logger = LoggingManager.get_logger("config_manager")
        
        if config_dir is None:
            # Default to config directory relative to project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self.config = configparser.ConfigParser(interpolation=None)
        self._loaded_files = []
    
    def load_config(self, environment: str = "default") -> Dict[str, Any]:
        """
        Load configuration for specified environment.
        
        Args:
            environment: Environment name (default, development, production)
            
        Returns:
            Dictionary containing configuration values
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        config_file = self.config_dir / f"{environment}.ini"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            self.config.read(config_file)
            self._loaded_files.append(str(config_file))
            
            # Convert to nested dictionary
            config_dict = {}
            for section_name in self.config.sections():
                config_dict[section_name] = dict(self.config[section_name])
            
            # Apply environment variable overrides
            config_dict = self._apply_env_overrides(config_dict)
            
            # Validate and convert types
            config_dict = self._validate_and_convert_config(config_dict)
            
            self.logger.info(f"Loaded configuration from {config_file}")
            return config_dict
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}: {e}")
            raise ValueError(f"Configuration loading failed: {e}")
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables should be named: CHEQUE_OCR_<SECTION>_<KEY>
        Example: CHEQUE_OCR_OCR_SETTINGS_USE_GPU=true
        """
        env_prefix = "CHEQUE_OCR_"
        
        for env_var, value in os.environ.items():
            if not env_var.startswith(env_prefix):
                continue
            
            # Parse environment variable name
            var_parts = env_var[len(env_prefix):].lower().split('_')
            if len(var_parts) < 2:
                continue
            
            # Reconstruct section and key names
            section = var_parts[0]
            if len(var_parts) > 2:
                # Handle multi-word sections like "ocr_settings"
                section = '_'.join(var_parts[:-1])
                key = var_parts[-1]
            else:
                key = var_parts[1]
            
            # Apply override if section exists
            if section in config:
                config[section][key] = value
                self.logger.debug(f"Applied env override: {section}.{key} = {value}")
        
        return config
    
    def _validate_and_convert_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration values and convert to appropriate types.
        
        Args:
            config: Raw configuration dictionary
            
        Returns:
            Validated and type-converted configuration
        """
        # Define expected types for configuration values
        type_conversions = {
            'ocr_settings': {
                'use_gpu': self._to_bool,
                'use_doc_orientation_classify': self._to_bool,
                'use_doc_unwarping': self._to_bool,
                'use_textline_orientation': self._to_bool
            },
            'processing': {
                'min_confidence': float,
                'max_image_size': int,
                'batch_size': int,
                'parallel_processing': self._to_bool
            },
            'output': {
                'include_confidence': self._to_bool,
                'include_headers': self._to_bool
            }
        }
        
        converted_config = {}
        
        for section_name, section_config in config.items():
            converted_section = {}
            
            for key, value in section_config.items():
                try:
                    # Apply type conversion if defined
                    if (section_name in type_conversions and 
                        key in type_conversions[section_name]):
                        converter = type_conversions[section_name][key]
                        converted_value = converter(value)
                    else:
                        converted_value = value
                    
                    converted_section[key] = converted_value
                    
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Failed to convert config value {section_name}.{key}={value}: {e}"
                    )
                    converted_section[key] = value  # Keep original value
            
            converted_config[section_name] = converted_section
        
        return converted_config
    
    @staticmethod
    def _to_bool(value: str) -> bool:
        """Convert string value to boolean."""
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        
        return bool(value)
    
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.
        
        Returns:
            Dictionary with default configuration
        """
        return {
            'ocr_settings': {
                'use_gpu': False,
                'language': 'en',
                'model_version': 'PP-OCRv5',
                'use_doc_orientation_classify': False,
                'use_doc_unwarping': False,
                'use_textline_orientation': False
            },
            'processing': {
                'min_confidence': 0.7,
                'max_image_size': 10485760,
                'batch_size': 10,
                'parallel_processing': False
            },
            'output': {
                'csv_encoding': 'utf-8',
                'include_confidence': True,
                'date_format': '%Y-%m-%d',
                'include_headers': True
            },
            'logging': {
                'level': 'INFO',
                'console_output': True,
                'log_file': 'logs/cheque_ocr.log'
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration completeness and correctness.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid
            
        Raises:
            ValueError: If configuration is invalid
        """
        required_sections = ['ocr_settings', 'processing', 'output', 'logging']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate specific values
        processing = config.get('processing', {})
        
        if processing.get('min_confidence', 0) < 0 or processing.get('min_confidence', 0) > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        
        if processing.get('batch_size', 1) < 1:
            raise ValueError("batch_size must be at least 1")
        
        if processing.get('max_image_size', 0) < 1024:
            raise ValueError("max_image_size must be at least 1024 bytes")
        
        self.logger.info("Configuration validation passed")
        return True
