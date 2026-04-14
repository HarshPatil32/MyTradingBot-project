"""Tests for env var validation (validate_env_vars + health check endpoint)."""
import pytest
from unittest.mock import patch


class TestValidateEnvVarsShape:
    def test_returns_expected_keys(self):
        from app import validate_env_vars
        result = validate_env_vars()
        assert set(result.keys()) == {"missing_required", "missing_optional", "all_present"}

    def test_missing_required_is_list(self):
        from app import validate_env_vars
        result = validate_env_vars()
        assert isinstance(result["missing_required"], list)

    def test_all_present_is_bool(self):
        from app import validate_env_vars
        result = validate_env_vars()
        assert isinstance(result["all_present"], bool)


class TestValidateEnvVarsLogic:
    def test_all_present_true_when_no_required_vars_missing(self, monkeypatch):
        # All current manifest vars are optional, so all_present should always be True
        from app import validate_env_vars
        result = validate_env_vars()
        assert result["all_present"] is True
        assert result["missing_required"] == []

    def test_optional_var_reported_when_unset(self, monkeypatch):
        monkeypatch.delenv("PORT", raising=False)
        monkeypatch.delenv("FLASK_DEBUG", raising=False)
        from app import validate_env_vars
        result = validate_env_vars()
        assert "PORT" in result["missing_optional"]

    def test_optional_var_not_reported_when_set(self, monkeypatch):
        monkeypatch.setenv("PORT", "5001")
        from app import validate_env_vars
        result = validate_env_vars()
        assert "PORT" not in result["missing_optional"]

    def test_required_var_triggers_all_present_false(self, monkeypatch):
        # Temporarily inject a required var into the manifest to test the path
        import app as app_module
        original = app_module._ENV_VAR_MANIFEST
        app_module._ENV_VAR_MANIFEST = (
            {"name": "FAKE_REQUIRED_VAR", "required": True, "description": "test only"},
        )
        monkeypatch.delenv("FAKE_REQUIRED_VAR", raising=False)
        try:
            result = app_module.validate_env_vars()
            assert result["all_present"] is False
            assert "FAKE_REQUIRED_VAR" in result["missing_required"]
        finally:
            app_module._ENV_VAR_MANIFEST = original

    def test_no_secret_values_in_log_output(self, monkeypatch, caplog):
        monkeypatch.setenv("PORT", "supersecret")
        import logging
        from app import validate_env_vars
        with caplog.at_level(logging.INFO):
            validate_env_vars()
        for record in caplog.records:
            assert "supersecret" not in record.message


class TestHealthCheckEnvStatus:
    @pytest.fixture(scope="class")
    def client(self):
        from app import app as flask_app
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            yield c

    def test_env_status_present_in_response(self, client):
        resp = client.get("/")
        data = resp.get_json()
        assert "env_status" in data

    def test_env_status_has_all_present_field(self, client):
        resp = client.get("/")
        data = resp.get_json()
        assert "all_present" in data["env_status"]

    def test_env_status_has_missing_required_field(self, client):
        resp = client.get("/")
        data = resp.get_json()
        assert "missing_required" in data["env_status"]

    def test_missing_required_is_list(self, client):
        resp = client.get("/")
        data = resp.get_json()
        assert isinstance(data["env_status"]["missing_required"], list)
