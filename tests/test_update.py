"""Unit tests for `quivo update` (CLI self-upgrade).

Network and subprocess calls are mocked — these tests perform zero real HTTP
requests and never spawn the real installer.
"""

from __future__ import annotations

import subprocess
import sys
import types

import pytest
from typer.testing import CliRunner

import quivo
from quivo.cli import app
from quivo.commands import update as update_mod

runner = CliRunner()


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #


def test_fetch_latest_cli_tag_picks_highest_version(monkeypatch):
    tags = [
        {"name": "cli-v0.1.0"},
        {"name": "cli-v0.10.0"},   # 0.10 > 0.2 under PEP 440
        {"name": "cli-v0.2.0"},
        {"name": "skills-v9.9.9"},  # ignored
        {"name": "random-tag"},     # ignored
    ]
    monkeypatch.setattr(update_mod, "_gh_get_json", lambda url: tags)
    assert update_mod._fetch_latest_cli_tag("owner/repo") == "cli-v0.10.0"


def test_fetch_latest_cli_tag_returns_none_when_no_cli_tags(monkeypatch):
    monkeypatch.setattr(
        update_mod, "_gh_get_json", lambda url: [{"name": "skills-v1.0.0"}]
    )
    assert update_mod._fetch_latest_cli_tag("owner/repo") is None


def test_fetch_latest_cli_tag_rejects_non_list(monkeypatch):
    monkeypatch.setattr(update_mod, "_gh_get_json", lambda url: {"unexpected": 1})
    with pytest.raises(RuntimeError):
        update_mod._fetch_latest_cli_tag("owner/repo")


@pytest.mark.parametrize(
    "latest,current,expected",
    [
        ("0.2.0", "0.1.0", True),
        ("0.1.0", "0.1.0", False),
        ("0.1.0", "0.2.0", False),
        ("0.10.0", "0.2.0", True),
    ],
)
def test_is_newer(latest, current, expected):
    assert update_mod._is_newer(latest, current) is expected


@pytest.mark.parametrize(
    "method,expected_head",
    [
        ("uv-tool", ["uv", "tool", "install", "--force"]),
        ("pipx", ["pipx", "install", "--force"]),
        ("uvx", ["uvx", "--refresh", "--from"]),
        ("unknown", ["uvx", "--refresh", "--from"]),
    ],
)
def test_build_argv_per_method(method, expected_head):
    argv = update_mod._build_argv(method, "owner/repo", "cli-v0.2.0")
    assert argv[: len(expected_head)] == expected_head
    # The pinned spec must always be present.
    assert "git+https://github.com/owner/repo.git@cli-v0.2.0" in argv


@pytest.mark.parametrize(
    "paths,expected",
    [
        ({"exe": "/home/u/.local/share/pipx/venvs/quivo/bin/quivo"}, "pipx"),
        ({"exe": "/home/u/.local/share/uv/tools/quivo/bin/quivo"}, "uv-tool"),
        ({"exe": "/home/u/.cache/uv/archive-v0/abc/bin/quivo"}, "uvx"),
        ({"exe": "/usr/local/bin/quivo", "prefix": "/usr/local"}, "unknown"),
    ],
)
def test_detect_install_method(monkeypatch, paths, expected):
    monkeypatch.setattr(update_mod, "_executable_path", lambda: paths["exe"])
    monkeypatch.setattr(sys, "executable", paths.get("exe", "/usr/bin/python"))
    monkeypatch.setattr(sys, "prefix", paths.get("prefix", "/opt/none"))
    assert update_mod._detect_install_method() == expected


# --------------------------------------------------------------------------- #
# Command flow (via CliRunner)
# --------------------------------------------------------------------------- #


@pytest.fixture
def stub_repo(monkeypatch):
    monkeypatch.setattr(update_mod, "resolve_repo", lambda: "owner/repo")


def test_up_to_date_short_circuits(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.5.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.5.0")
    # subprocess must never run on the happy "already latest" path.
    monkeypatch.setattr(update_mod.subprocess, "run", _boom)

    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "Up to date" in result.stdout


def test_check_reports_without_upgrading(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod.subprocess, "run", _boom)

    result = runner.invoke(app, ["update", "--check"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "New version available: 0.9.0" in result.stdout
    assert "quivo update" in result.stdout


def test_dry_run_shows_command_without_running(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")
    monkeypatch.setattr(update_mod.subprocess, "run", _boom)

    result = runner.invoke(app, ["update", "--dry-run"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "Dry run" in result.stdout
    assert "uvx --refresh --from" in result.stdout


def test_no_cli_tags_exits_ok_with_guidance(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: None)

    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "No 'cli-v*' tags found" in result.stdout


def test_resolve_error_exits_1(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")

    def _raise(repo):
        raise RuntimeError("GitHub API error 403")

    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", _raise)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_RESOLVE_ERROR


def test_successful_upgrade_runs_and_verifies(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")

    calls = []

    def fake_run(argv, **kwargs):
        calls.append(argv)
        # _run() uses no capture; _verify() captures output.
        if kwargs.get("capture_output"):
            return types.SimpleNamespace(returncode=0, stdout="quivo 0.9.0\n", stderr="")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(update_mod.subprocess, "run", fake_run)

    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "Upgraded to quivo 0.9.0" in result.stdout
    # Both the installer and the verification subprocess were invoked.
    assert len(calls) == 2


def test_installer_nonzero_propagates_exit_code(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")
    monkeypatch.setattr(
        update_mod.subprocess,
        "run",
        lambda argv, **kw: types.SimpleNamespace(returncode=7),
    )

    result = runner.invoke(app, ["update"])
    assert result.exit_code == 7


def test_installer_missing_exits_3(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")

    def _missing(argv, **kw):
        raise FileNotFoundError(argv[0])

    monkeypatch.setattr(update_mod.subprocess, "run", _missing)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_INSTALLER_MISSING


def test_timeout_exits_124(monkeypatch, stub_repo):
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")

    def _timeout(argv, **kw):
        raise subprocess.TimeoutExpired(argv, 600)

    monkeypatch.setattr(update_mod.subprocess, "run", _timeout)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_TIMEOUT


def test_verify_mismatch_warns_but_exits_ok(monkeypatch, stub_repo):
    """Installer succeeds but version cannot be confirmed → warn, still exit 0."""
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", lambda repo: "cli-v0.9.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uv-tool")

    def fake_run(argv, **kwargs):
        if kwargs.get("capture_output"):
            return types.SimpleNamespace(returncode=0, stdout="quivo 0.1.0\n", stderr="")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(update_mod.subprocess, "run", fake_run)
    result = runner.invoke(app, ["update"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "could not confirm" in result.stdout


def test_pinned_tag_skips_network(monkeypatch, stub_repo):
    """--tag must not trigger a tag lookup."""
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_fetch_latest_cli_tag", _boom)  # must not be called
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")
    monkeypatch.setattr(update_mod.subprocess, "run", _boom)

    result = runner.invoke(app, ["update", "--tag", "cli-v0.2.0", "--dry-run"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "cli-v0.2.0" in result.stdout


def test_tag_normalization_adds_prefix(monkeypatch, stub_repo):
    """A bare version like '0.2.0' should be normalised to 'cli-v0.2.0'."""
    monkeypatch.setattr(quivo, "__version__", "0.1.0")
    monkeypatch.setattr(update_mod, "_detect_install_method", lambda: "uvx")
    monkeypatch.setattr(update_mod.subprocess, "run", _boom)

    result = runner.invoke(app, ["update", "--tag", "0.2.0", "--dry-run"])
    assert result.exit_code == update_mod.EXIT_OK
    assert "cli-v0.2.0" in result.stdout


def _boom(*args, **kwargs):
    raise AssertionError("this callable should not have been invoked")
