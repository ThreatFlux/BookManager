# File: book_manager/utils/config_loader.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configuration loader with validation and caching.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)

CONFIG_SCHEMA = {
    'required': {
        'stopwords': list,
        'top_words_count': int,
        'pandoc_output_formats': list,
        'outline_file': str,
        'drafts_dir': str,
        'compiled_dir': str
    },
    'optional': {
        'cache_size': int,
        'max_file_size': int,
        'encoding': str
    }
}

_DEFAULT_CONFIG: Dict[str, Any] = {
    'stopwords': ["the", "and", "to", "of", "a", "in", "that", "is", "for",
                  "with", "on", "as", "it", "at", "by"],
    'top_words_count': 5,
    'pandoc_output_formats': ['pdf', 'docx', 'epub'],
    'outline_file': "3_Plot_and_Outline/outline.md",
    'drafts_dir': "4_Scenes_and_Chapters/Drafts",
    'compiled_dir': "Compiled",
    'cache_size': 1000,  # Maximum number of cached analyses
    'max_file_size': 10 * 1024 * 1024,  # 10MB max file size
    'encoding': 'utf-8'
}

_CONFIG_CACHE: Optional[Dict[str, Any]] = None


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration against schema.

    Args:
        config: Configuration dictionary to validate

    Returns:
        bool: True if valid, False otherwise

    Raises:
        ValueError: If configuration is invalid
    """
    # Check required fields
    for key, expected_type in CONFIG_SCHEMA['required'].items():
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
        if not isinstance(config[key], expected_type):
            raise ValueError(
                f"Invalid type for {key}. Expected {expected_type}, got {type(config[key])}"
            )

    # Validate specific values
    if config['top_words_count'] < 1:
        raise ValueError("top_words_count must be positive")

    if not config['pandoc_output_formats']:
        raise ValueError("pandoc_output_formats cannot be empty")

    if 'cache_size' in config and config['cache_size'] < 0:
        raise ValueError("cache_size must be non-negative")

    return True


def load_config(config_path: str = "config.yaml") -> None:
    """
    Load configuration from YAML file or use defaults.

    Args:
        config_path: Path to configuration file

    Raises:
        ValueError: If configuration is invalid
    """
    global _CONFIG_CACHE

    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data is None:
                    data = {}
        else:
            logger.warning(f"Config file not found: {config_path}")
            data = {}

        # Merge with defaults
        config = _DEFAULT_CONFIG.copy()
        config.update(data)

        # Validate merged config
        if validate_config(config):
            _CONFIG_CACHE = config
            logger.info("Configuration loaded successfully")

    except (yaml.YAMLError, IOError) as e:
        logger.error(f"Error loading config: {e}")
        raise


def get_config() -> Dict[str, Any]:
    """
    Get the current configuration.

    Returns:
        dict: Current configuration
    """
    if _CONFIG_CACHE is None:
        load_config()
    return _CONFIG_CACHE


def reload_config(config_path: str = "config.yaml") -> None:
    """
    Force reload of configuration.

    Args:
        config_path: Path to configuration file
    """
    global _CONFIG_CACHE
    _CONFIG_CACHE = None
    load_config(config_path)