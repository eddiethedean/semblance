"""Tests for Phase 4: CLI, export, plugins."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from semblance import SemblanceAPI
from semblance.cli import (
    _load_app,
    cmd_export_fixtures,
    cmd_export_openapi,
    cmd_run,
    main,
)
from tests.example_models import User, UserQuery


class TestLoadApp:
    def test_load_semblance_api(self):
        app = _load_app("tests.sample_app:api")

        assert hasattr(app, "openapi")

    def test_load_fastapi_app(self):
        app = _load_app("tests.sample_app:app")
        from fastapi import FastAPI

        assert isinstance(app, FastAPI)

    def test_invalid_path_no_colon(self):
        with pytest.raises(SystemExit):
            _load_app("tests.sample_app")

    def test_invalid_module(self):
        with pytest.raises(SystemExit):
            _load_app("nonexistent_module:api")

    def test_invalid_attr(self):
        with pytest.raises(SystemExit):
            _load_app("tests.sample_app:nonexistent")

    def test_empty_module_or_attr(self):
        with pytest.raises(SystemExit):
            _load_app(":api")
        with pytest.raises(SystemExit):
            _load_app("tests.sample_app:")


class TestExportOpenAPI:
    def test_export_stdout(self, capsys):
        args = type(
            "Args",
            (),
            {"app": "tests.sample_app:app", "output": None, "include_examples": False},
        )()
        cmd_export_openapi(args)
        out, _ = capsys.readouterr()
        schema = json.loads(out)
        assert "openapi" in schema
        assert "paths" in schema
        assert "/users" in schema["paths"]

    def test_export_to_file(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            args = type(
                "Args",
                (),
                {
                    "app": "tests.sample_app:app",
                    "output": path,
                    "include_examples": False,
                },
            )()
            cmd_export_openapi(args)
            schema = json.load(open(path))
            assert "/users" in schema["paths"]
        finally:
            Path(path).unlink(missing_ok=True)


class TestExportFixtures:
    def test_export_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = type("Args", (), {"app": "tests.sample_app:app", "output": tmp})()
            cmd_export_fixtures(args)
            out_file = Path(tmp) / "openapi.json"
            assert out_file.exists()
            schema = json.loads(out_file.read_text())
            assert "paths" in schema
            # Per-endpoint fixtures
            users_get = Path(tmp) / "users_GET.json"
            assert users_get.exists()
            data = json.loads(users_get.read_text())
            assert isinstance(data, list)


class TestOpenAPIAnnotations:
    def test_summary_description_tags_in_openapi(self):
        api = SemblanceAPI()
        api.get(
            "/users",
            input=UserQuery,
            output=list[User],
            summary="List users",
            description="Returns users matching query",
            tags=["users"],
        )(lambda: None)
        app = api.as_fastapi()
        schema = app.openapi()
        get_op = schema["paths"]["/users"]["get"]
        assert get_op.get("summary") == "List users"
        assert get_op.get("description") == "Returns users matching query"
        assert get_op.get("tags") == ["users"]


class TestExportOpenAPIWithExamples:
    def test_export_openapi_include_examples_populates_response_examples(self):
        """export_openapi with include_examples=True adds example to schema."""
        from semblance.export import export_openapi

        app = _load_app("tests.sample_app:app")
        schema = export_openapi(app, include_examples=True)
        get_op = schema["paths"]["/users"]["get"]
        responses = get_op.get("responses", {})
        content = responses.get("200", {}).get("content", {})
        json_content = content.get("application/json", {})
        assert "example" in json_content
        example = json_content["example"]
        assert isinstance(example, list)
        assert len(example) >= 1


class TestExportFixturesWithPost:
    def test_export_fixtures_includes_post_endpoint(self):
        """export_fixtures generates fixture for POST endpoints when they succeed."""
        from typing import Annotated

        from pydantic import BaseModel

        from semblance import FromInput, SemblanceAPI
        from semblance.export import export_fixtures

        class CreateReq(BaseModel):
            name: str = "fixture"

        class Item(BaseModel):
            name: Annotated[str, FromInput("name")]

        api = SemblanceAPI()
        api.post("/items", input=CreateReq, output=Item)(lambda: None)
        app = api.as_fastapi()

        with tempfile.TemporaryDirectory() as tmp:
            export_fixtures(app, tmp)
            post_file = Path(tmp) / "items_POST.json"
            assert post_file.exists()
            data = json.loads(post_file.read_text())
            assert data["name"] == "fixture"


class TestCmdRun:
    def test_cmd_run_without_reload_mocks_uvicorn(self):
        """cmd_run without reload loads app and calls uvicorn.run."""
        args = type(
            "Args",
            (),
            {
                "app": "tests.sample_app:app",
                "host": "127.0.0.1",
                "port": 8000,
                "reload": False,
            },
        )()
        with patch("uvicorn.run") as mock_run:
            cmd_run(args)
            mock_run.assert_called_once()
            call_kw = mock_run.call_args[1]
            assert call_kw["host"] == "127.0.0.1"
            assert call_kw["port"] == 8000

    def test_cmd_run_with_reload_calls_uvicorn_with_reload(self):
        """cmd_run with reload loads app and calls uvicorn.run with reload=True."""
        args = type(
            "Args",
            (),
            {
                "app": "tests.sample_app:app",
                "host": "127.0.0.1",
                "port": 8000,
                "reload": True,
            },
        )()
        with patch("uvicorn.run") as mock_run:
            cmd_run(args)
            mock_run.assert_called_once()
            call_kw = mock_run.call_args[1]
            assert call_kw["host"] == "127.0.0.1"
            assert call_kw["port"] == 8000
            assert call_kw["reload"] is True

    def test_cmd_run_uvicorn_not_found_exits(self):
        """cmd_run raises SystemExit when uvicorn import fails."""
        args = type(
            "Args",
            (),
            {
                "app": "tests.sample_app:app",
                "host": "127.0.0.1",
                "port": 8000,
                "reload": False,
            },
        )()
        import builtins

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "uvicorn":
                raise ImportError("No module named 'uvicorn'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", fake_import):
            with pytest.raises(SystemExit, match="uvicorn not found"):
                cmd_run(args)


class TestCmdExportNonFastAPI:
    def test_cmd_export_openapi_raises_when_app_not_fastapi(self):
        """cmd_export_openapi raises SystemExit when loaded app is not FastAPI."""
        args = type(
            "Args",
            (),
            {
                "app": "tests.cli_test_module:not_fastapi",
                "output": None,
                "include_examples": False,
            },
        )()
        with pytest.raises(SystemExit, match="App must be a FastAPI instance"):
            cmd_export_openapi(args)

    def test_cmd_export_fixtures_raises_when_app_not_fastapi(self):
        """cmd_export_fixtures raises SystemExit when loaded app is not FastAPI."""
        args = type(
            "Args",
            (),
            {"app": "tests.cli_test_module:not_fastapi", "output": "fixtures"},
        )()
        with pytest.raises(SystemExit, match="App must be a FastAPI instance"):
            cmd_export_fixtures(args)


class TestMain:
    def test_main_export_openapi_via_argv(self, capsys):
        """main() with export openapi args dispatches to cmd_export_openapi."""
        with patch.object(
            sys, "argv", ["semblance", "export", "openapi", "tests.sample_app:app"]
        ):
            main()
        out, _ = capsys.readouterr()
        schema = json.loads(out)
        assert "openapi" in schema
        assert "/users" in schema["paths"]

    def test_main_export_fixtures_via_argv(self, tmp_path):
        """main() with export fixtures args dispatches to cmd_export_fixtures."""
        with patch.object(
            sys,
            "argv",
            [
                "semblance",
                "export",
                "fixtures",
                "tests.sample_app:app",
                "-o",
                str(tmp_path),
            ],
        ):
            main()
        assert (tmp_path / "openapi.json").exists()
        assert (tmp_path / "users_GET.json").exists()

    def test_main_run_via_argv_mocks_uvicorn(self):
        """main() with run args dispatches to cmd_run."""
        with patch.object(
            sys,
            "argv",
            [
                "semblance",
                "run",
                "tests.sample_app:app",
                "--host",
                "0.0.0.0",
                "--port",
                "9999",
            ],
        ):
            with patch("uvicorn.run") as mock_run:
                main()
                mock_run.assert_called_once()
                assert mock_run.call_args[1]["host"] == "0.0.0.0"
                assert mock_run.call_args[1]["port"] == 9999

    def test_cli_module_main_entrypoint(self):
        """Running semblance.cli as __main__ invokes main()."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "semblance.cli",
                "export",
                "openapi",
                "tests.sample_app:app",
            ],
            capture_output=True,
            text=True,
            cwd=Path(__file__).resolve().parent.parent,
        )
        assert result.returncode == 0
        schema = json.loads(result.stdout)
        assert "openapi" in schema
        assert "/users" in schema["paths"]
