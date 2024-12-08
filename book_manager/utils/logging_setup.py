# File: book_manager/utils/logging_setup.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Logging Setup Module
--------------------

Provides a basic logging configuration for the book_manager project.

Example:
    from book_manager.utils.logging_setup import get_logger
    logger = get_logger(__name__)
    logger.info("This is an info message.")

Doctest:
    >>> from book_manager.utils.logging_setup import get_logger
    >>> logger = get_logger("test")
    >>> logger.info("Test message")  # Should print to stdout
"""

import logging


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name (str): The name of the logger (usually __name__).

    Returns:
        logging.Logger: A logger instance with basic configuration.
    """
    # If needed, adjust configuration once and reuse
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(name)
