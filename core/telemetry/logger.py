"""Structured JSON Logger."""

import logging
import json
from typing import Any

class JsonFormatter(logging.Formatter):
    """Formats logs as JSON with trace IDs."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "message": record.getMessage(),
            "name": record.name,
        }
        # Include any extra attributes passed via the `extra` dictionary
        # We skip standard LogRecord attributes
        standard_attrs = {"args", "asctime", "created", "exc_info", "exc_text", "filename", 
                          "funcName", "levelname", "levelno", "lineno", "module", "msecs", 
                          "message", "msg", "name", "pathname", "process", "processName", 
                          "relativeCreated", "stack_info", "thread", "threadName", "taskName", "color_message"}
                          
        for key, value in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = value
                
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """Returns a JSON configured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
