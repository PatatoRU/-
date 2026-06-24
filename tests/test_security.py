import subprocess


def test_no_tracked_secrets():
    result = subprocess.run(["python", "scripts/security_check.py"], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
