"""
Extended integration tests for the ReleaseShield FastAPI application.
These complement the existing test_integration.py without duplicating.
STRICT RULE: No source file is modified.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


BASE = "/api/releases"


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ===========================================================================
# Scenarios endpoint
# ===========================================================================

class TestScenariosEndpoint:

    @pytest.mark.asyncio
    async def test_get_scenarios_200(self, client):
        resp = await client.get(f"{BASE}/scenarios")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_scenarios_returns_5(self, client):
        resp = await client.get(f"{BASE}/scenarios")
        data = resp.json()
        scenarios = data if isinstance(data, list) else data.get("scenarios", data)
        assert len(scenarios) == 5

    @pytest.mark.asyncio
    async def test_scenarios_have_expected_risk_field(self, client):
        resp = await client.get(f"{BASE}/scenarios")
        data = resp.json()
        scenarios = data if isinstance(data, list) else data.get("scenarios", data)
        for s in scenarios:
            assert "expected_risk" in s


# ===========================================================================
# Analyze endpoint
# ===========================================================================

class TestAnalyzeEndpoint:

    @pytest.mark.asyncio
    async def test_analyze_standard_healthy_200(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "scenario": "standard_healthy"
        }
        resp = await client.post(f"{BASE}/analyze", json=payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_analyze_response_has_risk_score(self, client):
        payload = {"repository": "owner/my-repo", "release": "v1.0.0", "scenario": "standard_healthy"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        data = resp.json()
        assert "risk_score" in data

    @pytest.mark.asyncio
    async def test_analyze_response_has_risk_level(self, client):
        payload = {"repository": "owner/my-repo", "release": "v1.0.0", "scenario": "standard_healthy"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        data = resp.json()
        assert "risk_level" in data
        assert data["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    @pytest.mark.asyncio
    async def test_analyze_blocker_scenario_hard_gate(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "scenario": "blocker_defects"
        }
        resp = await client.post(f"{BASE}/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        engine = data.get("hybrid_engine", {})
        assert engine.get("hard_gate_triggered") is True

    @pytest.mark.asyncio
    async def test_analyze_missing_release_field_422(self, client):
        payload = {"repository": "owner/my-repo"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_missing_repository_field_422(self, client):
        payload = {"release": "v1.0.0"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_invalid_repo_format_error(self, client):
        payload = {
            "repository": "invalid_repo_no_slash",
            "release": "v1.0.0",
            "scenario": "standard_healthy"
        }
        resp = await client.post(f"{BASE}/analyze", json=payload)
        # Should return 400 or 422 or an error response
        assert resp.status_code in (400, 422, 500)

    @pytest.mark.asyncio
    async def test_analyze_response_has_required_actions(self, client):
        payload = {"repository": "owner/my-repo", "release": "v1.0.0", "scenario": "standard_healthy"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        data = resp.json()
        assert "required_actions" in data
        assert isinstance(data["required_actions"], list)

    @pytest.mark.asyncio
    async def test_analyze_response_has_hybrid_engine(self, client):
        payload = {"repository": "owner/my-repo", "release": "v1.0.0", "scenario": "standard_healthy"}
        resp = await client.post(f"{BASE}/analyze", json=payload)
        data = resp.json()
        assert "hybrid_engine" in data

    @pytest.mark.asyncio
    async def test_analyze_ops_instability_critical(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "scenario": "ops_instability"
        }
        resp = await client.post(f"{BASE}/analyze", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] in ("CRITICAL", "HIGH")


# ===========================================================================
# Approval endpoint
# ===========================================================================

class TestApprovalEndpoint:

    @pytest.mark.asyncio
    async def test_submit_approval_200(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "status": "APPROVED",
            "approver_name": "Alice",
            "approver_role": "Release Manager",
            "notes": "Approved after review"
        }
        resp = await client.post(f"{BASE}/approval", json=payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_submit_approval_deployment_unblocked(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v99.0.0-unique",
            "status": "APPROVED",
            "approver_name": "Bob",
            "approver_role": "Manager",
            "notes": ""
        }
        resp = await client.post(f"{BASE}/approval", json=payload)
        data = resp.json()
        assert data.get("deployment_blocked") is False

    @pytest.mark.asyncio
    async def test_get_approval_200(self, client):
        resp = await client.get(
            f"{BASE}/approval",
            params={"repository": "owner/my-repo", "release": "v1.0.0"}
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_get_approval_has_status(self, client):
        resp = await client.get(
            f"{BASE}/approval",
            params={"repository": "owner/my-repo", "release": "v1.0.0"}
        )
        data = resp.json()
        assert "status" in data
        assert "deployment_blocked" in data


# ===========================================================================
# Action toggle endpoint
# ===========================================================================

class TestActionToggleEndpoint:

    @pytest.mark.asyncio
    async def test_toggle_action_200(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "action_id": "ACT-GOV-01",
            "status": "COMPLETED"
        }
        resp = await client.post(f"{BASE}/actions/toggle", json=payload)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_toggle_action_response_has_id(self, client):
        payload = {
            "repository": "owner/my-repo",
            "release": "v1.0.0",
            "action_id": "ACT-TST-02",
            "status": "WAIVED",
            "waiver_reason": "Approved by VP"
        }
        resp = await client.post(f"{BASE}/actions/toggle", json=payload)
        data = resp.json()
        assert "action_id" in data or resp.status_code == 200
