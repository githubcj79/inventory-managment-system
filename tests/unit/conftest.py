# tests/unit/conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_db():
    db = Mock()
    db.products = Mock()
    db.inventory = Mock()
    return db
