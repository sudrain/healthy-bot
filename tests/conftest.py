from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def bot():
    return AsyncMock()


@pytest.fixture
def pool():
    return AsyncMock()
