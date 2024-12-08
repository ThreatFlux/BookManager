# File: book_manager/tests/test_dir_scanner.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for the directory scanner module.
"""

import pytest
from pathlib import Path
from book_manager.structure.dir_scanner import (
    extract_book_act_from_path,
    get_scene_number,
    scan_project
)


def test_extract_book_act_from_path():
    """Test book and act number extraction from paths."""
    assert extract_book_act_from_path(("Book1", "Act2")) == (1, 2)
    assert extract_book_act_from_path(("book1", "act2")) == (1, 2)
    assert extract_book_act_from_path(("Chapter1", "Scene1")) == (None, None)
    assert extract_book_act_from_path(("Book1", "Scene1")) == (1, None)


def test_get_scene_number():
    """Test scene number extraction from filenames."""
    assert get_scene_number(Path("Scene01.md")) == 1
    assert get_scene_number(Path("scene_02.md")) == 2
    assert get_scene_number(Path("random.md")) == 9999


def test_scan_project(temp_project, monkeypatch):
    """Test project structure scanning."""
    from book_manager.utils import config_loader

    # Create test structure first
    test_dir = temp_project / "4_Scenes_and_Chapters/Drafts/Book1/Act1"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "Scene01.md").write_text("Test content")

    def mock_get_config():
        return {
            'drafts_dir': str(test_dir.parent.parent.parent)
        }

    monkeypatch.setattr(config_loader, "get_config", mock_get_config)

    structure = scan_project()
    assert 1 in structure  # Book1 exists
    assert 1 in structure[1]  # Act1 exists