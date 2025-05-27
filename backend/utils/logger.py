#! /usr/bin/env python3


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


class Logger:
    """Centralized logger for the application."""
    _logger = None

    @classmethod
    def setup_logger(cls, app_config):
        """
        Sets up and configures the application-wide logger.

        Args:
            app_config (dict): The application configuration dictionary,
                               containing keys like 'LOG_FILE', 'LOG_LEVEL',
                               'LOG_FORMAT', 'LOG_DATEFORMAT', 'LOG_MAX_SIZE',
                               'LOG_BACKUPS', and 'DEBUG'.

        Returns:
            logging.Logger: The configured logger instance.
        """
        if cls._logger is not None:
            return cls._logger

        log_file = app_config.get('LOG_FILE')
        logs_dir = Path(log_file).parent
        logs_dir.mkdir(exist_ok=True, parents=True)

        logger = logging.getLogger('secrets_manager')
        log_level = getattr(logging, app_config.get('LOG_LEVEL', 'INFO'))
        logger.setLevel(log_level)

        if logger.hasHandlers():
            logger.handlers.clear()

        formatter = logging.Formatter(
            app_config.get('LOG_FORMAT'),
            datefmt=app_config.get('LOG_DATEFORMAT')
        )

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=app_config.get('LOG_MAX_SIZE', 10 * 1024 * 1024),
            backupCount=app_config.get('LOG_BACKUPS', 7)
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)

        if app_config.get('DEBUG', False):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(log_level)
            logger.addHandler(console_handler)

        logger.propagate = False

        cls._logger = logger
        return logger

    @classmethod
    def get_logger(cls):
        """
        Retrieves the singleton instance of the configured logger.

        Returns:
            logging.Logger: The application logger instance.

        Raises:
            RuntimeError: If the logger has not been set up by calling `setup_logger` first.
        """
        if cls._logger is None:
            raise RuntimeError("Logger has not been set up. Call setup_logger first.")
        return cls._logger
