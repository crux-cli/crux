"""Integration tests: crux doctor"""
import pytest

from .conftest import run_crux


@pytest.mark.integration
class TestCruxDoctor:
    def test_environment_checks_header(self, crux_env):
        env, _ = crux_env
        result = run_crux("doctor", env=env)
        assert "Environment" in result.stdout

    def test_reports_missing_src_dir(self, crux_env):
        env, root = crux_env
        import shutil
        shutil.rmtree(root / "src")
        result = run_crux("doctor", env=env)
        assert result.returncode == 0

    def test_runtime_dependencies_checked(self, crux_env):
        env, _ = crux_env
        result = run_crux("doctor", env=env)
        assert "node" in result.stdout
        assert "uv" in result.stdout
        assert "git" in result.stdout

    def test_exits_zero_in_healthy_env(self, crux_env):
        env, _ = crux_env
        result = run_crux("doctor", env=env)
        assert result.returncode == 0
