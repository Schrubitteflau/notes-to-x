"""Structured logging configuration for the pipeline."""

import logging
import sys

import structlog


def configure_logging(verbose: bool = True, json_output: bool = False) -> None:
    """
    Configure structured logging for the application.

    Args:
        verbose: If True, set log level to INFO, otherwise WARNING
        json_output: If True, output logs as JSON, otherwise as console-friendly format
    """
    log_level = logging.INFO if verbose else logging.WARNING

    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
        force=True,
    )

    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if json_output:
        # JSON output for production/log aggregation
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Console-friendly output for development
        processors.extend(
            [
                structlog.dev.ConsoleRenderer(
                    colors=sys.stdout.isatty(),
                    exception_formatter=structlog.dev.plain_traceback,
                )
            ]
        )

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)
