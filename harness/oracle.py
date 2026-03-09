"""
Test oracle: evaluates agent outputs against task acceptance criteria.

The oracle runs two complementary checks:
1. Claims evaluation (claims-based partial credit rubric)
2. Test suite execution (automated pass/fail)
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from harness.models import Claim, ClaimResult, OracleResult, Task


class TaskOracle:
    """
    Evaluates a completed agent run against the task's oracle specification.

    Usage:
        oracle = TaskOracle(task, workspace_dir)
        result = oracle.evaluate()
    """

    def __init__(self, task: Task, workspace_dir: Path):
        self.task = task
        self.workspace_dir = workspace_dir

    def evaluate(self) -> OracleResult:
        """Run all oracle checks and return a complete OracleResult."""
        claim_results = self._evaluate_claims()
        test_pass_rate = self._run_test_suite()
        sas = self._run_static_analysis()
        rr = self._measure_regression_rate()

        return OracleResult(
            task_id=self.task.id,
            claims=claim_results,
            test_pass_rate=test_pass_rate,
            static_analysis_score=sas,
            regression_rate=rr,
        )

    def _evaluate_claims(self) -> list[ClaimResult]:
        """
        Evaluate each claim in the task's oracle spec.

        For automated claims: runs the test_command and checks exit code.
        For manual claims: returns a neutral 0.5 score (requires human review).
        """
        results = []

        for claim in self.task.oracle.claims:
            if claim.automated and claim.test_command:
                passed, evidence = self._run_claim_command(claim)
            else:
                # Non-automated claims require human review — marked pending
                passed = False
                evidence = "PENDING_HUMAN_REVIEW"

            results.append(ClaimResult(
                claim_id=claim.id,
                passed=passed,
                weight=claim.weight,
                evidence=evidence,
            ))

        return results

    def _run_claim_command(self, claim: Claim) -> tuple[bool, str]:
        """Run a single claim's test command, return (passed, evidence)."""
        try:
            result = subprocess.run(
                claim.test_command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            passed = result.returncode == 0
            evidence = (result.stdout + result.stderr)[:500]
            return passed, evidence
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT"
        except Exception as e:
            return False, f"ERROR: {e}"

    def _run_test_suite(self) -> float | None:
        """Run the task's test suite, return fraction of tests that passed."""
        if self.task.oracle.test_suite is None:
            return None

        ts = self.task.oracle.test_suite
        try:
            result = subprocess.run(
                ts.command,
                shell=True,
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=ts.timeout_seconds,
            )
            # Parse test runner output for pass/fail counts
            # This is a simplified parser — production implementation should
            # support pytest, jest, go test, etc. via separate parsers.
            return self._parse_test_output(result.stdout + result.stderr)
        except subprocess.TimeoutExpired:
            return 0.0
        except Exception:
            return None

    def _parse_test_output(self, output: str) -> float:
        """
        Parse test runner output to extract pass rate.

        Handles common formats:
        - pytest: "X passed, Y failed"
        - jest: "X tests passed, Y failed"
        - go test: "ok" / "FAIL"
        """
        import re

        # pytest style: "5 passed, 2 failed" or "5 passed"
        m = re.search(r"(\d+) passed(?:,\s*(\d+) failed)?", output)
        if m:
            passed = int(m.group(1))
            failed = int(m.group(2)) if m.group(2) else 0
            total = passed + failed
            return passed / total if total > 0 else 1.0

        # go test style
        if "ok" in output and "FAIL" not in output:
            return 1.0
        if "FAIL" in output:
            return 0.0

        return 0.5  # unknown format — neutral

    def _run_static_analysis(self) -> float | None:
        """
        Run ruff on all Python files in the workspace.
        Returns 1 - (new_violations / 100), clamped to [0, 1].
        """
        try:
            result = subprocess.run(
                ["ruff", "check", "--output-format=json", "."],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                timeout=60,
            )
            import json
            violations = json.loads(result.stdout) if result.stdout.strip() else []
            return max(0.0, 1.0 - len(violations) / 100)
        except FileNotFoundError:
            return None  # ruff not installed in sandbox
        except Exception:
            return None

    def _measure_regression_rate(self) -> float | None:
        """
        Measure the fraction of tests that were passing before agent changes
        and fail after. Requires a pre-run baseline snapshot.

        This is a placeholder — full implementation requires:
        1. Running the test suite on the base commit before agent runs
        2. Recording which tests passed
        3. Running again after agent changes
        4. Comparing which previously-passing tests now fail

        TODO: wire baseline snapshot from harness setup phase.
        """
        return None  # not yet implemented
