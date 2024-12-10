"""
Test configuration and fixtures for book_manager tests.

Provides common test fixtures and mocks for the book_manager test suite.
"""

import pytest
from unittest.mock import Mock
from pathlib import Path
import tempfile
import shutil


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment with mocked dependencies."""

    def mock_config():
        return {
            "outline_file": "3_Plot_and_Outline/outline.md",
            "drafts_dir": "4_Scenes_and_Chapters/Drafts",
            "compiled_dir": "Compiled",
            "document_style": {
                "body_font": "'Arial', sans-serif",
                "heading_font": "'Arial', sans-serif",
                "code_font": "'Courier New', monospace",
                "font_size": "12pt",
                "paper_format": "letter",
                "margin_top": "1in",
                "margin_right": "1in",
                "margin_bottom": "1in",
                "margin_left": "1in",
                "heading_color": "#000000",
                "text_color": "#000000",
                "link_color": "#0366d6",
                "code_background": "#f6f8fa",
            },
            "stopwords": ["the", "and"],
            "top_words_count": 5,
            "cache_size": 100,
            "max_file_size": 1048576,
        }

    # Mock config loader
    monkeypatch.setattr("book_manager.utils.config_loader.get_config", mock_config)

    # Mock WeasyPrint components
    mock_html = Mock()
    mock_html.write_pdf = Mock(return_value=None)
    monkeypatch.setattr("weasyprint.HTML", Mock(return_value=mock_html))

    # Mock python-docx
    mock_document = Mock()
    mock_document.add_paragraph = Mock(return_value=Mock())
    monkeypatch.setattr("docx.Document", Mock(return_value=mock_document))


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
                    "path": temp_project / "4_Scenes_and_Chapters/Drafts/Book1/Act1/Scene01.md",
                    "scene_num": 1,
                    "word_count": 100,
                    "top_words": ["test", "words"],
                    "todos": ["Fix scene"],
                }
            ]
        }
    }


@pytest.fixture
def default_style_config():
    """Provide default document style configuration."""
    return {
        "body_font": "'Arial', sans-serif",
        "heading_font": "'Arial', sans-serif",
        "code_font": "'Courier New', monospace",
        "font_size": "12pt",
        "paper_format": "letter",
        "margin_top": "1in",
        "margin_right": "1in",
        "margin_bottom": "1in",
        "margin_left": "1in",
        "heading_color": "#000000",
        "text_color": "#000000",
        "link_color": "#0366d6",
        "code_background": "#f6f8fa",
    }


@pytest.fixture
def mock_compiler(monkeypatch):
    """Provide a mocked DocumentCompiler instance."""

    class MockCompiler:
        def convert_to_docx(self, *args, **kwargs):
            """Mock convert_to_docx method."""
            return None

        def convert_to_pdf(self, *args, **kwargs):
            """Mock convert_to_pdf method."""
            return None

        def compile_manuscript(self, *args, **kwargs):
            """Mock compile_manuscript method."""
            return [], []

    return MockCompiler()
