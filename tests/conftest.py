# File: book_manager/tests/conftest.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test configuration and fixtures for book_manager tests.
"""
import pytest
from unittest.mock import Mock
from pathlib import Path
import shutil
import tempfile


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment with mocked dependencies."""

    def mock_pandoc_check(*args, **kwargs):
        return True

    def mock_config():
        return {
            'outline_file': "3_Plot_and_Outline/outline.md",
            'drafts_dir': "4_Scenes_and_Chapters/Drafts",
            'compiled_dir': "Compiled",
            'pandoc_output_formats': ['pdf', 'docx', 'epub'],
            'stopwords': ['the', 'and'],
            'top_words_count': 5,
            'cache_size': 100,
            'max_file_size': 1048576
        }

    monkeypatch.setattr('book_manager.compile.compiler.ManuscriptCompiler._check_pandoc',
                        mock_pandoc_check)
    monkeypatch.setattr('book_manager.utils.config_loader.get_config',
                        mock_config)


@pytest.fixture
def temp_project():
    """Create a temporary project structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)

        # Create project structure
        drafts = project_dir / "4_Scenes_and_Chapters" / "Drafts"
        book1 = drafts / "Book1"
        act1 = book1 / "Act1"
        act1.mkdir(parents=True)

        # Create test scenes
        scene1 = act1 / "Scene01.md"
        scene1.write_text("# Test Scene\nThis is test content.\nTODO: Fix this\n")

        scene2 = act1 / "Scene02.md"
        scene2.write_text("# Another Scene\nMore test content.\nTODO: Review this\n")

        yield project_dir


@pytest.fixture
def mock_structure(temp_project):
    """Create a mock book structure."""
    return {
        1: {
            1: [
                {
                    'path': temp_project / "4_Scenes_and_Chapters/Drafts/Book1/Act1/Scene01.md",
                    'scene_num': 1,
                    'word_count': 100,
                    'top_words': ['test', 'words'],
                    'todos': ['Fix scene']
                }
            ]
        }
    }

