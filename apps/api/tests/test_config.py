"""Configuration validation tests."""

import pytest
from gradpath_api.core.config import Settings
from pydantic import ValidationError


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="demo")  # type: ignore[arg-type]
