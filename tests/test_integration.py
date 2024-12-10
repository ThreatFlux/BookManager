# File: book_manager/tests/test_integration.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Integration tests for book manager functionality.
"""

import pytest
import shutil
from pathlib import Path
from book_manager.main import BookManager, BookManagerError
from unittest.mock import Mock


@pytest.fixture
def project_structure(tmp_path):
    """Create a complete project structure for testing."""
    # Create directories
    drafts = tmp_path / "4_Scenes_and_Chapters" / "Drafts"
    book1 = drafts / "Book1"
    act1 = book1 / "Act1"
    act1.mkdir(parents=True)

    # Create scene files
    scene1 = act1 / "Scene01.md"
    scene1.write_text(
        """
    # Opening Scene

    This is the first scene with some content.
    The quick brown fox jumps over the lazy dog.

    TODO: Improve description
    TODO: Add character development
    """
    )

    scene2 = act1 / "Scene02.md"
    scene2.write_text(
        """
    # Second Scene

    Another scene with different content.
    More text for analysis purposes.

    TODO: Add conflict
    """
    )

    # Create config
    config = tmp_path / "config.yaml"
    config.write_text(
        f"""
        stopwords: [the, and, with]
        top_words_count: 5
        pandoc_output_formats: [docx]
        outline_file: {tmp_path}/3_Plot_and_Outline/outline.md
        drafts_dir: {drafts}
        compiled_dir: {tmp_path}/Compiled
        cache_size: 100
        max_file_size: 1048576
        encoding: utf-8
    """
    )

    return tmp_path


def test_complete_workflow(project_structure):
    """Test complete workflow from scanning to compilation."""
    # Setup arguments
    args = Mock()
    args.config = str(project_structure / "config.yaml")
    args.no_compile = True  # Skip actual compilation
    args.report_only = False
    args.output_format = None
    args.force = True
    args.verbose = True
    args.quiet = False

    # Create and run manager
    manager = BookManager(args)
    manager.run()

    # Verify outline was created
    outline_path = project_structure / "3_Plot_and_Outline" / "outline.md"
    assert outline_path.exists()

    outline_content = outline_path.read_text()
    assert "Book 1" in outline_content
    assert "Act 1" in outline_content
    assert "Scene01" in outline_content
    assert "Scene02" in outline_content
    assert "TODO" in outline_content
    assert "words" in outline_content.lower()


def test_incremental_update(project_structure):
    """Test incremental updates to scenes."""
    args = Mock()
    args.config = str(project_structure / "config.yaml")
    args.no_compile = True
    args.report_only = False
    args.force = False

    # Initial run
    manager = BookManager(args)
    manager.run()

    # Modify a scene
    scene_path = project_structure / "4_Scenes_and_Chapters" / "Drafts" / "Book1" / "Act1" / "Scene01.md"
    original_content = scene_path.read_text()
    new_content = original_content + "\nNew content added.\nTODO: Review new content"
    scene_path.write_text(new_content)

    # Run again
    manager = BookManager(args)
    manager.run()

    # Check that changes are reflected
    outline_path = project_structure / "3_Plot_and_Outline" / "outline.md"
    outline_content = outline_path.read_text()
    assert "Review new content" in outline_content


@pytest.mark.skipif(not shutil.which("pandoc"), reason="Pandoc not installed")
def test_compilation(project_structure):
    """Test actual manuscript compilation (requires pandoc)."""
    args = Mock()
    args.config = str(project_structure / "config.yaml")
    args.no_compile = False
    args.report_only = False
    args.output_format = ["docx"]

    manager = BookManager(args)
    manager.run()


def test_error_conditions(project_structure):
    """Test various error conditions."""
    args = Mock()
    args.config = str(project_structure / "config.yaml")
    args.no_compile = True

    # Setup configuration
    project_structure.joinpath("config.yaml").write_text(
        """
        stopwords: [the, and]
        top_words_count: 5
        pandoc_output_formats: [docx]
        outline_file: outline.md
        drafts_dir: 4_Scenes_and_Chapters/Drafts
        compiled_dir: Compiled
    """
    )

    manager = BookManager(args)
    manager.setup()

    # This should raise BookManagerError due to missing structure
    with pytest.raises(BookManagerError):
        manager.run()
