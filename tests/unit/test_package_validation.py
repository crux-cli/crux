"""Unit tests for crux_cli.package_validation — all subprocess calls mocked."""

import subprocess
from unittest.mock import MagicMock

from crux_cli.package_validation import validate_npm_package, validate_pypi_package


class TestValidateNpmPackage:
    def test_existing_package_passes(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=[
                MagicMock(returncode=0, stdout="some-package\n", stderr=""),  # npm view
                MagicMock(returncode=0, stdout="", stderr=""),  # npm cache add
            ],
        )
        ok, err = validate_npm_package("some-package")
        assert ok
        assert err == ""

    def test_nonexistent_package_fails(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="E404 - Not found"),
        )
        ok, err = validate_npm_package("nonexistent-xyz")
        assert not ok
        assert "not found" in err

    def test_404_in_stderr_detected(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="404 Not Found - GET"),
        )
        ok, err = validate_npm_package("bad-pkg")
        assert not ok
        assert "not found" in err

    def test_scoped_package_with_version(self, mocker):
        mock_run = mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=[
                MagicMock(returncode=0, stdout="@scope/pkg\n", stderr=""),  # npm view
                MagicMock(returncode=0, stdout="", stderr=""),  # npm cache add
            ],
        )
        ok, err = validate_npm_package("@scope/pkg@1.0.0")
        assert ok
        # First call (npm view) should query @scope/pkg (without version)
        first_call_args = mock_run.call_args_list[0][0][0]
        assert "@scope/pkg" in first_call_args
        assert "1.0.0" not in " ".join(first_call_args)

    def test_npm_not_installed_skips_validation(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=FileNotFoundError("npm not found"),
        )
        ok, err = validate_npm_package("any-package")
        assert ok

    def test_timeout_skips_validation(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="npm", timeout=15),
        )
        ok, err = validate_npm_package("any-package")
        assert ok

    def test_other_npm_error_reported(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="ENETWORK connection refused"),
        )
        ok, err = validate_npm_package("some-pkg")
        assert not ok
        assert "npm lookup failed" in err

    def test_cache_add_failure_reported(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=[
                MagicMock(returncode=0, stdout="pkg\n", stderr=""),  # npm view succeeds
                MagicMock(returncode=1, stdout="", stderr="ERR! Cannot install, wrong platform"),  # cache fails
            ],
        )
        ok, err = validate_npm_package("pkg")
        assert not ok
        assert "failed to download" in err


class TestValidatePypiPackage:
    def test_existing_package_passes(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        ok, err = validate_pypi_package("requests")
        assert ok
        assert err == ""

    def test_no_versions_available(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(
                returncode=1, stdout="", stderr="No solution found: all versions of pkg were yanked"
            ),
        )
        ok, err = validate_pypi_package("yanked-pkg")
        assert not ok
        assert "not installable" in err

    def test_package_not_found(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="Package not found: fake-pkg"),
        )
        ok, err = validate_pypi_package("fake-pkg")
        assert not ok
        assert "not found" in err

    def test_strips_extras_and_version(self, mocker):
        mock_run = mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=0, stdout="", stderr=""),
        )
        ok, _ = validate_pypi_package("pkg[extra]>=1.0")
        assert ok
        call_args = mock_run.call_args[0][0]
        assert "pkg" in call_args
        assert "[extra]" not in " ".join(call_args)

    def test_uv_not_installed_skips_validation(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=FileNotFoundError("uv not found"),
        )
        ok, err = validate_pypi_package("any-package")
        assert ok

    def test_timeout_skips_validation(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="uv", timeout=15),
        )
        ok, err = validate_pypi_package("any-package")
        assert ok

    def test_other_uv_error_reported(self, mocker):
        mocker.patch(
            "crux_cli.package_validation.subprocess.run",
            return_value=MagicMock(returncode=1, stdout="", stderr="some random error happened"),
        )
        ok, err = validate_pypi_package("some-pkg")
        assert not ok
        assert "uv lookup failed" in err
