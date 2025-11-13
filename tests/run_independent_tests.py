#!/usr/bin/env python3
"""
Run each test case independently to avoid one crash affecting others.
Each test runs 5 times to measure variance.
"""

import json
import subprocess
import sys
from pathlib import Path

# Load test cases
test_cases_path = Path(__file__).parent / "test_cases_refactored.json"
with open(test_cases_path) as f:
    test_cases = json.load(f)

# Configuration
NUM_RUNS = 5
OUTPUT_DIR = Path(__file__).parent.parent
BASE_CMD = [
    "python", str(Path(__file__).parent / "test_conversational_layer.py"),
    "--suite", "assistant",
    "--mode", "real",
    "--test-cases", "refactored",
    "--clean-graph-between-tests",
    "--interrogate-all"
]

print(f"Running {len(test_cases)} tests × {NUM_RUNS} runs = {len(test_cases) * NUM_RUNS} total executions")
print("Each test is fully independent - crashes won't affect other tests")
print()

for test_idx, test_case in enumerate(test_cases, 1):
    test_name = test_case["name"]
    print(f"[{test_idx}/{len(test_cases)}] Running test: {test_name}")

    for run in range(1, NUM_RUNS + 1):
        output_file = OUTPUT_DIR / f"independent_{test_name}_run{run}.json"
        stdout_file = OUTPUT_DIR / f"independent_{test_name}_run{run}.stdout"
        stderr_file = OUTPUT_DIR / f"independent_{test_name}_run{run}.stderr"
        status_file = OUTPUT_DIR / f"independent_{test_name}_run{run}.status"

        # Build command for this specific test
        cmd = BASE_CMD + [
            "--test-name", test_name,
            "--interrogation-log", str(output_file)
        ]

        import datetime
        start_time = datetime.datetime.now()
        status_info = {
            "test": test_name,
            "run": run,
            "start_time": start_time.isoformat(),
            "command": " ".join(str(c) for c in cmd)
        }

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout per test
                cwd=Path(__file__).parent
            )

            end_time = datetime.datetime.now()
            status_info["end_time"] = end_time.isoformat()
            status_info["duration_seconds"] = (end_time - start_time).total_seconds()
            status_info["exit_code"] = result.returncode
            status_info["status"] = "PASS" if result.returncode == 0 else "FAIL"

            # Write stdout and stderr
            stdout_file.write_text(result.stdout, encoding='utf-8')
            stderr_file.write_text(result.stderr, encoding='utf-8')

            if result.returncode == 0:
                print(f"  Run {run}: ✓ PASS ({status_info['duration_seconds']:.1f}s)")
            else:
                print(f"  Run {run}: ✗ FAIL (exit {result.returncode}, {status_info['duration_seconds']:.1f}s)")
                if result.stderr:
                    print(f"    stderr: {result.stderr[:200]}")

        except subprocess.TimeoutExpired as timeout:
            end_time = datetime.datetime.now()
            status_info["end_time"] = end_time.isoformat()
            status_info["duration_seconds"] = (end_time - start_time).total_seconds()
            status_info["status"] = "TIMEOUT"
            status_info["timeout_seconds"] = 600

            # Save partial output from timeout
            if timeout.stdout:
                stdout_file.write_text(timeout.stdout, encoding='utf-8')
            if timeout.stderr:
                stderr_file.write_text(timeout.stderr, encoding='utf-8')

            print(f"  Run {run}: ⏱ TIMEOUT (after {status_info['duration_seconds']:.1f}s)")
            if timeout.stderr:
                print(f"    stderr: {timeout.stderr[:200]}")

        except Exception as e:
            import traceback
            end_time = datetime.datetime.now()
            status_info["end_time"] = end_time.isoformat()
            status_info["duration_seconds"] = (end_time - start_time).total_seconds()
            status_info["status"] = "ERROR"
            status_info["error"] = str(e)
            status_info["traceback"] = traceback.format_exc()

            # Write error details
            stderr_file.write_text(status_info["traceback"], encoding='utf-8')

            print(f"  Run {run}: ⚠ ERROR: {e}")
            print(f"    {traceback.format_exc()[:200]}")

        finally:
            # Always write status file
            status_file.write_text(json.dumps(status_info, indent=2), encoding='utf-8')

    print()

print("Done! Check independent_*.json files for results")
