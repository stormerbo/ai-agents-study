"""Release-candidate manifest contracts; no Docker or provider calls."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from threading import Event
import unittest
from unittest.mock import patch

P5 = Path(__file__).resolve().parents[1]
P4 = P5.parent / "p4-durable-support"
for path in (P4.parent, P4, P5):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import release_candidate
from canonicalization import HASH_PROFILE


class ReleaseCandidateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self._write_minimal_materials()
        self._git("init", "-q")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "Test")
        self._git("add", ".")
        self._git("commit", "-qm", "candidate snapshot")
        self.commit = self._git("rev-parse", "HEAD").stdout.strip()

    def tearDown(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.run(
            ["git", *args], cwd=self.root, check=True, capture_output=True, text=True
        )

    def _write_minimal_materials(self):
        for relative in (
            "examples/p4-durable-support/app/__init__.py",
            "examples/p4-durable-support/migrations/0001_init.sql",
            "examples/p4-durable-support/tests/test_placeholder.py",
            *release_candidate.DOC_FILES,
        ):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"fixture: {relative}\n", encoding="utf-8")
        for relative in release_candidate.REQUIRED_FILES:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"pinned material: {relative}\n", encoding="utf-8")
        evaluation_root = self.root / "examples/p5-agent-delivery/evaluation"
        prompt_hash = hashlib.sha256((evaluation_root / "prompt.txt").read_bytes()).hexdigest()
        smoke_hash = hashlib.sha256((evaluation_root / "live-smoke.json").read_bytes()).hexdigest()
        (evaluation_root / "release.json").write_text(
            json.dumps({
                "release_id": "fixture-release",
                "hash_profile": HASH_PROFILE,
                "materials": {"prompt.txt": prompt_hash},
                "live_smoke": {"file": "live-smoke.json", "sha256": smoke_hash},
            }),
            encoding="utf-8",
        )

    def _drill_evidence(self):
        return [
            {"scenario_id": scenario, "run_id": f"run-{scenario}", "sha256": "a" * 64}
            for scenario in release_candidate.REQUIRED_DRILLS
        ]

    def test_builds_commit_bound_manifest_with_material_and_drill_hashes(self):
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self._drill_evidence()):
            manifest = release_candidate.build_release_candidate(
                self.root,
                image_digest="sha256:" + "b" * 64,
                evidence_root=self.root / "verify-output/stage5-drills",
            )

        self.assertEqual(manifest["commit_sha"], self.commit)
        self.assertEqual(manifest["image_digest"], "sha256:" + "b" * 64)
        self.assertEqual(manifest["evaluation_release_id"], "fixture-release")
        self.assertEqual(manifest["status"], "frozen-candidate")
        self.assertFalse(manifest["publishable"])
        self.assertEqual(len(manifest["drill_evidence"]), 6)
        expected_release_materials = (
            "examples/p4-durable-support/uv.lock",
            "examples/p5-agent-delivery/HANDOFF-RECORD.template.json",
            "examples/p5-agent-delivery/HANDOFF-RECORD.schema.json",
            "examples/p5-agent-delivery/evaluation/prompt.txt",
            "examples/p5-agent-delivery/evaluation/tool-schema.json",
            "examples/p5-agent-delivery/evaluation/dev.json",
            "examples/p5-agent-delivery/evaluation/holdout.json",
            "examples/p5-agent-delivery/evaluation/scorer.json",
            "examples/p5-agent-delivery/evaluation/scorer.py",
            "examples/p5-agent-delivery/evaluation/test_evaluation.py",
            "examples/p5-agent-delivery/evaluation/README.md",
            *release_candidate.DOC_FILES,
        )
        for relative in expected_release_materials:
            with self.subTest(material=relative):
                self.assertIn(relative, manifest["materials"])
                self.assertRegex(manifest["materials"][relative], r"^[0-9a-f]{64}$")
        self.assertEqual(len(manifest["candidate_hash"]), 64)
        self.assertEqual(
            release_candidate.canonical_hash(release_candidate.without_candidate_hash(manifest)),
            manifest["candidate_hash"],
        )

    def test_refuses_dirty_worktree_before_freezing(self):
        (self.root / "examples/p5-agent-delivery/runner.py").write_text("changed\n", encoding="utf-8")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self._drill_evidence()):
            with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "clean worktree"):
                release_candidate.build_release_candidate(
                    self.root,
                    image_digest="sha256:" + "b" * 64,
                    evidence_root=self.root / "verify-output/stage5-drills",
                )

    def test_rejects_mutable_or_malformed_image_reference(self):
        with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "immutable sha256 digest"):
            release_candidate.build_release_candidate(
                self.root,
                image_digest="latest",
                evidence_root=self.root / "verify-output/stage5-drills",
            )

    def test_rejects_changed_frozen_evaluation_material(self):
        prompt = self.root / "examples/p5-agent-delivery/evaluation/prompt.txt"
        prompt.write_text("mutated after evaluation freeze\n", encoding="utf-8")
        self._git("add", ".")
        self._git("commit", "-qm", "mutated evaluation")
        with patch.object(release_candidate, "_collect_drill_evidence", return_value=self._drill_evidence()):
            with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "frozen evaluation material"):
                release_candidate.build_release_candidate(
                    self.root,
                    image_digest="sha256:" + "b" * 64,
                    evidence_root=self.root / "verify-output/stage5-drills",
                )

    def test_rejects_changed_predeclared_live_smoke_case(self):
        smoke = self.root / "examples/p5-agent-delivery/evaluation/live-smoke.json"
        smoke.write_text('{"case_id":"tampered"}\n', encoding="utf-8")

        with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "smoke case hash mismatch"):
            release_candidate._frozen_evaluation(self.root.resolve())

    def test_drill_collection_rejects_reports_from_dirty_worktrees(self):
        evidence_root = self.root / "verify-output/stage5-drills/run-1/approval-pause-resume"
        evidence_root.mkdir(parents=True)
        (evidence_root / "report.json").write_text(json.dumps({
            "scenario_id": "approval-pause-resume",
            "run_id": "dirty-run",
            "finished_at_utc": "2026-10-20T00:00:00+00:00",
            "status": "passed",
            "materials": {"commit": self.commit, "worktree_clean": False},
        }), encoding="utf-8")
        with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "missing clean passing drill"):
            release_candidate._collect_drill_evidence(
                self.root, self.root / "verify-output/stage5-drills", self.commit
            )

    def test_drill_collection_rejects_malformed_or_timezone_free_timestamps(self):
        evidence_root = self.root / "verify-output/stage5-drills"
        for index, scenario in enumerate(release_candidate.REQUIRED_DRILLS):
            report_dir = evidence_root / f"run-{index}" / scenario
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(json.dumps({
                "scenario_id": scenario,
                "run_id": f"run-{index}",
                "finished_at_utc": "9999-not-a-date" if index == 0 else "2026-10-20T00:00:00",
                "status": "passed",
                "materials": {"commit": self.commit, "worktree_clean": True},
            }), encoding="utf-8")
        with patch("drill_report.evaluate_report", return_value={"status": "passed"}):
            with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "missing clean passing drill evidence: approval-pause-resume"):
                release_candidate._collect_drill_evidence(
                    self.root, evidence_root, self.commit
                )

    def test_drill_collection_binds_each_clean_same_commit_scenario(self):
        root = self.root.resolve()
        evidence_root = root / "verify-output/stage5-drills"
        for index, scenario in enumerate(release_candidate.REQUIRED_DRILLS):
            report_dir = evidence_root / f"run-{index}" / scenario
            report_dir.mkdir(parents=True)
            (report_dir / "report.json").write_text(json.dumps({
                "scenario_id": scenario,
                "run_id": f"run-{index}",
                "finished_at_utc": f"2026-10-20T00:00:0{index}+00:00",
                "status": "passed",
                "materials": {"commit": self.commit, "worktree_clean": True},
            }), encoding="utf-8")
        with patch("drill_report.evaluate_report", return_value={"status": "passed"}):
            selected = release_candidate._collect_drill_evidence(root, evidence_root, self.commit)

        self.assertEqual([item["scenario_id"] for item in selected], list(release_candidate.REQUIRED_DRILLS))
        self.assertTrue(all(len(item["report_sha256"]) == 64 for item in selected))
        self.assertTrue(all(item["run_id"] for item in selected))

    def test_candidate_manifest_is_append_only(self):
        output = self.root / "verify-output/stage5-release/candidate.json"
        manifest = {"schema": "test", "candidate_id": "p5-rc-test"}
        release_candidate.write_new_manifest(output, manifest)
        with self.assertRaisesRegex(release_candidate.ReleaseCandidateError, "already exists"):
            release_candidate.write_new_manifest(output, manifest)

    def test_candidate_manifest_is_invisible_until_fully_staged(self):
        output = self.root / "verify-output/stage5-release/candidate.json"
        manifest = {"schema": "test", "candidate_id": "p5-rc-test"}
        link_started = Event()
        allow_publish = Event()
        original_link = release_candidate.os.link

        def pause_before_publish(source, destination, *args, **kwargs):
            link_started.set()
            self.assertTrue(allow_publish.wait(timeout=5))
            return original_link(source, destination, *args, **kwargs)

        with patch.object(release_candidate.os, "link", side_effect=pause_before_publish):
            with ThreadPoolExecutor(max_workers=1) as executor:
                pending = executor.submit(release_candidate.write_new_manifest, output, manifest)
                reached_publish = link_started.wait(timeout=2)
                try:
                    self.assertTrue(reached_publish, "manifest should be staged before publication")
                    self.assertFalse(output.exists())
                finally:
                    allow_publish.set()
                pending.result(timeout=5)

        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), manifest)


if __name__ == "__main__":
    unittest.main()
