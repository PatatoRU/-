from pathlib import Path


def test_project_status_contains_audit_and_roadmap():
    text = Path("PROJECT_STATUS.md").read_text(encoding="utf-8")
    for required in ["Security Audit", "Roadmap", "Critical", "High", "Medium", "Future"]:
        assert required in text
