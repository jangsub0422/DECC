import ast
import json
import subprocess
import sys
from pathlib import Path

from code_pipeline.contracts import (
    DEFAULT_PROFILE,
    ENTRY_POINT_CANDIDATES,
    get_profile_function_specs,
)
from code_pipeline.plasmid_paths import get_active_run_dir, get_output_run_dir

PROJECT_ROOT = Path(__file__).resolve().parent
FINAL_APP = PROJECT_ROOT / "final_app.py"
SMOKE_TEST_TIMEOUT_SECONDS = 10


def extract_module_exports(file_path: Path) -> dict[str, list[str]]:
    source_code = file_path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        print(f"[SKIP] SyntaxError detected in {file_path}")
        return {}

    exports: dict[str, list[str]] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            exports[node.name] = [argument.arg for argument in node.args.args]

    return exports


def detect_active_profile() -> str:
    plasmid_dir = get_active_run_dir(PROJECT_ROOT)
    if not plasmid_dir.exists():
        return DEFAULT_PROFILE

    profiles: set[str] = set()
    for plasmid_path in sorted(plasmid_dir.glob("plasmid_*.json")):
        try:
            data = json.loads(plasmid_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue

        profile = data.get("profile")
        if isinstance(profile, str) and profile.strip():
            profiles.add(profile.strip())

    if len(profiles) == 1:
        return profiles.pop()

    return DEFAULT_PROFILE


def scan_outputs() -> tuple[dict[str, dict[str, list[str]]], dict[str, str], list[str], list[str]]:
    output_dir = get_output_run_dir(PROJECT_ROOT)
    if not output_dir.exists():
        raise FileNotFoundError("[ERROR] outputs directory was not found. Run run_batch.py first.")

    module_exports: dict[str, dict[str, list[str]]] = {}
    function_map: dict[str, str] = {}
    duplicates: list[str] = []
    empty_modules: list[str] = []

    for file_path in sorted(output_dir.glob("*.py")):
        if file_path.name == "final_app.py":
            continue

        module_name = file_path.stem
        exports = extract_module_exports(file_path)
        module_exports[module_name] = exports

        if not exports:
            empty_modules.append(module_name)
            continue

        for function_name in exports:
            if function_name in function_map:
                duplicates.append(
                    f"{function_name}: outputs/{function_map[function_name]}.py and outputs/{module_name}.py"
                )
                continue
            function_map[function_name] = module_name

    return module_exports, function_map, duplicates, empty_modules


def validate_required_contracts(
    profile: str,
    module_exports: dict[str, dict[str, list[str]]],
    function_map: dict[str, str],
) -> tuple[bool, list[str]]:
    issues: list[str] = []
    required_function_specs = get_profile_function_specs(profile)

    for function_name, expected_arguments in required_function_specs.items():
        module_name = function_map.get(function_name)
        if not module_name:
            issues.append(f"Missing required function: {function_name}")
            continue

        actual_arguments = module_exports[module_name].get(function_name, [])
        if actual_arguments != expected_arguments:
            issues.append(
                f"Signature mismatch for {function_name}: expected ({', '.join(expected_arguments)}) "
                f"but found ({', '.join(actual_arguments)})"
            )

    return not issues, issues


def find_entry_points(function_map: dict[str, str]) -> list[tuple[str, str]]:
    entry_points: list[tuple[str, str]] = []

    for candidate in ENTRY_POINT_CANDIDATES:
        module_name = function_map.get(candidate)
        if module_name:
            entry_points.append((module_name, candidate))

    return entry_points


def build_entry_execution_code(module_name: str, function_name: str, output_dir: Path) -> list[str]:
    return [
        "import sys",
        "from pathlib import Path",
        "",
        f'ACTIVE_OUTPUT_DIR = Path(r"{output_dir}")',
        "if str(ACTIVE_OUTPUT_DIR) not in sys.path:",
        "    sys.path.insert(0, str(ACTIVE_OUTPUT_DIR))",
        "",
        f"from {module_name} import {function_name}",
        "",
        'if __name__ == "__main__":',
        f"    {function_name}()",
    ]


def run_import_smoke_test(output_dir: Path, module_names: list[str]) -> tuple[bool, list[str]]:
    if not module_names:
        return False, ["No generated modules were available for import smoke testing."]

    smoke_script = """
import importlib
import json
import sys
from pathlib import Path

output_dir = Path(sys.argv[1])
module_names = json.loads(sys.argv[2])

if str(output_dir) not in sys.path:
    sys.path.insert(0, str(output_dir))

issues = []
for module_name in module_names:
    try:
        importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        issues.append(f"{module_name}: {type(exc).__name__}: {exc}")

print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False))
raise SystemExit(0 if not issues else 1)
""".strip()

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                smoke_script,
                str(output_dir),
                json.dumps(module_names),
            ],
            check=False,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            input="",
            timeout=SMOKE_TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False, [
            f"Import smoke test timed out after {SMOKE_TEST_TIMEOUT_SECONDS} seconds. "
            "A generated module may be blocking during import."
        ]

    try:
        payload = json.loads(result.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError):
        details = result.stderr.strip() or result.stdout.strip() or "No smoke test output was produced."
        return False, [f"Import smoke test could not be parsed: {details}"]

    issues = payload.get("issues", [])
    if result.returncode != 0 and not issues:
        issues = [result.stderr.strip() or "Import smoke test failed without details."]

    return not issues, issues


def build_integration_failure_code(title: str, details: list[str]) -> list[str]:
    lines = [f'INTEGRATION_STATUS = "{title}"']
    if details:
        lines.append("INTEGRATION_DETAILS = [")
        lines.extend(f"    {json.dumps(detail, ensure_ascii=False)}," for detail in details)
        lines.append("]")
    else:
        lines.append("INTEGRATION_DETAILS = []")

    lines.extend(
        [
            "",
            'if __name__ == "__main__":',
            "    print(INTEGRATION_STATUS)",
            "    for detail in INTEGRATION_DETAILS:",
            '        print(f"- {detail}")',
        ]
    )
    return lines


def create_final_app() -> bool:
    active_run_dir = get_active_run_dir(PROJECT_ROOT)
    active_output_dir = get_output_run_dir(PROJECT_ROOT)
    profile = detect_active_profile()
    module_exports, function_map, duplicates, empty_modules = scan_outputs()
    entry_points = find_entry_points(function_map)
    contracts_ok, issues = validate_required_contracts(profile, module_exports, function_map)
    module_names = sorted(module_exports)
    smoke_ok, smoke_issues = run_import_smoke_test(active_output_dir, module_names)

    final_code_lines = [
        "# final_app.py",
        "# Auto-generated by DECC Integration Linker",
        f'ACTIVE_PROFILE = "{profile}"',
        "",
    ]

    if duplicates:
        print("[WARN] Duplicate function definitions were detected:")
        for duplicate in duplicates:
            print(f" - {duplicate}")

    if empty_modules:
        print("[WARN] Modules without usable function exports were detected:")
        for module_name in empty_modules:
            print(f" - outputs/{module_name}.py")

    has_usable_modules = bool(module_exports) and any(exports for exports in module_exports.values())
    has_single_entry = len(entry_points) == 1
    linker_issues = list(issues)

    if duplicates:
        linker_issues.extend(f"Duplicate function export detected: {duplicate}" for duplicate in duplicates)

    if empty_modules:
        linker_issues.extend(f"Module has no usable function exports: {module_name}" for module_name in empty_modules)

    if not smoke_ok:
        linker_issues.extend(f"Import smoke test failed: {issue}" for issue in smoke_issues)

    if not entry_points:
        linker_issues.append(
            f"No entry point found. Expected one of: {', '.join(ENTRY_POINT_CANDIDATES)}"
        )
    elif len(entry_points) > 1:
        formatted_entries = ", ".join(f"outputs/{module}.py::{function}()" for module, function in entry_points)
        linker_issues.append(f"Multiple entry points found: {formatted_entries}")

    if not has_usable_modules:
        final_code_lines.extend(
            build_integration_failure_code(
                "Integration skipped: outputs directory does not contain usable generated modules.",
                ["Run run_batch.py first, then re-run integration.py."],
            )
        )
        success = False
    elif contracts_ok and smoke_ok and has_single_entry and not duplicates and not empty_modules:
        module_name, function_name = entry_points[0]
        final_code_lines.extend(build_entry_execution_code(module_name, function_name, active_output_dir))
        success = True
    else:
        final_code_lines.extend(
            build_integration_failure_code(
                "Integration failed: module contracts are incomplete or no executable entry point could be linked.",
                linker_issues,
            )
        )
        success = False

    final_app_text = "\n".join(final_code_lines)
    FINAL_APP.write_text(final_app_text, encoding="utf-8")
    active_output_dir.mkdir(parents=True, exist_ok=True)
    (active_output_dir / "final_app.py").write_text(final_app_text, encoding="utf-8")

    print("=" * 60)
    print("[Integration Complete]")
    print(f"Created: {FINAL_APP}")
    print("=" * 60)
    print("[Notice] Integration only links generated modules. Final behavior still requires user review and testing.")

    print(f"\n[Active Profile] {profile}")
    print(f"[Active Plasmid Run] {active_run_dir}")
    print(f"[Active Output Run] {active_output_dir}")
    print("\n[Discovered Modules]")
    if module_exports:
        for module_name, exports in sorted(module_exports.items()):
            export_names = ", ".join(sorted(exports)) if exports else "(no functions)"
            print(f"{module_name}: {export_names}")
    else:
        print(" - outputs directory is empty")

    if len(entry_points) == 1:
        module_name, function_name = entry_points[0]
        print(f"\n[Linked Entry Point] outputs/{module_name}.py::{function_name}()")
    elif len(entry_points) > 1:
        print("\n[Linked Entry Point] Ambiguous")
    else:
        print("\n[Linked Entry Point] Not found")

    print(f"\n[Import Smoke Test] {'PASS' if smoke_ok else 'FAIL'}")
    if smoke_issues:
        for issue in smoke_issues:
            print(f" - {issue}")

    if linker_issues:
        print("\n[Contract Notes]")
        for issue in linker_issues:
            print(f" - {issue}")

    return success


if __name__ == "__main__":
    create_final_app()
