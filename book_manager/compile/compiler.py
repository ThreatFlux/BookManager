#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Compiler Module
--------------

Handles manuscript compilation using pandoc with robust error handling,
progress tracking, and support for multiple output formats.

Requirements:
    - pandoc must be installed and accessible in the system PATH
    - appropriate LaTeX installation for PDF compilation
    - appropriate fonts for various formats
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable
from tqdm import tqdm

from ..utils.config_loader import get_config
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


class CompilationError(Exception):
    """Custom exception for compilation errors."""
    pass


class PandocMissingError(CompilationError):
    """Exception raised when pandoc is not available."""
    pass


class InvalidStructureError(CompilationError):
    """Exception raised when the book structure is invalid."""
    pass


class CompilationConfig:
    """
    Configuration for manuscript compilation.

    Attributes:
        formats (List[str]): Output formats to generate
        temp_dir (Path): Directory for temporary files
        output_dir (Path): Directory for compiled outputs
        extra_args (Dict[str, List[str]]): Format-specific pandoc arguments
    """

    FORMAT_REQUIREMENTS = {
        'pdf': ['xelatex', '--pdf-engine=xelatex'],
        'epub': ['--epub-chapter-level=2'],
        'docx': [],
        'html': ['--standalone', '--self-contained']
    }

    def __init__(
            self,
            formats: Optional[List[str]] = None,
            extra_args: Optional[Dict[str, List[str]]] = None,
            timeout: int = 300
    ) -> None:
        """
        Initialize compilation configuration.

        Args:
            formats: List of output formats to generate
            extra_args: Additional pandoc arguments per format
            timeout: Compilation timeout in seconds
        """
        config = get_config()
        self.formats = formats or config['pandoc_output_formats']
        self.output_dir = Path(config['compiled_dir'])
        self.extra_args = extra_args or {}
        self.timeout = timeout

    def get_format_args(self, format_name: str) -> List[str]:
        """
        Get combined arguments for a specific format.

        Args:
            format_name: Name of the output format

        Returns:
            List[str]: Combined pandoc arguments
        """
        base_args = self.FORMAT_REQUIREMENTS.get(format_name, [])
        extra_args = self.extra_args.get(format_name, [])
        return base_args + extra_args

    def validate_formats(self) -> None:
        """
        Validate requested formats are supported.

        Raises:
            ValueError: If any format is unsupported
        """
        unsupported = set(self.formats) - set(self.FORMAT_REQUIREMENTS.keys())
        if unsupported:
            raise ValueError(f"Unsupported output formats: {unsupported}")


class ManuscriptCompiler:
    """
    Handles manuscript compilation with proper resource management.
    """

    def __init__(
            self,
            config: CompilationConfig,
            progress_callback: Optional[Callable[[str, int, int], None]] = None
    ) -> None:
        """
        Initialize compiler with configuration.

        Args:
            config: Compilation configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config
        self.temp_dir = None
        self.progress_callback = progress_callback
        self._check_requirements()

    def __enter__(self) -> 'ManuscriptCompiler':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit with cleanup."""
        self._cleanup_temp_dir()

    def _validate_structure(self, structure: Dict) -> None:
        """
        Validate book structure format.

        Args:
            structure: Book structure dictionary

        Raises:
            InvalidStructureError: If structure is invalid
        """
        try:
            for book_num, acts in structure.items():
                if not isinstance(book_num, int):
                    raise InvalidStructureError(f"Invalid book number: {book_num}")
                for act_num, scenes in acts.items():
                    if not isinstance(act_num, int):
                        raise InvalidStructureError(f"Invalid act number: {act_num}")
                    for scene in scenes:
                        if not isinstance(scene, dict):
                            raise InvalidStructureError("Invalid scene format")
                        if 'path' not in scene or 'scene_num' not in scene:
                            raise InvalidStructureError("Missing required scene attributes")
        except (TypeError, AttributeError) as e:
            raise InvalidStructureError(f"Invalid structure format: {e}")

    # book_manager/compile/compiler.py update the _check_requirements method:

    def _check_requirements(self) -> Tuple[bool, List[str]]:
        """
        Check if all required tools are available.

        Returns:
            Tuple[bool, List[str]]: (all_available, available_formats)

        Raises:
            PandocMissingError: If pandoc is not installed
        """
        # First check pandoc
        if not self._check_pandoc():
            raise PandocMissingError(
                "Pandoc not found. Please install pandoc:\n"
                "Ubuntu/Debian: sudo apt-get install pandoc texlive-xetex\n"
                "macOS: brew install pandoc basictex\n"
                "Windows: choco install pandoc miktex"
            )

        available_formats = []
        all_available = True

        for fmt in self.config.formats:
            if fmt == 'pdf':
                has_xelatex = self._check_xelatex()
                if has_xelatex:
                    available_formats.append('pdf')
                else:
                    all_available = False
                    logger.warning(
                        "XeLaTeX not found. PDF compilation will be disabled.\n"
                        "To enable PDF compilation, install:\n"
                        "- Ubuntu/Debian: sudo apt-get install texlive-xetex\n"
                        "- macOS: brew install basictex\n"
                        "- Windows: choco install miktex"
                    )
            else:
                available_formats.append(fmt)

        if not available_formats:
            raise CompilationError("No supported output formats available")

        return all_available, available_formats

    @staticmethod
    def _check_xelatex() -> bool:
        """
        Check if XeLaTeX is available and working.

        Returns:
            bool: True if XeLaTeX is available and working
        """
        try:
            # Check if xelatex exists
            xelatex_path = shutil.which('xelatex')
            if not xelatex_path:
                return False

            # Try running xelatex
            result = subprocess.run(
                ['xelatex', '--version'],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.info(f"Found XeLaTeX: {result.stdout.splitlines()[0]}")
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as e:
            logger.debug(f"XeLaTeX check failed: {e}")
            return False

    @staticmethod
    def _check_pandoc() -> bool:
        """Check if pandoc is available."""
        try:
            result = subprocess.run(
                ['pandoc', '--version'],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            logger.info(f"Found pandoc: {result.stdout.splitlines()[0]}")
            return True
        except (subprocess.SubprocessError, FileNotFoundError, OSError):
            return False

    def _prepare_temp_dir(self) -> Path:
        """
        Create and prepare temporary directory.

        Returns:
            Path: Path to temporary directory
        """
        self.temp_dir = Path(tempfile.mkdtemp())
        return self.temp_dir

    def _cleanup_temp_dir(self) -> None:
        """Clean up temporary directory with retries."""
        if self.temp_dir and self.temp_dir.exists():
            for attempt in range(3):
                try:
                    shutil.rmtree(self.temp_dir)
                    self.temp_dir = None
                    break
                except (OSError, IOError) as e:
                    if attempt == 2:
                        logger.error(f"Failed to cleanup temp dir: {e}")
                    time.sleep(0.1)

    def create_combined_markdown(
            self,
            structure: Dict,
            temp_dir: Path
    ) -> Optional[Path]:
        """
        Create combined markdown file from manuscript structure.

        Args:
            structure: Book structure dictionary
            temp_dir: Directory for temporary files

        Returns:
            Optional[Path]: Path to combined file or None if error

        Raises:
            IOError: If there are issues reading scene files
            InvalidStructureError: If structure is invalid
        """
        self._validate_structure(structure)
        combined_path = temp_dir / "combined_manuscript.md"
        lines = []

        try:
            total_scenes = sum(
                len(scenes) for book in structure.values()
                for scenes in book.values()
            )

            with tqdm(total=total_scenes, desc="Combining scenes") as pbar:
                for book_num in sorted(structure.keys()):
                    lines.append(f"\n# Book {book_num}\n")

                    for act_num in sorted(structure[book_num].keys()):
                        lines.append(f"\n## Act {act_num}\n")

                        for scene in sorted(
                                structure[book_num][act_num],
                                key=lambda x: x['scene_num']
                        ):
                            scene_path = scene['path']
                            lines.append(f"\n### {scene_path.stem}\n")

                            try:
                                content = scene_path.read_text(encoding='utf-8')
                                lines.append(content)
                                lines.append("\n")
                            except IOError as e:
                                logger.error(f"Error reading {scene_path}: {e}")
                                raise

                            pbar.update(1)
                            if self.progress_callback:
                                self.progress_callback("Combining scenes", pbar.n, total_scenes)

            combined_path.write_text("\n".join(lines), encoding='utf-8')
            return combined_path

        except Exception as e:
            logger.error(f"Error creating combined markdown: {e}")
            return None

    def compile_to_format(
            self,
            input_path: Path,
            output_path: Path,
            format_name: str
    ) -> bool:
        """
        Compile markdown to a specific format using pandoc.

        Args:
            input_path: Path to input markdown
            output_path: Path for output file
            format_name: Output format name

        Returns:
            bool: True if compilation successful

        Raises:
            CompilationError: If compilation fails
        """
        format_args = self.config.get_format_args(format_name)
        base_args = ['pandoc', str(input_path), '-o', str(output_path)]
        command = base_args + format_args

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            return True
        except subprocess.SubprocessError as e:
            error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
            raise CompilationError(f"Pandoc error for {format_name}: {error_msg}")
        except subprocess.TimeoutExpired:
            raise CompilationError(
                f"Compilation timeout after {self.config.timeout} seconds"
            )

    def compile_manuscript(self, structure: Dict) -> Tuple[bool, List[str]]:
        """
        Compile manuscript to all specified formats.

        Args:
            structure: Book structure dictionary

        Returns:
            Tuple[bool, List[str]]: Success status and list of created files

        Raises:
            CompilationError: If compilation fails
            InvalidStructureError: If structure is invalid
        """
        self._validate_structure(structure)
        self.config.validate_formats()
        self.config.output_dir.mkdir(exist_ok=True)
        created_files = []

        try:
            temp_dir = self._prepare_temp_dir()
            combined_md = self.create_combined_markdown(structure, temp_dir)

            if not combined_md:
                raise CompilationError("Failed to create combined markdown")

            with tqdm(total=len(self.config.formats), desc="Compiling formats") as pbar:
                for fmt in self.config.formats:
                    output_path = self.config.output_dir / f"manuscript.{fmt}"
                    logger.info(f"Compiling to {fmt}...")

                    try:
                        self.compile_to_format(combined_md, output_path, fmt)
                        created_files.append(str(output_path))
                        logger.info(f"Successfully created {output_path}")
                    except CompilationError as e:
                        logger.error(str(e))
                        raise

                    pbar.update(1)
                    if self.progress_callback:
                        self.progress_callback("Compiling formats", pbar.n, len(self.config.formats))

            return True, created_files

        except Exception as e:
            logger.error(f"Compilation failed: {e}")
            return False, created_files

        finally:
            self._cleanup_temp_dir()


def compile_manuscript(
        structure: Dict,
        formats: Optional[List[str]] = None,
        extra_args: Optional[Dict[str, List[str]]] = None,
        timeout: int = 300,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Tuple[bool, List[str]]:
    """
    Convenience function to compile manuscript.

    Args:
        structure: Book structure dictionary
        formats: List of output formats
        extra_args: Format-specific pandoc arguments
        timeout: Compilation timeout in seconds
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple[bool, List[str]]: Success status and list of created files
    """
    config = CompilationConfig(formats=formats, extra_args=extra_args, timeout=timeout)
    compiler = ManuscriptCompiler(config, progress_callback)
    return compiler.compile_manuscript(structure)


def batch_compile(
        structure: Dict,
        formats: Optional[List[str]] = None,
        extra_args: Optional[Dict[str, List[str]]] = None,
        retries: int = 2,
        timeout: int = 300,
        progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Tuple[bool, List[str]]:
    """
    Compile manuscript with retry logic.

    Args:
        structure: Book structure dictionary
        formats: List of output formats
        extra_args: Format-specific pandoc arguments
        retries: Number of retry attempts
        timeout: Compilation timeout in seconds
        progress_callback: Optional callback for progress updates

    Returns:
        Tuple[bool, List[str]]: Success status and list of created files
    """
    created_files = []

    for attempt in range(retries + 1):
        if attempt > 0:
            logger.info(f"Retry attempt {attempt}/{retries}")

        success, files = compile_manuscript(
            structure,
            formats,
            extra_args,
            timeout,
            progress_callback
        )
        created_files.extend(files)

        if success:
            return True, created_files

        if attempt < retries:
            logger.warning("Compilation failed, will retry...")
            time.sleep(2 ** attempt)  # Exponential backoff

    logger.error("All compilation attempts failed")
    return False, created_files


if __name__ == "__main__":
    import doctest

    doctest.testmod()