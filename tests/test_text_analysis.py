# File: book_manager/tests/test_text_analysis.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tests for text analysis functionality.
"""

import pytest
from pathlib import Path
from book_manager.analysis.text_analysis import (
    TextAnalyzer,
    LRUCache,
    analyze_scene
)


@pytest.fixture
def analyzer():
    """Create a TextAnalyzer instance."""
    return TextAnalyzer()


@pytest.fixture
def sample_text():
    """Create sample text content."""
    return """
    # Chapter 1

    This is a test chapter with some sample text.
    The quick brown fox jumps over the lazy dog.

    TODO: Fix the description
    TODO: Add more content
    """


def test_lru_cache():
    """Test LRU cache functionality."""
    cache = LRUCache(2)

    cache.put("key1", {"value": 1})
    cache.put("key2", {"value": 2})
    cache.put("key3", {"value": 3})

    assert "key1" not in cache  # Should be evicted
    assert "key2" in cache
    assert "key3" in cache

    # Test get updates LRU order
    cache.get("key2")
    cache.put("key4", {"value": 4})
    assert "key2" in cache  # Should not be evicted
    assert "key3" not in cache  # Should be evicted


def test_word_counting(analyzer, sample_text):
    """Test word counting functionality."""
    count = analyzer.count_words(sample_text)
    assert count > 0
    assert isinstance(count, int)


def test_word_frequency(analyzer, sample_text):
    """Test word frequency analysis."""
    stopwords = frozenset(['the', 'a'])
    freq = analyzer.get_word_frequency(sample_text, stopwords)

    # Common words should be excluded
    assert 'the' not in freq

    # Verify counts
    assert freq['quick'] == 1
    assert freq['fox'] == 1


def test_todo_extraction(analyzer, sample_text):
    """Test TODO extraction."""
    todos = analyzer.extract_todos(sample_text)
    assert len(todos) == 2
    assert "Fix the description" in todos
    assert "Add more content" in todos


def test_scene_analysis(tmp_path, analyzer):
    """Test complete scene analysis."""
    scene_file = tmp_path / "scene.md"
    scene_file.write_text("""
    # Test Scene

    This is a test scene with some repeated words.
    This is another test line.

    TODO: Review this scene
    """)

    results = analyzer.analyze_scene(scene_file)
    assert results is not None
    assert results['word_count'] > 0
    assert len(results['top_words']) > 0
    assert len(results['todos']) == 1


def test_scene_analysis_caching(tmp_path, analyzer):
    """Test scene analysis caching."""
    scene_file = tmp_path / "scene.md"
    scene_file.write_text("Test content")

    # First analysis
    results1 = analyzer.analyze_scene(scene_file, use_cache=True)

    # Second analysis should use cache
    results2 = analyzer.analyze_scene(scene_file, use_cache=True)

    assert results1 == results2

    # Modify file
    scene_file.write_text("Different content")

    # Analysis should return different results
    results3 = analyzer.analyze_scene(scene_file, use_cache=True)
    assert results1 != results3


def test_large_file_handling(tmp_path, analyzer):
    """Test handling of large files."""
    large_file = tmp_path / "large.md"

    # Create a file larger than max_size
    large_content = "x" * (analyzer.config['max_file_size'] + 1)
    large_file.write_text(large_content)

    with pytest.raises(ValueError, match="File too large"):
        analyzer.analyze_scene(large_file)


def test_invalid_encoding(tmp_path, analyzer):
    """Test handling of files with invalid encoding."""
    invalid_file = tmp_path / "invalid.md"

    # Write binary content that's not valid utf-8
    with open(invalid_file, 'wb') as f:
        f.write(b'\x80\x81')

    results = analyzer.analyze_scene(invalid_file)
    assert results is None