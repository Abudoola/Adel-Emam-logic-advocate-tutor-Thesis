"""
run_tests.py
------------
Tiny standalone test runner. Works without PyTest installed.

For a full test report with parameterised cases, install pytest and
run:
    pytest tests/ -v

This runner discovers `test_*` functions and `Test*` classes in
tests/test_*.py modules, runs each, prints PASS/FAIL, and exits with
status 0/1 accordingly.
"""
from __future__ import annotations
import importlib
import inspect
import os
import sys
import traceback

# Inject conftest's path/stub setup
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THIS_DIR)
sys.path.insert(0, os.path.join(THIS_DIR, "tests"))
import conftest  # noqa


def _collect(module):
    tests = []
    for name, obj in inspect.getmembers(module):
        if inspect.isfunction(obj) and name.startswith("test_"):
            tests.append((name, obj, None))
        elif inspect.isclass(obj) and name.startswith("Test"):
            instance = obj()
            for mname, method in inspect.getmembers(instance):
                if mname.startswith("test_"):
                    tests.append((f"{name}.{mname}", method, instance))
    return tests


def _run_parametric(name, fn, instance, module):
    """Detect pytest.mark.parametrize and expand it. Otherwise just run once."""
    # Look for pytest_mark stored by pytest decorator. If pytest is not
    # available we cannot read the mark, so fall back to skipping the
    # parametrize step.
    parametrize = getattr(fn, "pytestmark", None)
    if not parametrize:
        try:
            fn()
            return [(name, True, None)]
        except Exception:
            return [(name, False, traceback.format_exc())]
    # Find the parametrize mark
    cases = None
    for mark in parametrize:
        if mark.name == "parametrize":
            argnames, argvalues = mark.args[:2]
            cases = argvalues
            break
    if cases is None:
        try:
            fn()
            return [(name, True, None)]
        except Exception:
            return [(name, False, traceback.format_exc())]

    results = []
    for case in cases:
        case_id = getattr(case, "id", str(case)[:30])
        try:
            fn(case)
            results.append((f"{name}[{case_id}]", True, None))
        except Exception:
            results.append((f"{name}[{case_id}]", False, traceback.format_exc()))
    return results


def main():
    test_dir = os.path.join(THIS_DIR, "tests")
    modules = sorted(f for f in os.listdir(test_dir)
                      if f.startswith("test_") and f.endswith(".py"))

    total_pass = total_fail = 0
    failures = []

    for fname in modules:
        modname = fname[:-3]
        print(f"\n=== {modname} ===")
        try:
            mod = importlib.import_module(f"tests.{modname}")
        except Exception:
            print(f"  FAIL to import: {traceback.format_exc()}")
            total_fail += 1
            continue
        tests = _collect(mod)
        for name, fn, instance in tests:
            try:
                # Check for pytest parametrize
                if hasattr(fn, "pytestmark"):
                    results = _run_parametric(name, fn, instance, mod)
                    for r_name, ok, err in results:
                        if ok:
                            total_pass += 1
                            # don't print every parametric subcase
                        else:
                            total_fail += 1
                            failures.append((f"{modname}.{r_name}", err))
                    n_ok = sum(1 for _, ok, _ in results if ok)
                    n_fail = sum(1 for _, ok, _ in results if not ok)
                    marker = "PASS" if n_fail == 0 else "FAIL"
                    print(f"  {marker}  {name}  ({n_ok} ok, {n_fail} fail)")
                else:
                    fn()
                    total_pass += 1
                    print(f"  PASS  {name}")
            except Exception:
                total_fail += 1
                failures.append((f"{modname}.{name}", traceback.format_exc()))
                print(f"  FAIL  {name}")

    print()
    print("=" * 60)
    print(f"PASS: {total_pass}    FAIL: {total_fail}")
    print("=" * 60)
    if failures:
        print("\nFailures detail:")
        for name, err in failures:
            print(f"\n--- {name} ---")
            print(err)
        sys.exit(1)
    print("\nAll tests passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
