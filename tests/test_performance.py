#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance tests for book manager functionality.
Measures execution time and memory usage for various operations.
"""

import pytest
import time
import psutil
import os
import random
import string
import concurrent.futures
from pathlib import Path
from contextlib import contextmanager
from book_manager.main import BookManager
from book_manager.analysis.text_analysis import TextAnalyzer  # Fixed import
from unittest.mock import Mock


class TimeMeasurement:
    """Class to store time measurement results."""

    def __init__(self):
        self.start_time = 0
        self.elapsed = 0.0


class MemoryMeasurement:
    """Class to store memory measurement results."""

    def __init__(self):
        self.start_mem = 0
        self.used = 0


@contextmanager
def measure_time():
    """
    Measure execution time using a context manager.

    Yields:
        TimeMeasurement: Object containing timing information
    """
    measurement = TimeMeasurement()
    measurement.start_time = time.perf_counter()
    try:
        yield measurement
    finally:
        measurement.elapsed = time.perf_counter() - measurement.start_time


@contextmanager
def measure_memory():
    """
    Measure memory usage using a context manager.

    Yields:
        MemoryMeasurement: Object containing memory usage information
    """
    measurement = MemoryMeasurement()
    process = psutil.Process(os.getpid())
    measurement.start_mem = process.memory_info().rss
    try:
        yield measurement
    finally:
        measurement.used = process.memory_info().rss - measurement.start_mem


def generate_random_text(words: int) -> str:
    """
    Generate random text with specified number of words.

    Args:
        words: Number of words to generate

    Returns:
        str: Generated random text
    """
    word_list = []
    for _ in range(words):
        word_len = random.randint(3, 10)
        word = "".join(random.choices(string.ascii_lowercase, k=word_len))
        word_list.append(word)
    return " ".join(word_list)


def generate_test_files(project_dir: Path, num_files: int = 10):
    """
    Generate test files for performance testing.

    Args:
        project_dir: Project root directory
        num_files: Number of files to generate
    """
    drafts = project_dir / "4_Scenes_and_Chapters/Drafts/Book1/Act1"
    drafts.mkdir(parents=True, exist_ok=True)

    for i in range(num_files):
        scene_path = drafts / f"Scene{i:02d}.md"
        content = f"# Scene {i}\n\n"
        content += generate_random_text(1000)  # 1000 random words
        content += f"\nTODO: Review scene {i}\n"
        scene_path.write_text(content)


@pytest.fixture(autouse=True)
def clean_analyzer_cache():
    """Clean analyzer cache between tests."""
    analyzer = TextAnalyzer()  # Create new analyzer instance
    if hasattr(analyzer, "_cache"):
        analyzer._cache.clear()  # Clear cache if it exists
    yield


@pytest.fixture
def large_project(tmp_path):
    """
    Create a large project structure for performance testing.

    Args:
        tmp_path: Pytest temporary path fixture

    Returns:
        Path: Path to test project
    """
    drafts = tmp_path / "4_Scenes_and_Chapters" / "Drafts"

    # Create 5 books, each with 5 acts, each with 20 scenes
    for book in range(1, 6):
        for act in range(1, 6):
            act_dir = drafts / f"Book{book}" / f"Act{act}"
            act_dir.mkdir(parents=True)

            for scene in range(1, 21):
                scene_path = act_dir / f"Scene{scene:02d}.md"
                content = f"# Scene {scene}\n\n"
                content += generate_random_text(1000)
                content += f"\nTODO: Review scene {scene}\n"
                scene_path.write_text(content)

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
        cache_size: 1000
        max_file_size: 1048576
        encoding: utf-8
    """
    )

    return tmp_path


def test_scanning_performance(large_project):
    """Test performance of project structure scanning."""
    args = Mock(config=str(large_project / "config.yaml"), no_compile=True, report_only=False, force=False)
    manager = BookManager(args)

    with measure_time() as timing:
        try:
            manager.scan_project()
        except Exception as e:
            pytest.fail(f"Scanning failed: {e}")

    assert timing.elapsed < 2.0, f"Scanning took too long: {timing.elapsed:.2f}s"


def test_analysis_performance(large_project):
    """Test performance of scene analysis."""
    generate_test_files(large_project, num_files=5)
    analyzer = TextAnalyzer()
    scene_files = list(large_project.rglob("*.md"))

    with measure_time() as no_cache_time:
        for scene in scene_files:
            try:
                analyzer.analyze_scene(scene, use_cache=False)
            except Exception as e:
                pytest.fail(f"Analysis without cache failed: {e}")

    with measure_time() as cache_time:
        for scene in scene_files:
            try:
                analyzer.analyze_scene(scene, use_cache=True)
            except Exception as e:
                pytest.fail(f"Analysis with cache failed: {e}")

    assert cache_time.elapsed < no_cache_time.elapsed, (
        f"Cached analysis ({cache_time.elapsed:.2f}s) not faster than " f"uncached ({no_cache_time.elapsed:.2f}s)"
    )


def test_memory_usage(large_project):
    """Test memory usage during processing."""
    args = Mock(config=str(large_project / "config.yaml"), no_compile=True, report_only=False, force=True)
    manager = BookManager(args)

    with measure_memory() as memory:
        try:
            manager.run()
        except Exception as e:
            pytest.fail(f"Manager run failed: {e}")

    max_memory = 500 * 1024 * 1024  # 500MB
    assert memory.used < max_memory, (
        f"Memory usage too high: {memory.used / 1024 / 1024:.1f}MB " f"(max: {max_memory / 1024 / 1024:.1f}MB)"
    )


def test_cache_effectiveness(large_project):
    """Test effectiveness of caching mechanism."""
    analyzer = TextAnalyzer()
    scene_files = list(large_project.rglob("*.md"))[:5]

    # First pass - no cache
    with measure_time() as no_cache_time:
        for scene in scene_files:
            try:
                analyzer.analyze_scene(scene, use_cache=False)
            except Exception as e:
                pytest.fail(f"Analysis without cache failed: {e}")

    # Second pass - with cache
    with measure_time() as cache_time:
        for scene in scene_files:
            try:
                analyzer.analyze_scene(scene, use_cache=True)
            except Exception as e:
                pytest.fail(f"Cached analysis failed: {e}")

    assert cache_time.elapsed < no_cache_time.elapsed * 1.5, (
        f"Cache not effective enough: cached={cache_time.elapsed:.2f}s, " f"uncached={no_cache_time.elapsed:.2f}s"
    )


def test_large_file_handling(large_project):
    """Test performance with large files."""
    large_scene = large_project / "4_Scenes_and_Chapters/Drafts/large_scene.md"
    content = generate_random_text(100000)  # Very large scene
    large_scene.write_text(content)

    analyzer = TextAnalyzer()

    with measure_time() as timing:
        try:
            analyzer.analyze_scene(large_scene)
        except Exception as e:
            pytest.fail(f"Large file analysis failed: {e}")

    assert timing.elapsed < 5.0, f"Large file processing too slow: {timing.elapsed:.2f}s"


def test_concurrent_access(large_project):
    """Test performance with concurrent access."""
    analyzer = TextAnalyzer()
    scene_files = list(large_project.rglob("*.md"))[:20]

    def analyze_file(file_path):
        try:
            return analyzer.analyze_scene(file_path)
        except Exception as e:
            pytest.fail(f"Concurrent analysis failed: {e}")
        return None

    with measure_time() as timing:
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(analyze_file, scene_files))

    assert all(r is not None for r in results), "Some files failed analysis"
    assert timing.elapsed < 10.0, f"Concurrent processing too slow: {timing.elapsed:.2f}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
