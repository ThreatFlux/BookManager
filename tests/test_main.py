# File: book_manager/tests/test_main.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for main module functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from book_manager.main import (
    CommandLineParser,
    BookManager,
    BookManagerError,
    main
)


@pytest.fixture
def mock_structure(tmp_path):
    """Create a mock book structure."""
    return {
        1: {
            1: [
                {
                    'path': tmp_path / "Book1/Act1/Scene01.md",
                    'scene_num': 1,
                    'word_count': 100,
                    'top_words': ['test', 'words'],
                    'todos': ['Fix scene']
                }
            ]
        }
    }


@pytest.fixture
def cli_parser():
    """Create a CommandLineParser instance."""
    return CommandLineParser()


def test_command_line_parser_basic(cli_parser):
    """Test basic command line argument parsing."""
    args = cli_parser.parser.parse_args([])
    assert not args.no_compile
    assert not args.report_only
    assert args.config == 'config.yaml'


def test_command_line_parser_formats(cli_parser):
    """Test output format parsing."""
    args = cli_parser.parser.parse_args(['--output-format', 'pdf,docx'])
    assert args.output_format == ['pdf', 'docx']



@pytest.fixture
def book_manager(tmp_path):
    """Create a BookManager instance with mock arguments."""
    args = Mock()
    args.config = str(tmp_path / "config.yaml")
    args.no_compile = False
    args.report_only = False
    args.output_format = None
    args.force = False
    args.verbose = False
    args.quiet = False
    return BookManager(args)


def test_book_manager_setup(book_manager, tmp_path):
    """Test BookManager setup."""
    # Create mock config
    config_path = Path(book_manager.args.config)
    config_path.write_text("""
        stopwords: [the, and]
        top_words_count: 5
        pandoc_output_formats: [pdf]
        outline_file: outline.md
        drafts_dir: drafts
        compiled_dir: compiled
    """)

    book_manager.setup()
    assert book_manager.config is not None


def test_book_manager_scan(book_manager, mock_structure):
    """Test project structure scanning."""
    with patch('book_manager.main.scan_project') as mock_scan:
        mock_scan.return_value = mock_structure
        book_manager.scan_project()
        assert book_manager.structure == mock_structure


def test_book_manager_analyze(book_manager, mock_structure):
    """Test scene analysis."""
    book_manager.structure = mock_structure

    with patch('book_manager.main.analyze_scene') as mock_analyze:
        mock_analyze.return_value = {
            'word_count': 100,
            'top_words': ['test'],
            'todos': []
        }
        book_manager.analyze_scenes()


def test_outline_generation(book_manager, mock_structure):
    """Test outline content generation."""
    book_manager.structure = mock_structure
    outline = book_manager.generate_outline()

    assert "Book 1" in outline
    assert "Act 1" in outline
    assert "Words: 100" in outline
    assert "Fix scene" in outline


def test_outline_saving(book_manager, tmp_path):
    """Test outline file saving."""
    book_manager.config = {'outline_file': str(tmp_path / "outline.md")}
    content = "# Test Outline"
    book_manager.save_outline(content)

    assert Path(book_manager.config['outline_file']).exists()
    assert Path(book_manager.config['outline_file']).read_text() == content


@patch('book_manager.main.batch_compile')
def test_manuscript_compilation(mock_compile, book_manager, mock_structure):
    """Test manuscript compilation process."""
    book_manager.structure = mock_structure
    mock_compile.return_value = (True, ["output.pdf"])

    book_manager.compile_manuscript()
    assert mock_compile.called


def test_complete_workflow(book_manager, mock_structure, tmp_path):
    """Test complete workflow execution."""
    # Setup mocks
    with patch.multiple(
            'book_manager.main',
            scan_project=Mock(return_value=mock_structure),
            analyze_scene=Mock(return_value={'word_count': 100}),
            batch_compile=Mock(return_value=(True, ["output.pdf"]))
    ):
        # Create config file
        config_path = Path(book_manager.args.config)
        config_path.write_text("""
            stopwords: [the, and]
            top_words_count: 5
            pandoc_output_formats: [pdf]
            outline_file: outline.md
            drafts_dir: drafts
            compiled_dir: compiled
        """)

        # Run workflow
        book_manager.run()


def test_error_handling(book_manager):
    """Test error handling in main workflow."""
    with patch('book_manager.main.scan_project') as mock_scan:
        mock_scan.return_value = None
        with pytest.raises(BookManagerError):
            book_manager.run()


@patch('book_manager.main.CommandLineParser')
@patch('book_manager.main.BookManager')
def test_main_function(mock_manager_class, mock_parser_class):
    """Test main entry point function."""
    # Setup mocks
    mock_parser = Mock()
    mock_parser.parse.return_value = Mock()
    mock_parser_class.return_value = mock_parser

    mock_manager = Mock()
    mock_manager_class.return_value = mock_manager

    # Test successful execution
    assert main() == 0

    # Test error handling
    mock_manager.run.side_effect = BookManagerError("Test error")
    assert main() == 1