"""Tests that security headers are present on every Flask response."""
import pytest
from app import app, CSP_POLICY


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestCSPHeader:
    def test_present_on_root(self, client):
        resp = client.get("/")
        assert "Content-Security-Policy" in resp.headers

    def test_present_on_heartbeat(self, client):
        resp = client.get("/heartbeat")
        assert "Content-Security-Policy" in resp.headers

    def test_present_on_404(self, client):
        resp = client.get("/nonexistent-route-xyz")
        assert "Content-Security-Policy" in resp.headers

    def test_value_matches_policy_constant(self, client):
        resp = client.get("/heartbeat")
        assert resp.headers["Content-Security-Policy"] == CSP_POLICY

    def test_default_src_none(self, client):
        resp = client.get("/")
        assert "default-src 'none'" in resp.headers["Content-Security-Policy"]

    def test_frame_ancestors_none(self, client):
        resp = client.get("/")
        assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]

    def test_base_uri_self(self, client):
        resp = client.get("/")
        assert "base-uri 'self'" in resp.headers["Content-Security-Policy"]

    def test_csp_present_on_options_preflight(self, client):
        resp = client.options("/heartbeat")
        assert "Content-Security-Policy" in resp.headers
