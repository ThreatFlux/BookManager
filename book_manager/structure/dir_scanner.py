# File: book_manager/structure/dir_scanner.py
# !/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Directory Scanner Module
-----------------------

Scans the project directory structure for books, acts, and scenes.
Uses tqdm for progress indication during scanning.

Example:
    from book_manager.structure.dir_scanner import scan_project
    structure = scan_project()
    print(structure)  # Shows books/acts/scenes hierarchy

The structure dictionary format is:
{
    book_num: {
        act_num: [
            {
                'path': Path object,
                'scene_num': int,
                'word_count': int,
                'top_words': List[str],
                'todos': List[str]
            }
        ]
    }
}
"""

import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from tqdm import tqdm

from ..utils.config_loader import get_config
from ..utils.logging_setup import get_logger

logger = get_logger(__name__)


def extract_book_act_from_path(path_parts: Tuple[str, ...]) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract book and act numbers from path parts.

    Args:
        path_parts: Tuple of path parts (e.g., ("Book1", "Act2"))

    Returns:
        Tuple of (book_number, act_number) or (None, None) if not found

    >>> extract_book_act_from_path(("Book1", "Act2"))
    (1, 2)
    >>> extract_book_act_from_path(("Chapter1", "Scene1"))
    (None, None)
    """
    book_pattern = re.compile(r"^Book(\d+)$", re.IGNORECASE)
    act_pattern = re.compile(r"^Act(\d+)$", re.IGNORECASE)

    book_num = act_num = None

    for part in path_parts:
        if book_match := book_pattern.match(part):
            book_num = int(book_match.group(1))
        elif act_match := act_pattern.match(part):
            act_num = int(act_match.group(1))

    return book_num, act_num


def get_scene_number(path: Path) -> int:
    """
    Extract scene number from filename or return 9999 if not found.

    Args:
        path: Path object for the scene file

    Returns:
        int: Scene number or 9999 if not found

    >>> from pathlib import Path
    >>> get_scene_number(Path("Scene01.md"))
    1
    >>> get_scene_number(Path("random.md"))
    9999
    """
    if match := re.search(r"(\d+)", path.stem):
        return int(match.group(1))
    return 9999


def scan_project() -> Dict:
    """Scan the project directory for books, acts, and scenes."""
    config = get_config()
    drafts_dir = Path(config['drafts_dir'])
    structure = {}

    if not drafts_dir.exists():
        logger.warning(f"Drafts directory not found: {drafts_dir}")
        return {}

    try:
        # Look for files first to set up progress bar
        md_files = list(drafts_dir.rglob("*.md"))

        with tqdm(total=len(md_files), desc="Scanning files") as pbar:
            for file_path in md_files:
                relative_path = file_path.relative_to(drafts_dir)
                parts = relative_path.parts

                # Extract book and act numbers
                book_num = act_num = None
                for part in parts:
                    if book_match := re.match(r"^Book(\d+)$", part, re.IGNORECASE):
                        book_num = int(book_match.group(1))
                    elif act_match := re.match(r"^Act(\d+)$", part, re.IGNORECASE):
                        act_num = int(act_match.group(1))

                if book_num is not None and act_num is not None:
                    if book_num not in structure:
                        structure[book_num] = {}
                    if act_num not in structure[book_num]:
                        structure[book_num][act_num] = []

                    structure[book_num][act_num].append({
                        'path': file_path,
                        'scene_num': get_scene_number(file_path)
                    })

                pbar.update(1)

        # Sort scenes within each act
        for book in structure.values():
            for act in book.values():
                act.sort(key=lambda x: x['scene_num'])

    except Exception as e:
        logger.error(f"Error scanning project: {e}")
        return {}

    return structure

# And in test_scan_project
def test_scan_project(temp_project, monkeypatch):
    """Test project structure scanning."""
    from book_manager.utils import config_loader

    # Create test structure first
    drafts_dir = temp_project / "4_Scenes_and_Chapters/Drafts"
    test_dir = drafts_dir / "Book1/Act1"
    test_dir.mkdir(parents=True, exist_ok=True)
    (test_dir / "Scene01.md").write_text("Test content")

    def mock_get_config():
        return {
            'drafts_dir': str(drafts_dir)
        }

    monkeypatch.setattr(config_loader, "get_config", mock_get_config)

    structure = scan_project()
    assert 1 in structure, "Book1 not found in structure"
    assert 1 in structure[1], "Act1 not found in Book1"
    assert len(structure[1][1]) == 1, "Scene not found in Act1"


if __name__ == "__main__":
    import doctest

    doctest.testmod()