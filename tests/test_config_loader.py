# File: book_manager/tests/test_config_loader.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for configuration loading functionality.
"""

import pytest
import yaml
from pathlib import Path
from book_manager.utils.config_loader import load_config, get_config, reload_config, validate_config


@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config file."""
    config_path = tmp_path / "config.yaml"
    config = {
        "stopwords": ["the", "and"],
        "top_words_count": 5,
        "pandoc_output_formats": ["pdf"],
        "outline_file": "outline.md",
        "drafts_dir": "drafts",
        "compiled_dir": "compiled",
    }
    config_path.write_text(yaml.dump(config))
    return config_path


def test_load_config_with_file(temp_config):
    """Test loading configuration from file."""
    load_config(str(temp_config))
    config = get_config()
    assert config["top_words_count"] == 5
    assert "the" in config["stopwords"]


def test_load_config_without_file():
    """Test loading configuration with missing file."""
    load_config("nonexistent.yaml")
    config = get_config()
    assert isinstance(config["top_words_count"], int)
    assert isinstance(config["stopwords"], list)


def test_validate_config():
    """Test configuration validation."""
    valid_config = {
        "stopwords": ["the"],
        "top_words_count": 5,
        "pandoc_output_formats": ["pdf"],
        "outline_file": "outline.md",
        "drafts_dir": "drafts",
        "compiled_dir": "compiled",
    }
    assert validate_config(valid_config) is True

    invalid_config = valid_config.copy()
    invalid_config["top_words_count"] = -1
    with pytest.raises(ValueError):
        validate_config(invalid_config)


def test_reload_config(temp_config):
    """Test configuration reloading."""
    load_config(str(temp_config))
    initial_config = get_config()

    # Modify config file
    new_config = {
        "stopwords": ["a", "the"],
        "top_words_count": 10,
        "pandoc_output_formats": ["pdf"],
        "outline_file": "outline.md",
        "drafts_dir": "drafts",
        "compiled_dir": "compiled",
    }
    temp_config.write_text(yaml.dump(new_config))

    reload_config(str(temp_config))
    updated_config = get_config()

    assert updated_config["top_words_count"] == 10
    assert updated_config["top_words_count"] != initial_config["top_words_count"]
