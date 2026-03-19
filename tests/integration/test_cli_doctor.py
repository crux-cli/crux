"""Integration tests: crux init, crux doctor"""

import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestCruxInit:
    def test_init_runs(self, crux_env):
        env, root = crux_env
        result = run_crux("init", env=env)
        assert result.returncode == 0
        assert "Setup complete" in result.stdout


@pytest.mark.integration
class TestCruxDoctor:
    def test_doctor_runs(self, crux_env):
        env, root = crux_env
        result = run_crux("doctor", env=env)
        assert result.returncode == 0
        assert "CRUX DOCTOR" in result.stdout

    def test_doctor_does_not_check_secrets(self, crux_env):
        env, root = crux_env
        result = run_crux("doctor", env=env)
        assert "secret" not in result.stdout.lower()
        assert "crux secret" not in result.stdout
