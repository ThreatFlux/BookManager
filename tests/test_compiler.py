"""
Tests for manuscript compilation functionality.
"""

import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from docx import Document
from book_manager.compile.compiler import DocumentCompiler, DocumentStyle, PaperFormat, CompilationError

from book_manager.compile.compiler import compile_manuscript, DocumentCompiler


@pytest.fixture
def sample_structure(tmp_path):
    """Create a sample book structure for testing."""
    book_dir = tmp_path / "Book1" / "Act1"
    book_dir.mkdir(parents=True)

    scene1 = book_dir / "Scene01.md"
    scene1.write_text("# Scene 1\nTest content.")

    scene2 = book_dir / "Scene02.md"
    scene2.write_text("# Scene 2\nMore content.")

    return {1: {1: [{"path": scene1, "scene_num": 1}, {"path": scene2, "scene_num": 2}]}}


@pytest.fixture
def default_config():
    """Create a default configuration for testing."""
    return {
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
        "compiled_dir": "Compiled",
    }


@pytest.fixture
def compiler(default_config):
    """Create a DocumentCompiler instance."""
    return DocumentCompiler(default_config)


def test_paper_format():
    """Test paper format creation and validation."""
    format_a4 = PaperFormat.from_name("a4")
    assert format_a4.width == "210mm"
    assert format_a4.height == "297mm"

    format_letter = PaperFormat.from_name("letter")
    assert format_letter.width == "8.5in"
    assert format_letter.height == "11in"

    # Test invalid format defaults to letter
    format_invalid = PaperFormat.from_name("invalid")
    assert format_invalid.width == "8.5in"
    assert format_invalid.height == "11in"


def test_document_style_from_config(default_config):
    """Test document style creation from config."""
    style = DocumentStyle.from_config(default_config)
    assert style.fonts.body_font == "'Arial', sans-serif"
    assert style.fonts.font_size == "12pt"
    assert isinstance(style.paper_format, PaperFormat)


def test_convert_to_docx(compiler, tmp_path):
    """Test conversion to DOCX format."""
    content = "# Test Heading\nTest content with **bold** and *italic*."
    output_file = tmp_path / "test.docx"

    compiler.convert_to_docx(content, output_file)

    assert output_file.exists()

    # Verify DOCX content
    string_output_path = str(output_file)
    doc = Document(string_output_path)
    paragraphs = [p.text for p in doc.paragraphs]
    assert "Test Heading" in paragraphs


def test_convert_to_pdf(compiler, tmp_path):
    """Test conversion to PDF format."""
    content = "# Test Heading\nTest content."
    output_file = tmp_path / "test.pdf"

    compiler.convert_to_pdf(content, output_file)

    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_invalid_format(compiler, tmp_path):
    """Test handling of invalid formats."""
    content = "# Test"
    formats = ["invalid"]
    output_dir = tmp_path / "output"

    files = compiler.compile_manuscript(content, formats, output_dir)
    assert len(files) == 0


def test_compilation_error_handling(compiler, tmp_path):
    """Test handling of compilation errors."""
    content = "# Test"
    output_file = tmp_path / "nonexistent" / "test.pdf"

    with pytest.raises(CompilationError):
        compiler.convert_to_pdf(content, output_file)


def test_style_application(compiler, tmp_path):
    """Test that styles are correctly applied."""
    content = "# Heading\nParagraph"
    temp_html = tmp_path / "test.html"

    # Get the styled HTML
    styled_html = compiler._create_styled_html(content)
    temp_html.write_text(styled_html)

    # Parse the HTML to verify styles
    soup = BeautifulSoup(styled_html, "html.parser")
    assert soup.find("body") is not None


def test_batch_compilation(sample_structure, default_config, tmp_path):
    """Test batch compilation with different formats."""
    from book_manager.compile.compiler import batch_compile

    output_dir = tmp_path / "output"
    default_config["compiled_dir"] = str(output_dir)

    success, files = batch_compile(sample_structure, formats=["docx", "pdf"], config=default_config)

    assert success
    assert len(files) == 2
    assert any(f.endswith(".docx") for f in files)
    assert any(f.endswith(".pdf") for f in files)


def test_empty_structure(compiler, default_config, tmp_path):
    """Test compilation with empty structure."""
    empty_structure = {}
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)

    success, files = compile_manuscript(empty_structure, ["pdf"], output_dir, config=default_config)

    assert not success  # Should fail for empty structure
    assert len(files) == 0  # Should produce no files
