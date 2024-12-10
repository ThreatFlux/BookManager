#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Book Manager Main Module
-----------------------

Main entry point for the book manager project.

Features:
- Directory structure scanning
- Scene analysis with caching
- Manuscript compilation
- Progress tracking
- Detailed reporting

Usage:
    book_manager [options]

Options:
    --no-compile          Skip manuscript compilation
    --report-only         Only generate outline report
    --output-format       Comma-separated list of output formats
    --config             Path to config file
    --force              Force reanalysis of all scenes
    --verbose            Increase output verbosity
    --quiet              Suppress non-error output
"""
import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import pytest
import yaml

from book_manager.utils.config_loader import load_config, get_config, reload_config
from book_manager.utils.logging_setup import get_logger
from book_manager.structure.dir_scanner import scan_project
from book_manager.analysis.text_analysis import analyze_scene, get_analyzer
from book_manager.compile.compiler import batch_compile, CompilationError
from tqdm import tqdm

logger = get_logger(__name__)


def ensure_config(args: argparse.Namespace) -> None:
    """
    Ensure config file exists with defaults and proper permissions.

    Args:
        args: Command line arguments containing config path

    Raises:
        BookManagerError: If config file cannot be created or accessed
    """
    config_path = Path(args.config)

    try:
        # Create config directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if not config_path.exists():
            default_config = {
                'stopwords': ["the", "and", "to", "of", "a", "in", "that",
                              "is", "for", "with", "on", "as", "it", "at", "by"],
                'top_words_count': 5,
                'pandoc_output_formats': ['docx', 'epub'],  # PDF disabled by default
                'outline_file': "3_Plot_and_Outline/outline.md",
                'drafts_dir': "4_Scenes_and_Chapters/Drafts",
                'compiled_dir': "Compiled",
                'cache_size': 1000,
                'max_file_size': 10485760,  # 10MB
                'encoding': 'utf-8',
                'compilation': {
                    'timeout': 300,
                    'retries': 2,
                    'formats': {
                        'pdf': {
                            'enabled': False,  # Disabled by default
                            'extra_args': ['--pdf-engine=xelatex']
                        },
                        'docx': {
                            'enabled': True,
                            'extra_args': []
                        },
                        'epub': {
                            'enabled': True,
                            'extra_args': ['--epub-chapter-level=2']
                        }
                    }
                }
            }

            # Write config with proper permissions
            config_path.write_text(
                yaml.dump(default_config,
                          default_flow_style=False),
                encoding='utf-8'
            )

            # Set readable/writable for user only
            config_path.chmod(0o600)

            logger.info(f"Created default configuration at {config_path}")

        # Validate config can be read
        with open(config_path, 'r', encoding='utf-8') as f:
            yaml.safe_load(f)

    except (OSError, yaml.YAMLError) as e:
        raise BookManagerError(f"Configuration error: {e}")

class BookManagerError(Exception):
    """Base exception for book manager errors."""
    pass


class CommandLineParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            description="Book project management tool",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        self._add_arguments()
        self._args = None  # Store parsed args

    def _add_arguments(self) -> None:
        """Add command line arguments to parser."""
        self.parser.add_argument(
            '--no-compile',
            action='store_true',
            help="Skip manuscript compilation"
        )
        self.parser.add_argument(
            '--report-only',
            action='store_true',
            help="Only generate outline report"
        )
        self.parser.add_argument(
            '--output-format',
            type=lambda x: x.split(','),
            help="Comma-separated list of output formats (pdf,docx,epub)"
        )
        self.parser.add_argument(
            '--config',
            type=str,
            default='config.yaml',
            help="Path to config file (default: config.yaml)"
        )
        self.parser.add_argument(
            '--force',
            action='store_true',
            help="Force reanalysis of all scenes"
        )
        self.parser.add_argument(
            '--quiet',
            action='store_true',
            help="Suppress non-error output"
        )
        self.parser.add_argument(
            '--verbose',
            action='store_true',
            help="Increase output verbosity"
        )
    def parse(self) -> argparse.Namespace:
        """Parse and validate command line arguments."""
        args = self.parser.parse_args()

        # Check for invalid argument combinations
        if args.verbose and args.quiet:
            raise ValueError("Cannot specify both --verbose and --quiet")

        # Validate output formats if specified
        if args.output_format:
            valid_formats = {'pdf', 'docx', 'epub'}
            invalid_formats = set(args.output_format) - valid_formats
            if invalid_formats:
                raise ValueError(f"Invalid output formats: {', '.join(invalid_formats)}")

        return args

# And in test_main.py
def test_invalid_arguments(cli_parser):
    """Test handling of invalid argument combinations."""
    args = cli_parser.parser.parse_args(['--verbose', '--quiet'])

    with pytest.raises(ValueError):
        cli_parser.parse()  # This will raise ValueError due to conflicting args


class BookManager:
    """
    Manages the book project workflow.

    Attributes:
        args: Command line arguments
        config: Configuration dictionary
    """

    def __init__(self, args: argparse.Namespace):
        """Initialize with command line arguments."""
        self.args = args
        self.config = None
        self.structure = None
        self.setup()

    def setup(self) -> None:
        """
        Set up the manager.

        Raises:
            BookManagerError: If setup fails
        """
        try:
            # Load configuration
            load_config(self.args.config)
            self.config = get_config()

            # Create necessary directories
            Path(self.config['compiled_dir']).mkdir(exist_ok=True)
            Path(self.config['outline_file']).parent.mkdir(
                parents=True,
                exist_ok=True
            )

        except Exception as e:
            raise BookManagerError(f"Setup failed: {e}")

    def scan_project(self) -> None:
        """
        Scan project structure.

        Raises:
            BookManagerError: If scanning fails
        """
        logger.info("Scanning project structure...")
        self.structure = scan_project()

        if not self.structure:
            raise BookManagerError("No valid book structure found")

    def analyze_scenes(self) -> None:
        """Analyze all scenes in the structure."""
        total_scenes = sum(len(scenes) for book in self.structure.values()
                           for scenes in book.values())

        with tqdm(total=total_scenes,
                  desc="Analyzing scenes",
                  position=0) as pbar:
            for book_num in self.structure:
                for act_num in self.structure[book_num]:
                    for scene in self.structure[book_num][act_num]:
                        results = analyze_scene(
                            scene['path'],
                            use_cache=not self.args.force
                        )
                        if results:
                            scene.update(results)
                        else:
                            raise BookManagerError(
                                f"Failed to analyze {scene['path']}"
                            )
                        pbar.update(1)

    def generate_outline(self) -> str:
        """
        Generate outline content.

        Returns:
            str: Markdown formatted outline
        """
        lines = ["# Book Project Outline\n"]
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        total_words = 0
        total_scenes = 0
        total_todos = 0

        for book_num in sorted(self.structure.keys()):
            lines.append(f"\n## Book {book_num}")
            book_words = 0

            for act_num in sorted(self.structure[book_num].keys()):
                lines.append(f"\n### Act {act_num}")
                act_words = 0

                for scene in sorted(self.structure[book_num][act_num],
                                    key=lambda x: x['scene_num']):
                    total_scenes += 1
                    scene_path = scene['path']
                    word_count = scene.get('word_count', 0)
                    top_words = scene.get('top_words', [])
                    todos = scene.get('todos', [])

                    act_words += word_count
                    total_todos += len(todos)

                    rel_path = os.path.relpath(scene_path,
                                               Path(self.config['outline_file']).parent)

                    lines.append(f"\n#### {scene_path.stem}")
                    lines.append(f"- Words: {word_count:,}")

                    if top_words:
                        lines.append(f"- Frequent terms: {', '.join(top_words)}")

                    if todos:
                        lines.append("\nTODOs:")
                        for todo in todos:
                            lines.append(f"- [ ] {todo}")

                lines.append(f"\nAct {act_num} total words: {act_words:,}")
                book_words += act_words

            lines.append(f"\nBook {book_num} total words: {book_words:,}")
            total_words += book_words

        lines.append(f"\n## Project Statistics")
        lines.append(f"- Total scenes: {total_scenes:,}")
        lines.append(f"- Total word count: {total_words:,}")
        lines.append(f"- Outstanding TODOs: {total_todos:,}")

        return "\n".join(lines)

    def save_outline(self, content: str) -> None:
        """
        Save outline content to file.

        Args:
            content: Markdown formatted outline

        Raises:
            BookManagerError: If save fails
        """
        try:
            outline_path = Path(self.config['outline_file'])
            outline_path.write_text(content, encoding='utf-8')
            logger.info(f"Outline saved to {outline_path}")
        except IOError as e:
            raise BookManagerError(f"Failed to save outline: {e}")

    def compile_manuscript(self) -> None:
        """
        Compile manuscript if requested.

        Raises:
            BookManagerError: If compilation fails
        """
        if not self.args.no_compile and not self.args.report_only:
            formats = (self.args.output_format or
                       self.config['pandoc_output_formats'])

            logger.info(f"Compiling manuscript to: {', '.join(formats)}")

            try:
                success, files = batch_compile(
                    self.structure,
                    formats=formats
                )
                if not success:
                    raise BookManagerError("Manuscript compilation failed")
                logger.info("Created files: " + ", ".join(files))
            except CompilationError as e:
                raise BookManagerError(f"Compilation error: {e}")

    def run(self) -> None:
        """
        Run the complete workflow.

        Raises:
            BookManagerError: If any step fails
        """
        start_time = time.time()

        try:
            self.setup()
            self.scan_project()
            if not self.args.report_only:
                self.analyze_scenes()
            outline = self.generate_outline()
            self.save_outline(outline)
            self.compile_manuscript()

            duration = time.time() - start_time
            logger.info(f"Book manager completed successfully in {duration:.1f}s")

        except BookManagerError as e:
            logger.error(str(e))
            raise


def main() -> int:
    """
    Main entry point.

    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    try:
        args = CommandLineParser().parse()
        manager = BookManager(args)
        manager.run()
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        if args.verbose:
            logger.exception("Detailed error information:")
        return 1


if __name__ == "__main__":
    sys.exit(main())