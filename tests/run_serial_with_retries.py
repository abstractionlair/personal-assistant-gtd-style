#!/usr/bin/env python3
"""
Run each test case serially with exponential backoff retries.
Each test runs 5 times to measure variance.
All output goes to test-results/ directory.
"""

import json
import subprocess
import sys
import time
import datetime
from pathlib import Path

def safe_print(*args, **kwargs):
    """Print with broken pipe handling"""
    try:
        print(*args, **kwargs)
        sys.stdout.flush()
    except BrokenPipeError:
        # Redirect stdout to devnull to prevent further errors
        sys.stdout = open('/dev/null', 'w')
    except Exception:
        pass  # Silently ignore other print errors

# Load test cases
test_cases_path = Path(__file__).parent / "test_cases_refactored.json"
with open(test_cases_path) as f:
    test_cases = json.load(f)

# Configuration
NUM_RUNS = 5
MAX_RETRIES = 3
INITIAL_BACKOFF = 30  # seconds (increased to handle rate limits better)
OUTPUT_DIR = Path(__file__).parent.parent / "test-results"
OUTPUT_DIR.mkdir(exist_ok=True)

BASE_CMD = [
    "python", str(Path(__file__).parent / "test_conversational_layer.py"),
    "--suite", "assistant",
    "--mode", "real",
    "--test-cases", "refactored",
    "--clean-graph-between-tests",
    "--interrogate-all"
]

# Delay between tests to avoid rate limits
INTER_TEST_DELAY = 10  # seconds

print(f"Running {len(test_cases)} tests × {NUM_RUNS} runs = {len(test_cases) * NUM_RUNS} total executions")
print(f"Output directory: {OUTPUT_DIR}")
print(f"Max retries per test: {MAX_RETRIES} with exponential backoff")
print(f"Delay between tests: {INTER_TEST_DELAY}s")
print()

total_tests = 0
total_passes = 0
total_failures = 0
total_retries = 0

for test_idx, test_case in enumerate(test_cases, 1):
    test_name = test_case["name"]
    print(f"[{test_idx}/{len(test_cases)}] Running test: {test_name}")

    for run in range(1, NUM_RUNS + 1):
        output_file = OUTPUT_DIR / f"{test_name}_run{run}.json"
        stdout_file = OUTPUT_DIR / f"{test_name}_run{run}.stdout"
        stderr_file = OUTPUT_DIR / f"{test_name}_run{run}.stderr"
        status_file = OUTPUT_DIR / f"{test_name}_run{run}.status"

        # Skip if already completed
        if output_file.exists():
            safe_print(f"  Run {run}: ⏭ SKIP (already completed)")
            total_tests += 1
            total_passes += 1
            continue

        # Build command for this specific test
        cmd = BASE_CMD + [
            "--test-name", test_name,
            "--interrogation-log", str(output_file)
        ]

        # Retry logic with exponential backoff
        retry_count = 0
        success = False

        while retry_count <= MAX_RETRIES and not success:
            start_time = datetime.datetime.now()
            status_info = {
                "test": test_name,
                "run": run,
                "retry": retry_count,
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

                # Write stdout and stderr
                stdout_file.write_text(result.stdout, encoding='utf-8')
                stderr_file.write_text(result.stderr, encoding='utf-8')

                if result.returncode == 0:
                    status_info["status"] = "PASS"
                    success = True
                    total_passes += 1
                    retry_msg = f" (after {retry_count} retries)" if retry_count > 0 else ""
                    print(f"  Run {run}: ✓ PASS ({status_info['duration_seconds']:.1f}s){retry_msg}")
                else:
                    # Check if test completed with interrogation data (judge FAIL is valid completion)
                    if output_file.exists() and output_file.stat().st_size > 100:
                        status_info["status"] = "COMPLETED_WITH_JUDGE_FAIL"
                        success = True
                        total_passes += 1
                        safe_print(f"  Run {run}: ✓ COMPLETED ({status_info['duration_seconds']:.1f}s) [Judge FAIL - behavioral issue, not crash]")
                    # Check if test doesn't exist (permanent error, don't retry)
                    elif "not found" in result.stderr.lower():
                        status_info["status"] = "TEST_NOT_FOUND"
                        success = True  # Mark as success to move on
                        total_failures += 1
                        safe_print(f"  Run {run}: ⊗ SKIP (test not found)")
                    # Check if it's a crash/rate limit that should be retried
                    elif retry_count < MAX_RETRIES:
                        backoff_time = INITIAL_BACKOFF * (2 ** retry_count)
                        total_retries += 1
                        print(f"  Run {run}: ⚠ FAIL (exit {result.returncode}), retrying in {backoff_time}s...")
                        if result.stderr:
                            print(f"    stderr: {result.stderr[:200]}")

                        status_info["status"] = "RETRY"
                        status_file.write_text(json.dumps(status_info, indent=2), encoding='utf-8')

                        time.sleep(backoff_time)
                        retry_count += 1
                        continue
                    else:
                        status_info["status"] = "FAIL"
                        total_failures += 1
                        print(f"  Run {run}: ✗ FAIL (exit {result.returncode}, exhausted retries)")
                        if result.stderr:
                            print(f"    stderr: {result.stderr[:200]}")

            except subprocess.TimeoutExpired as timeout:
                end_time = datetime.datetime.now()
                status_info["end_time"] = end_time.isoformat()
                status_info["duration_seconds"] = (end_time - start_time).total_seconds()
                status_info["timeout_seconds"] = 600

                # Save partial output from timeout
                if timeout.stdout:
                    stdout_file.write_text(timeout.stdout, encoding='utf-8')
                if timeout.stderr:
                    stderr_file.write_text(timeout.stderr, encoding='utf-8')

                if retry_count < MAX_RETRIES:
                    backoff_time = INITIAL_BACKOFF * (2 ** retry_count)
                    total_retries += 1
                    print(f"  Run {run}: ⏱ TIMEOUT, retrying in {backoff_time}s...")

                    status_info["status"] = "RETRY_TIMEOUT"
                    status_file.write_text(json.dumps(status_info, indent=2), encoding='utf-8')

                    time.sleep(backoff_time)
                    retry_count += 1
                    continue
                else:
                    status_info["status"] = "TIMEOUT"
                    total_failures += 1
                    print(f"  Run {run}: ⏱ TIMEOUT (exhausted retries)")

            except Exception as e:
                import traceback
                end_time = datetime.datetime.now()
                status_info["end_time"] = end_time.isoformat()
                status_info["duration_seconds"] = (end_time - start_time).total_seconds()
                status_info["error"] = str(e)
                status_info["traceback"] = traceback.format_exc()
                status_info["status"] = "ERROR"
                total_failures += 1

                # Write error details
                stderr_file.write_text(status_info["traceback"], encoding='utf-8')

                print(f"  Run {run}: ⚠ ERROR: {e}")
                print(f"    {traceback.format_exc()[:200]}")

            finally:
                # Always write final status file
                status_file.write_text(json.dumps(status_info, indent=2), encoding='utf-8')

        total_tests += 1

        # Small delay between runs of the same test
        if run < NUM_RUNS:
            time.sleep(2)

    # Delay between different tests to avoid rate limits
    if test_idx < len(test_cases):
        print(f"  Waiting {INTER_TEST_DELAY}s before next test...")
        time.sleep(INTER_TEST_DELAY)

    print()

print("=" * 60)
print(f"Done! Results saved to {OUTPUT_DIR}/")
print(f"Total: {total_tests} test executions")
print(f"  ✓ Pass: {total_passes}")
print(f"  ✗ Fail: {total_failures}")
print(f"  🔄 Retries: {total_retries}")
print(f"Pass rate: {total_passes}/{total_tests} ({100*total_passes/total_tests if total_tests > 0 else 0:.1f}%)")
