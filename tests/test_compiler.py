# File: book_manager/tests/test_compiler.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for manuscript compilation functionality.
"""

import pytest
import subprocess
from pathlib import Path
from book_manager.compile.compiler import (
    CompilationConfig,
    ManuscriptCompiler,
    CompilationError,
    PandocMissingError
)


@pytest.fixture
def sample_structure(tmp_path):
    """Create a sample book structure for testing."""
    book_dir = tmp_path / "Book1" / "Act1"
    book_dir.mkdir(parents=True)

    scene1 = book_dir / "Scene01.md"
    scene1.write_text("# Scene 1\nTest content.")

    scene2 = book_dir / "Scene02.md"
    scene2.write_text("# Scene 2\nMore content.")

    return {
        1: {
            1: [
                {'path': scene1, 'scene_num': 1},
                {'path': scene2, 'scene_num': 2}
            ]
        }
    }


@pytest.fixture
def compilation_config(tmp_path):
    """Create a CompilationConfig instance."""
    return CompilationConfig(
        formats=['docx'],
        extra_args={'docx': ['--toc']}
    )


def test_compilation_config():
    """Test compilation configuration."""
    config = CompilationConfig(
        formats=['pdf', 'docx'],
        extra_args={'pdf': ['--pdf-engine=xelatex']}
    )

    assert 'pdf' in config.formats
    assert 'docx' in config.formats

    pdf_args = config.get_format_args('pdf')
    assert '--pdf-engine=xelatex' in pdf_args


def test_invalid_format():
    """Test handling of invalid formats."""
    with pytest.raises(ValueError):
        config = CompilationConfig(formats=['invalid'])
        config.validate_formats()


@pytest.fixture
def mock_pandoc_check(monkeypatch):
    """Mock pandoc availability check."""

    def mock_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="pandoc 2.0")

    monkeypatch.setattr(subprocess, "run", mock_run)
    return mock_run


def test_compiler_initialization(mock_pandoc_check, compilation_config):
    """Test compiler initialization."""
    compiler = ManuscriptCompiler(compilation_config)
    assert compiler.config == compilation_config


# Then modify test_missing_pandoc in test_compiler.py
def test_missing_pandoc(monkeypatch):
    """Test behavior when pandoc is missing."""

    def mock_run(*args, **kwargs):
        cmd = args[0]
        if isinstance(cmd, list) and cmd[0] == 'pandoc':
            raise FileNotFoundError("No such file or directory: 'pandoc'")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr('subprocess.run', mock_run)

    with pytest.raises(PandocMissingError):
        ManuscriptCompiler(CompilationConfig())

def test_create_combined_markdown(
        sample_structure, compilation_config, tmp_path
):
    """Test creation of combined markdown file."""
    compiler = ManuscriptCompiler(compilation_config)
    combined = compiler.create_combined_markdown(
        sample_structure,
        tmp_path
    )

    assert combined is not None
    assert combined.exists()
    content = combined.read_text()
    assert "# Scene 1" in content
    assert "# Scene 2" in content


def test_compile_to_format(
        sample_structure, compilation_config, tmp_path, mock_pandoc_check
):
    """Test compilation to a specific format."""
    compiler = ManuscriptCompiler(compilation_config)
    input_file = tmp_path / "input.md"
    input_file.write_text("# Test")
    output_file = tmp_path / "output.docx"

    success = compiler.compile_to_format(
        input_file,
        output_file,
        'docx'
    )
    assert success


def test_compilation_error(
        sample_structure, compilation_config, tmp_path, monkeypatch
):
    """Test handling of compilation errors."""

    def mock_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args, "Error")

    monkeypatch.setattr(subprocess, "run", mock_run)

    compiler = ManuscriptCompiler(compilation_config)
    input_file = tmp_path / "input.md"
    input_file.write_text("# Test")
    output_file = tmp_path / "output.docx"

    with pytest.raises(CompilationError):
        compiler.compile_to_format(
            input_file,
            output_file,
            'docx'
        )