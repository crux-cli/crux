"""Unit tests for crux_cli.install — all subprocess calls mocked."""

import json
import subprocess
from unittest.mock import MagicMock

from crux_cli.install import (
    detect_and_install_deps,
    install_npm_package,
    install_uv_package,
    rollback_mcp_add,
)


class TestInstallNpmPackage:
    def test_successful_install(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="added 1 package\n", stderr=""),
        )
        ok, err = install_npm_package("@test/mcp-server")
        assert ok
        assert err == ""

    def test_package_not_found(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="npm error E404 Not Found"),
        )
        ok, err = install_npm_package("nonexistent-pkg")
        assert not ok
        assert "not found" in err

    def test_install_failure_reported(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="ERR! engine incompatible"),
        )
        ok, err = install_npm_package("bad-pkg")
        assert not ok
        assert "npm install failed" in err

    def test_npm_not_installed_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=FileNotFoundError("npm not found"),
        )
        ok, err = install_npm_package("any-pkg")
        assert ok

    def test_timeout_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="npm", timeout=120),
        )
        ok, err = install_npm_package("any-pkg")
        assert ok


class TestInstallUvPackage:
    def test_successful_install(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="Installed 1 package\n", stderr=""),
        )
        ok, err = install_uv_package("my-mcp-tool")
        assert ok
        assert err == ""

    def test_package_not_found(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="error: Package `fake-pkg` not found"),
        )
        ok, err = install_uv_package("fake-pkg")
        assert not ok
        assert "not found" in err

    def test_yanked_versions(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="No solution found: all versions yanked"),
        )
        ok, err = install_uv_package("yanked-pkg")
        assert not ok
        assert "not installable" in err

    def test_build_failure(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="error: Failed to build pglast"),
        )
        ok, err = install_uv_package("broken-pkg")
        assert not ok
        assert "uv tool install failed" in err

    def test_uv_not_installed_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=FileNotFoundError("uv not found"),
        )
        ok, err = install_uv_package("any-pkg")
        assert ok

    def test_timeout_skips(self, mocker):
        mocker.patch(
            "crux_cli.install.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="uv", timeout=120),
        )
        ok, err = install_uv_package("any-pkg")
        assert ok


class TestDetectAndInstallDeps:
    def test_npm_project_with_build(self, tmp_path, mocker):
        pkg_json = {"scripts": {"build": "tsc"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg_json))
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("npm" in str(c) and "install" in str(c) for c in commands)
        assert "build_cmd" in entry

    def test_npm_project_no_build(self, tmp_path, mocker):
        pkg_json = {"scripts": {"start": "node index.js"}}
        (tmp_path / "package.json").write_text(json.dumps(pkg_json))
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("npm" in str(c) and "install" in str(c) for c in commands)
        assert "build_cmd" not in entry

    def test_pyproject_toml(self, tmp_path, mocker):
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [call[0][0] for call in mock_run.call_args_list]
        assert any("uv" in str(c) and "sync" in str(c) for c in commands)

    def test_requirements_txt(self, tmp_path, mocker):
        (tmp_path / "requirements.txt").write_text("requests\n")
        mock_run = mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        commands = [str(call[0][0]) for call in mock_run.call_args_list]
        assert any("uv" in c for c in commands)

    def test_no_project_files_skips(self, tmp_path):
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert ok
        assert err == ""

    def test_npm_install_failure(self, tmp_path, mocker):
        (tmp_path / "package.json").write_text("{}")
        mocker.patch(
            "crux_cli.install.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="npm ERR! network error"),
        )
        entry = {}
        ok, err = detect_and_install_deps(tmp_path, entry)
        assert not ok
        assert "npm install failed" in err


class TestRollbackMcpAdd:
    def test_rollback_removes_registry_entry(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "mcp_definitions": {"test-mcp": {"type": "npm-package"}},
                    "skill_definitions": {},
                }
            )
        )
        rollback_mcp_add("test-mcp", {"type": "npm-package"})
        reg = json.loads(reg_path.read_text())
        assert "test-mcp" not in reg["mcp_definitions"]

    def test_rollback_deletes_source_dir(self, tmp_path, monkeypatch):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        source_dir = tmp_path / "mcps" / "test-mcp"
        source_dir.mkdir(parents=True)
        (source_dir / "index.js").write_text("// test")
        reg_path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "mcp_definitions": {
                        "test-mcp": {
                            "type": "github",
                            "source_dir": str(source_dir),
                        }
                    },
                    "skill_definitions": {},
                }
            )
        )
        rollback_mcp_add("test-mcp", {"type": "github", "source_dir": str(source_dir)})
        assert not source_dir.exists()

    def test_rollback_uvx_uninstalls(self, tmp_path, monkeypatch, mocker):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "mcp_definitions": {"test-mcp": {"type": "uvx-package", "args": ["my-tool"]}},
                    "skill_definitions": {},
                }
            )
        )
        mock_run = mocker.patch("crux_cli.install.subprocess.run")
        rollback_mcp_add("test-mcp", {"type": "uvx-package", "args": ["my-tool"]})
        mock_run.assert_called_once()
        assert "uninstall" in str(mock_run.call_args)

    def test_rollback_npm_uninstalls(self, tmp_path, monkeypatch, mocker):
        monkeypatch.setenv("CRUX_TEST_ROOT", str(tmp_path))
        monkeypatch.delenv("CRUX_HOME", raising=False)
        reg_path = tmp_path / "registry.json"
        reg_path.write_text(
            json.dumps(
                {
                    "version": "1.0.0",
                    "mcp_definitions": {"test-mcp": {"type": "npm-package", "args": ["-y", "@test/pkg"]}},
                    "skill_definitions": {},
                }
            )
        )
        mock_run = mocker.patch("crux_cli.install.subprocess.run")
        rollback_mcp_add("test-mcp", {"type": "npm-package", "args": ["-y", "@test/pkg"]})
        mock_run.assert_called_once()
        assert "uninstall" in str(mock_run.call_args)
