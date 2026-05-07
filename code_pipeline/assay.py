import ast
from typing import Optional, Tuple

from pydantic import ValidationError

from .contracts import get_expected_module_exports
from .models import CodeArtifact
from .plasmid_paths import get_output_run_dir


def check_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Lane 1: reject empty or syntactically invalid code."""
    if not code.strip():
        return False, "Ghost Output: generated code is empty."

    try:
        ast.parse(code)
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"


def check_interface(raw_data: dict) -> Tuple[bool, Optional[str]]:
    """Lane 2: validate the outer artifact envelope."""
    try:
        CodeArtifact(**raw_data)
        return True, None
    except ValidationError as e:
        return False, str(e)


def extract_function_signatures(code: str) -> dict[str, list[str]]:
    tree = ast.parse(code)
    signatures: dict[str, list[str]] = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            signatures[node.name] = [argument.arg for argument in node.args.args]

    return signatures


def check_required_functions(code: str, profile: str, module_id: str) -> Tuple[bool, Optional[str]]:
    """Lane 2b: enforce known module export contracts before writing outputs."""
    expected_exports = get_expected_module_exports(profile, module_id)
    if not expected_exports:
        return True, None

    try:
        signatures = extract_function_signatures(code)
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"

    issues: list[str] = []

    for function_name, expected_arguments in expected_exports.items():
        if function_name not in signatures:
            issues.append(f"Missing required export: {function_name}")
            continue

        actual_arguments = signatures[function_name]
        if actual_arguments != expected_arguments:
            issues.append(
                f"Signature mismatch for {function_name}: expected ({', '.join(expected_arguments)}) "
                f"but found ({', '.join(actual_arguments)})"
            )

    if issues:
        return False, "; ".join(issues)

    return True, None


def transfer_artifact(artifact: CodeArtifact) -> str:
    """Persist a validated artifact to outputs/runs/<run_name>/<module_id>.py."""
    import re

    output_dir = get_output_run_dir()
    output_dir.mkdir(parents=True, exist_ok=True)

    safe_module_id = re.sub(r"[^a-zA-Z0-9_]", "_", artifact.module_id)
    output_path = output_dir / f"{safe_module_id}.py"

    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(artifact.payload["code"])

    return str(output_path)
