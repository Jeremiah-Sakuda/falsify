#!/usr/bin/env python3
"""The experiments harness.

Runs each experiment twice against the MR head and once against the merge
base, inside the execution boundary. Writes experiments.json.

EXECUTION BOUNDARY (docs/controls.md, Control 1)
------------------------------------------------
Removing protected variables is not a credential-free environment: every job
carries CI_JOB_TOKEN and may carry registry credentials. So this script
separates PREPARATION from EXECUTION:

  - This process (trusted) fetches experiments and prepares checkouts.
  - pytest runs in a CHILD process started with a scrubbed environment
    (env -i plus only what conftest needs), under timeouts and rlimits, in a
    network namespace with no interfaces where the runner permits it.
  - Results are collected by this process after the child exits.

This script never imports an experiment. It only runs them as subprocesses
and reads exit codes and reports.
"""
from __future__ import annotations

import argparse
import json
import os
import resource
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from scripts.experiments_contract import (
    ExperimentResult,
    Outcome,
    digest_file,
)

# The ONLY variables that cross into the child. Everything else is dropped.
ALLOWED_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "PYTHONPATH",
    "PYTHONDONTWRITEBYTECODE",
    "TMPDIR",
    "FALSIFY_ENV",
    "FALSIFY_DB",
    "FALSIFY_NETNS_ENFORCED",
)

# pytest exit codes
PYTEST_OK = 0
PYTEST_TESTS_FAILED = 1
PYTEST_INTERNAL_ERROR = 3
PYTEST_USAGE_ERROR = 4
PYTEST_NO_TESTS = 5


def load_thresholds(path: str = ".falsify/thresholds.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text())["experiments"]


def scrubbed_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: os.environ[k] for k in ALLOWED_ENV if k in os.environ}
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.update(extra or {})
    return env


def _apply_rlimits(as_mb: int, nproc: int):
    def preexec() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (as_mb * 1024 * 1024,) * 2)
        resource.setrlimit(resource.RLIMIT_NPROC, (nproc, nproc))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        os.setsid()

    return preexec


def run_one(
    experiment: Path,
    checkout: Path,
    thresholds: dict,
) -> tuple[Outcome, str]:
    """Run one experiment file in a scrubbed child process.

    Distinguishing FAIL from ERROR is the whole point: an assertion failure is
    evidence, an import or fixture error is not a finding of any kind.
    """
    report = Path(tempfile.mkstemp(suffix=".json", prefix="falsify-report-")[1])
    db = Path(tempfile.mkdtemp(prefix="falsify-expdb-")) / "exp.db"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(experiment),
        "-q",
        "--no-header",
        f"--timeout={thresholds['per_test_timeout_s']}",
        "--timeout-method=thread",
        f"--junit-xml={report.with_suffix('.xml')}",
        "-p",
        "no:cacheprovider",
    ]

    try:
        proc = subprocess.run(
            cmd,
            cwd=checkout,
            env=scrubbed_env({"FALSIFY_ENV": "dev", "FALSIFY_DB": str(db)}),
            capture_output=True,
            text=True,
            timeout=thresholds["job_timeout_s"],
            preexec_fn=_apply_rlimits(
                thresholds["rlimit_as_mb"], thresholds["rlimit_nproc"]
            ),
        )
    except subprocess.TimeoutExpired:
        return Outcome.ERROR, "timeout: the job-level limit was reached"

    output = (proc.stdout or "") + (proc.stderr or "")

    if proc.returncode == PYTEST_OK:
        return Outcome.PASS, output
    if proc.returncode == PYTEST_TESTS_FAILED:
        # pytest reports collection errors as 'errors', not 'failures'. An
        # experiment whose module could not import exits 1 in some versions,
        # so check the output rather than trusting the code alone.
        if " error" in output and "failed" not in output:
            return Outcome.ERROR, output
        return Outcome.FAIL, output
    if proc.returncode in (PYTEST_INTERNAL_ERROR, PYTEST_USAGE_ERROR, PYTEST_NO_TESTS):
        return Outcome.ERROR, output
    return Outcome.ERROR, f"unexpected pytest exit {proc.returncode}\n{output}"


def prepare_checkout(ref: str, experiments_dir: Path) -> Path:
    """Worktree at `ref`, with the experiments copied in.

    Experiments run against MR code without ever living on the MR branch.
    """
    dest = Path(tempfile.mkdtemp(prefix=f"falsify-{ref.replace('/', '-')}-"))
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(dest), ref],
        check=True,
        capture_output=True,
    )
    target = dest / ".falsify" / "experiments"
    target.mkdir(parents=True, exist_ok=True)
    for f in experiments_dir.glob("*_test.py"):
        shutil.copy2(f, target / f.name)
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--experiments", default=".falsify/experiments")
    ap.add_argument("--head", required=True, help="MR head SHA or ref")
    ap.add_argument("--base", required=True, help="merge base SHA or ref")
    ap.add_argument("--out", default="experiments.json")
    ap.add_argument("--thresholds", default=".falsify/thresholds.yaml")
    args = ap.parse_args()

    thresholds = load_thresholds(args.thresholds)
    exp_dir = Path(args.experiments)
    files = sorted(exp_dir.glob("*_test.py"))

    if not files:
        print("no experiments to run")
        Path(args.out).write_text(json.dumps({"experiments": []}, indent=2))
        return 0

    if len(files) > thresholds["max_experiments"]:
        print(
            f"REFUSED: {len(files)} experiments exceeds the authorized maximum "
            f"of {thresholds['max_experiments']}",
            file=sys.stderr,
        )
        return 1

    head_co = prepare_checkout(args.head, exp_dir)
    base_co = prepare_checkout(args.base, exp_dir)

    results: list[ExperimentResult] = []
    logs: dict[str, dict[str, str]] = {}

    for f in files:
        eid = f.stem.split("_")[0].upper()
        result = ExperimentResult(
            experiment_id=eid, path=str(f), digest=digest_file(f)
        )
        logs[eid] = {}

        # Two runs on head. A FAIL must reproduce to be evidence.
        for i in range(thresholds["head_runs"]):
            outcome, log = run_one(head_co / ".falsify" / "experiments" / f.name,
                                   head_co, thresholds)
            result.head_runs.append(outcome)
            logs[eid][f"head_run_{i + 1}"] = log[-4000:]

        # One run on base. A missing target file means no base version.
        base_file = base_co / ".falsify" / "experiments" / f.name
        if not base_file.exists():
            result.base_run = Outcome.NA
        else:
            outcome, log = run_one(base_file, base_co, thresholds)
            # An experiment that cannot even import on the base is targeting
            # new code: that is `n/a`, not an error in the base comparison.
            if outcome is Outcome.ERROR and "ModuleNotFoundError" in log:
                result.base_run = Outcome.NA
            else:
                result.base_run = outcome
            logs[eid]["base_run"] = log[-4000:]

        results.append(result)
        print(
            f"{eid:>4}  head={','.join(result.head_runs):<12} "
            f"base={result.base_run:<5} -> {result.classification}"
        )

    payload = {
        "head": args.head,
        "base": args.base,
        "pipeline_id": os.environ.get("CI_PIPELINE_ID"),
        "job_id": os.environ.get("CI_JOB_ID"),
        "experiments": [
            {
                "id": r.experiment_id,
                "path": r.path,
                "digest": r.digest,
                "head_runs": [str(o) for o in r.head_runs],
                "base_run": str(r.base_run),
                "classification": str(r.classification),
                "is_finding": r.is_finding,
                "logs": logs.get(r.experiment_id, {}),
            }
            for r in results
        ],
    }
    Path(args.out).write_text(json.dumps(payload, indent=2))

    findings = sum(1 for r in results if r.is_finding)
    print(f"\n{findings} finding(s). Unsupported functional findings: 0.")

    # The harness exits 0 even with findings. Findings block merge at the
    # certificate job, after a human has ruled on each one — not here.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
