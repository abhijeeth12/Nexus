"""Tests for telemetry logger."""

import json
import logging
from io import StringIO
from core.telemetry.logger import get_logger, JsonFormatter

def test_json_logger() -> None:
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    
    logger.info("Test message", extra={"trace_id": "tx_123"})
    output = stream.getvalue()
    data = json.loads(output)
    
    assert data["message"] == "Test message"
    assert data["level"] == "INFO"
    assert data["trace_id"] == "tx_123"
