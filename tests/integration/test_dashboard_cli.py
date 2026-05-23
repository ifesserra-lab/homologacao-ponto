import subprocess
import sys


def _cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "homologacao_ponto.cli", *args],
        capture_output=True,
        text=True,
    )


def test_dashboard_subcommand_help_exits_zero() -> None:
    result = _cli("dashboard", "--help")
    assert result.returncode == 0
    assert "--data-dir" in result.stdout
    assert "--port" in result.stdout


def test_dashboard_subcommand_missing_dashboard_dir_exits_nonzero(tmp_path: object) -> None:
    result = _cli("dashboard", "--data-dir", str(tmp_path), "--dashboard-dir", "/nonexistent/dashboard")
    assert result.returncode != 0
