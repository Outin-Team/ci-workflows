#!/usr/bin/env python3
"""Offline unit tests for generic ci_hub_client and embedded workflow sync."""

from __future__ import annotations

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import ci_hub_client as client  # noqa: E402
import sync_workflows_embed as embed  # noqa: E402


class TestHubClient(unittest.TestCase):
    def test_clean_commit_and_sha(self) -> None:
        self.assertEqual(client.normalize_sha_short("sha-ABCDEF123"), "abcdef1")
        self.assertEqual(
            client.clean_commit_message("Merge pull request #9 from org/fix\n\nFix retry timeout"),
            "Fix retry timeout",
        )

    def test_stage1_posts_to_ci_hub(self) -> None:
        calls: list[tuple[str, str, dict | None]] = []

        def fake_http(url, *, method="GET", headers=None, payload=None, timeout=30):
            calls.append((method, url, payload))
            if "/pulls" in url:
                return 200, [{"number": 4, "title": "Add healthcheck", "body": "Adds /healthz", "html_url": "https://example.com/pr/4", "user": {"login": "alice"}}]
            if "/compare/" in url:
                return 200, {
                    "html_url": "https://example.com/compare/1...2",
                    "commits": [{"sha": "1234567", "commit": {"message": "feat: healthcheck"}, "author": {"login": "alice"}}],
                    "files": [{"filename": "app/main.py", "status": "modified", "additions": 10, "deletions": 2, "patch": "+ok"}],
                }
            if url.endswith("/api/v1/stage1"):
                return 200, {"ok": True, "coolify_ok": True, "state": "pending_approval"}
            return 404, {}

        rc = client.run_stage1(
            {
                "REPO_NAME": "demo-org/demo-app",
                "GITHUB_SHA": "1234567890abcdef1234567890abcdef12345678",
                "BEFORE_SHA": "0000000111111111111111111111111111111111",
                "EVENT_NAME": "push",
                "ACTOR": "alice",
                "REF_NAME": "main",
                "RUN_URL": "https://github.com/demo-org/demo-app/actions/runs/1",
                "GITHUB_TOKEN": "ghs_test",
                "CI_HUB_URL": "https://hub.example.test/_ci_hub",
                "CI_HUB_TOKEN": "tok",
                "COOLIFY_SERVICE_UUID": "svc-uuid-1",
                "JOB_STATUS": "success",
                "AUTO_DEPLOYED": "false",
                "REQUIRE_APPROVAL": "true",
            },
            http_fn=fake_http,
        )
        self.assertEqual(rc, 0)
        hub_call = [c for c in calls if c[1].endswith("/api/v1/stage1")][0]
        self.assertEqual(hub_call[2]["coolify_service_uuid"], "svc-uuid-1")
        self.assertEqual(hub_call[2]["change_context"]["pr_label"], "#4 Add healthcheck")

    def test_stage2_returns_nonzero_when_coolify_fails(self) -> None:
        def fake_http(url, *, method="GET", headers=None, payload=None, timeout=30):
            return 200, {"ok": False, "coolify_ok": False, "state": "deploy_failed"}

        rc = client.run_stage2(
            {
                "REPO_NAME": "demo-org/demo-app",
                "TARGET_SHA": "1234567",
                "APPROVER": "reviewer",
                "TRIGGER_ACTOR": "alice",
                "CARD_MESSAGE_ID": "om_1",
                "SUMMARY_TEXT": "- summary",
                "DIFF_URL": "https://example.com/diff",
                "RUN_URL": "https://example.com/run/2",
                "CI_HUB_URL": "https://hub.example.test",
                "CI_HUB_TOKEN": "tok",
                "COOLIFY_SERVICE_UUID": "svc-uuid-1",
                "JOB_STATUS": "success",
            },
            http_fn=fake_http,
        )
        self.assertEqual(rc, 1)

    def test_embedded_scripts_in_sync(self) -> None:
        source = embed.LIB_PATH.read_text(encoding="utf-8")
        for wf in embed.WORKFLOWS:
            self.assertTrue(embed.sync_file(wf, source, check_only=True))


if __name__ == "__main__":
    unittest.main()
