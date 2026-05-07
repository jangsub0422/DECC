DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:7b"
DEFAULT_PROFILE = "generic"
TASKS_FILE = "tasks.json"

ENTRY_POINT_CANDIDATES = ("main_loop", "main")

PROFILE_FUNCTION_SPECS = {
    "cli_crud": {
        "load_items": [],
        "save_items": ["items"],
        "get_menu_choice": [],
        "get_item_input": [],
        "render_menu": [],
        "render_item_list": ["items"],
        "add_item": ["items", "value"],
        "remove_item": ["items", "index"],
        "update_item_status": ["items", "index"],
        "create_item": ["value"],
        "main_loop": [],
    },
    "file_transformer": {
        "load_input_file": ["path"],
        "transform_data": ["data"],
        "write_output_file": ["path", "data"],
        "main_loop": [],
    },
    "data_analysis": {
        "load_dataset": ["path"],
        "analyze_dataset": ["dataset"],
        "build_visualizations": ["analysis_results"],
        "main_loop": [],
    },
}

PROFILE_MODULE_EXPORT_SPECS = {
    "cli_crud": {
        "storage_handler": {
            "load_items": [],
            "save_items": ["items"],
        },
        "input_controller": {
            "get_menu_choice": [],
            "get_item_input": [],
        },
        "ui_renderer": {
            "render_menu": [],
            "render_item_list": ["items"],
        },
        "domain_service": {
            "add_item": ["items", "value"],
            "remove_item": ["items", "index"],
            "update_item_status": ["items", "index"],
        },
        "entity_factory": {
            "create_item": ["value"],
        },
        "main_application_loop": {
            "main_loop": [],
        },
    },
    "file_transformer": {
        "file_loader": {
            "load_input_file": ["path"],
        },
        "transform_service": {
            "transform_data": ["data"],
        },
        "file_writer": {
            "write_output_file": ["path", "data"],
        },
        "cli_controller": {
            "main_loop": [],
        },
    },
    "data_analysis": {
        "data_loader": {
            "load_dataset": ["path"],
        },
        "analysis_service": {
            "analyze_dataset": ["dataset"],
        },
        "visualizer": {
            "build_visualizations": ["analysis_results"],
        },
        "reporter": {
            "main_loop": [],
        },
    },
}


def build_contract_instruction() -> str:
    lines = [
        "Every module must define only the exports it claims to own.",
        "Do not redefine other modules' functions inside an entry module.",
        "Keep each module single-responsibility and import sibling functionality instead of copying it.",
        "Prefer clear, stable function names and simple argument lists.",
        "Use exactly one entry function such as main_loop() or main() for the executable module.",
    ]
    return "\n".join(lines)


def get_profile_function_specs(profile: str | None) -> dict[str, list[str]]:
    if not profile:
        return {}
    return PROFILE_FUNCTION_SPECS.get(profile, {})


def get_expected_module_exports(profile: str | None, module_id: str) -> dict[str, list[str]] | None:
    if not profile:
        return None
    return PROFILE_MODULE_EXPORT_SPECS.get(profile, {}).get(module_id)
