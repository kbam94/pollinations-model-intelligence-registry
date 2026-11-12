#!/usr/bin/env python3
"""Interactive, standard-library menu for the Model Intelligence Registry."""
from __future__ import annotations
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable
REGISTRY = ROOT / "registry.py"
BENCHMARK = ROOT / "benchmark.py"
LIVE = ROOT / "live_runner.py"
CATALOG = ROOT / "catalog.py"
TESTS = ROOT / "tests"
DATA = ROOT / "data"


def choose_number(prompt, maximum, allow_back=True):
    """Return a 1-based selection, or None for a back/cancel choice."""
    while True:
        suffix = " (0 to go back)" if allow_back else ""
        raw = input(f"{prompt}{suffix}: ").strip()
        if allow_back and raw == "0":
            return None
        try:
            value = int(raw)
        except ValueError:
            print("Enter a whole number.")
            continue
        if 1 <= value <= maximum:
            return value
        print(f"Choose a number from 1 to {maximum}.")


def choose_file_path(prompt, default_path):
    raw = input(f"{prompt} [{default_path}]: ").strip()
    path = Path(raw).expanduser() if raw else Path(default_path)
    if path.exists():
        answer = input(f"File exists: {path}\nOverwrite? Type YES: ").strip()
        if answer != "YES":
            print("Cancelled. Existing file was not changed.")
            return None
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_command(args, stdout=None):
    print("\n$ " + " ".join(str(x) for x in args))
    result = subprocess.run([str(x) for x in args], cwd=ROOT, stdout=stdout)
    if result.returncode == 0:
        print("\n[PASS] Command completed.")
    else:
        print(f"\n[FAIL] Command exited with code {result.returncode}.")
    return result.returncode


def select_model():
    # Importing the allowlist is local-only and does not read credentials.
    import live_runner
    models = sorted(live_runner.ALLOWED_MODELS)
    print("\nQUEST-TESTED MODEL ALLOWLIST")
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    selected = choose_number("Select model", len(models))
    return models[selected - 1] if selected else None


def select_case():
    import benchmark
    cases = benchmark.load_cases(benchmark.DEFAULT_CASES)
    print("\nBENCHMARK CASES")
    for i, case in enumerate(cases, 1):
        print(f"  {i:2}. {case['id']} | {case['category'].replace('_', ' ')}")
    selected = choose_number("Select case", len(cases))
    return cases[selected - 1]["id"] if selected else None


def show_registry():
    print("\n1. Model summary\n2. Test history")
    choice = choose_number("Select view", 2)
    if choice == 1:
        run_command([PYTHON, REGISTRY, "summary"])
    elif choice == 2:
        raw = input("Maximum history rows [30]: ").strip()
        try:
            limit = max(1, min(int(raw or "30"), 1000))
        except ValueError:
            print("Invalid row limit.")
            return
        run_command([PYTHON, REGISTRY, "list", "--limit", str(limit)])


def generate_plan():
    model = select_model()
    if not model:
        return
    default = Path.home() / "tmp" / f"pollinations-plan-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    path = choose_file_path("JSONL plan output path", default)
    if not path:
        return
    with path.open("w", encoding="utf-8") as output:
        code = run_command([PYTHON, BENCHMARK, "plan", "--model", model], stdout=output)
    if code == 0:
        print(f"Plan saved: {path}")
    else:
        path.unlink(missing_ok=True)


def preview_live_test():
    model = select_model()
    if not model:
        return
    case_id = select_case()
    if not case_id:
        return
    run_command([PYTHON, LIVE, "preview", "--model", model, "--case", case_id])


def run_live_test():
    print("\nLIVE TEST SAFETY NOTICE")
    print("This sends exactly one model request and may consume earned Quest Pollen.")
    print("Only the Quest-only key file is accepted by the live runner.")
    print("No paid-enabled diagnostic key or paid model is used by this menu.")
    if input("To continue to model selection, type SELECT ONE TEST: ").strip() != "SELECT ONE TEST":
        print("Cancelled. No request was sent.")
        return
    model = select_model()
    if not model:
        return
    case_id = select_case()
    if not case_id:
        return
    print("\nPassing control to the live runner. Its separate exact confirmation remains required.")
    # Inherit stdin/stdout/stderr. Never capture input or bypass the runner's confirmation.
    run_command([PYTHON, LIVE, "run", "--model", model, "--case", case_id])


def score_responses():
    raw = input("Path to model-responses JSONL: ").strip()
    if not raw:
        print("No input file selected.")
        return
    source = Path(raw).expanduser()
    if not source.is_file():
        print("File not found.")
        return
    output = input("Optional JSON report path (Enter = do not save): ").strip()
    args = [PYTHON, BENCHMARK, "score", source]
    if output:
        target = Path(output).expanduser()
        if target.exists() and input(f"Report exists: {target}\nOverwrite? Type YES: ").strip() != "YES":
            print("Cancelled. Existing report was not changed.")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        args += ["--output", target]
    run_command(args)


def export_history():
    default = Path.home() / "tmp" / f"model-history-{datetime.now():%Y%m%d-%H%M%S}.jsonl"
    path = choose_file_path("Registry JSONL export path", default)
    if path:
        run_command([PYTHON, REGISTRY, "export-jsonl", path])
        if path.exists():
            print(f"Export path: {path}")


def validate_project():
    print("\nSYSTEM VALIDATION")
    compile_args = [PYTHON, "-m", "py_compile", "registry.py", "benchmark.py", "live_runner.py", "compare.py", "catalog.py", "menu.py"]
    compile_code = run_command(compile_args)
    test_code = run_command([PYTHON, "-m", "unittest", "discover", "-s", "tests", "-v"])
    if compile_code == 0 and test_code == 0:
        print("\n[PASS] Compilation and automated tests passed.")
    else:
        print("\n[WARN] Validation found a failure. Review the output above.")


def main():
    actions = {
        "1": show_registry,
        "2": lambda: run_command([PYTHON, BENCHMARK, "list-cases"]),
        "3": generate_plan,
        "4": preview_live_test,
        "5": run_live_test,
        "6": score_responses,
        "7": export_history,
        "8": validate_project,
        "9": lambda: run_command([PYTHON, ROOT / "compare.py", "history"]),
        "10": lambda: run_command([PYTHON, CATALOG, "list"]),
    }
    while True:
        print("\n" + "=" * 58)
        print(" POLLINATIONS MODEL INTELLIGENCE REGISTRY")
        print("=" * 58)
        print("  1. View model registry / test history")
        print("  2. Browse benchmark questions")
        print("  3. Generate offline benchmark plan")
        print("  4. Preview one live model test (NO API CALL)")
        print("  5. Run one live model test (may spend Quest Pollen)")
        print("  6. Score benchmark response JSONL (OFFLINE)")
        print("  7. Export model history to JSONL")
        print("  8. Run system validation")
        print("  9. Model Comparison Center (OFFLINE)")
        print(" 10. Model Catalog Intelligence (OFFLINE)")
        print("  0. Exit")
        choice = input("\nSelect an option: ").strip()
        if choice == "0":
            print("Exiting. No background tasks were started.")
            return 0
        action = actions.get(choice)
        if action is None:
            print("Invalid option. Choose 0 through 10.")
            continue
        try:
            action()
        except KeyboardInterrupt:
            print("\nCancelled by user. Returning to menu.")
        except Exception as exc:
            print(f"\n[ERROR] {type(exc).__name__}: {exc}")
        input("\nPress Enter to return to the menu...")


if __name__ == "__main__":
    raise SystemExit(main())
