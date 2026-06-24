from pathlib import Path

import pytest


def test_project_files_exist():
    assert Path("app/main.py").exists()
    assert Path("docker-compose.yml").exists()
    assert Path("alembic/versions/0001_initial.py").exists()


def test_core_config_imports_when_dependencies_are_available():
    pytest.importorskip("pydantic")
    pytest.importorskip("pydantic_settings")

    import app.core.config

    assert app.core.config.get_settings().app_env


def test_runtime_imports_when_dependencies_are_available():
    pytest.importorskip("aiogram")
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("redis")
    pytest.importorskip("openai")
    pytest.importorskip("httpx")

    import app.bot.handlers
    import app.models
    import app.web.main

    assert app.bot.handlers.router is not None
    assert app.models.Base is not None
    assert app.web.main.app is not None
