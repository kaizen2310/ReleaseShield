"""
Unit tests for ApprovalService.
Tests key normalization, default PENDING state, and round-trip approval.
STRICT RULE: No source file is modified.
"""
import pytest
from app.services.approval_service import ApprovalService, _IN_MEMORY_APPROVALS
from app.schemas.unified_risk import ApprovalStatus


def _clear_key(repo: str, release: str):
    """Helper to clear in-memory store for a given key."""
    key = ApprovalService._key(repo, release)
    if key in _IN_MEMORY_APPROVALS:
        del _IN_MEMORY_APPROVALS[key]


class TestApprovalService:

    def setup_method(self):
        """Clear any state before each test."""
        _IN_MEMORY_APPROVALS.clear()

    def test_get_new_release_pending(self):
        result = ApprovalService.get_approval("owner/repo", "v1.0.0")
        assert result.status == ApprovalStatus.PENDING_APPROVAL
        assert result.deployment_blocked is True

    def test_key_normalization_strips_whitespace(self):
        k1 = ApprovalService._key("  owner/repo  ", "v1.0.0")
        k2 = ApprovalService._key("owner/repo", "v1.0.0")
        assert k1 == k2

    def test_key_normalization_lowercases(self):
        k1 = ApprovalService._key("Owner/Repo", "V1.0.0")
        k2 = ApprovalService._key("owner/repo", "v1.0.0")
        assert k1 == k2

    def test_submit_approved_deployment_unblocked(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v1.0.0",
            ApprovalStatus.APPROVED,
            "Alice", "Release Manager", "LGTM"
        )
        assert result.status == ApprovalStatus.APPROVED
        assert result.deployment_blocked is False

    def test_submit_rejected_deployment_still_blocked(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v1.0.0",
            ApprovalStatus.REJECTED,
            "Bob", "Tech Lead", "Security concerns"
        )
        assert result.status == ApprovalStatus.REJECTED
        assert result.deployment_blocked is True

    def test_round_trip_get_after_submit(self):
        ApprovalService.submit_approval(
            "owner/repo", "v2.0.0",
            ApprovalStatus.APPROVED,
            "Carol", "Engineering Manager", "Approved after review"
        )
        result = ApprovalService.get_approval("owner/repo", "v2.0.0")
        assert result.status == ApprovalStatus.APPROVED
        assert result.deployment_blocked is False
        assert result.approver_name == "Carol"

    def test_submit_stores_approver_name(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v3.0.0",
            ApprovalStatus.APPROVED,
            "Dave", "VP Engineering", ""
        )
        assert result.approver_name == "Dave"

    def test_submit_stores_approver_role(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v4.0.0",
            ApprovalStatus.APPROVED,
            "Eve", "Release Manager", ""
        )
        assert result.approver_role == "Release Manager"

    def test_submit_stores_notes(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v5.0.0",
            ApprovalStatus.REJECTED,
            "Frank", "QA Lead", "Critical tests failing"
        )
        assert result.notes == "Critical tests failing"

    def test_submit_returns_timestamp(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v6.0.0",
            ApprovalStatus.APPROVED,
            "Grace", "CTO", ""
        )
        assert result.timestamp is not None

    def test_changes_requested_deployment_blocked(self):
        result = ApprovalService.submit_approval(
            "owner/repo", "v7.0.0",
            ApprovalStatus.CHANGES_REQUESTED,
            "Henry", "Tech Lead", "Minor changes required"
        )
        assert result.status == ApprovalStatus.CHANGES_REQUESTED
        assert result.deployment_blocked is True

    def test_different_repos_isolated(self):
        ApprovalService.submit_approval(
            "repo-a", "v1.0", ApprovalStatus.APPROVED, "A", "Manager", ""
        )
        ApprovalService.submit_approval(
            "repo-b", "v1.0", ApprovalStatus.REJECTED, "B", "Lead", ""
        )
        a = ApprovalService.get_approval("repo-a", "v1.0")
        b = ApprovalService.get_approval("repo-b", "v1.0")
        assert a.status == ApprovalStatus.APPROVED
        assert b.status == ApprovalStatus.REJECTED

    def test_approval_status_enum_values(self):
        assert ApprovalStatus.PENDING_APPROVAL == "PENDING_APPROVAL"
        assert ApprovalStatus.APPROVED == "APPROVED"
        assert ApprovalStatus.REJECTED == "REJECTED"
        assert ApprovalStatus.CHANGES_REQUESTED == "CHANGES_REQUESTED"
