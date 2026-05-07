from typing import TypedDict


class ArchitectureProfile(TypedDict):
    name: str
    keywords: list[str]
    canonical_modules: list[str]
    aliases: dict[str, str]
    blueprint_prompts: dict[str, str]


ARCHITECTURE_PROFILES: dict[str, ArchitectureProfile] = {
    "cli_crud": {
        "name": "cli_crud",
        "keywords": [
            "todo",
            "to-do",
            "task",
            "tasks",
            "checklist",
            "inventory",
            "contact",
            "ledger",
            "tracker",
            "planner",
        ],
        "canonical_modules": [
            "storage_handler",
            "input_controller",
            "ui_renderer",
            "domain_service",
            "entity_factory",
            "main_application_loop",
        ],
        "aliases": {
            "file_storage_handler": "storage_handler",
            "storage_manager": "storage_handler",
            "input_handler": "input_controller",
            "ui_display_renderer": "ui_renderer",
            "ui_render": "ui_renderer",
            "task_logic_service": "domain_service",
            "task_operations": "domain_service",
            "task_factory": "entity_factory",
            "main_loop": "main_application_loop",
        },
        "blueprint_prompts": {
            "storage_handler": (
                "Create a storage module. Export exactly load_items() and save_items(items). "
                "Persist the application state to a local JSON file. Return an empty list if the file "
                "does not exist. Do not define UI, input, domain logic, or main loop functions."
            ),
            "input_controller": (
                "Create an input module. Export exactly get_menu_choice() and get_item_input(). "
                "get_menu_choice() must read and return the raw menu choice string. "
                "get_item_input() must read and return one item description or record value. "
                "Do not print the menu. Do not define storage, UI, domain logic, or main loop functions."
            ),
            "ui_renderer": (
                "Create a UI rendering module. Export exactly render_menu() and render_item_list(items). "
                "render_menu() must only print the menu. render_item_list(items) must only display the current "
                "records. Do not read input, save files, mutate records, or define the main loop."
            ),
            "domain_service": (
                "Create a domain logic module. Export exactly add_item(items, value), remove_item(items, index), "
                "and update_item_status(items, index). Each function must return the updated item list. "
                "Do not define UI, input, storage, or main loop functions."
            ),
            "entity_factory": (
                "Create a helper module. Export exactly create_item(value). "
                "Return one normalized record dictionary for the application domain. "
                "Do not define domain service, storage, UI, input, or main loop functions."
            ),
            "main_application_loop": (
                "Create the entry module. Export exactly main_loop(). "
                "Assume the active output run directory itself is already on sys.path. "
                "Import functions using these exact import statements:\n"
                "from storage_handler import load_items, save_items\n"
                "from input_controller import get_menu_choice, get_item_input\n"
                "from ui_renderer import render_menu, render_item_list\n"
                "from domain_service import add_item, remove_item, update_item_status\n"
                "from entity_factory import create_item\n"
                "Do not redefine imported functions. "
                "Do not use relative imports. "
                "Do not use the outputs. prefix in imports. "
                "main_loop() must orchestrate the application only."
            ),
        },
    },
    "file_transformer": {
        "name": "file_transformer",
        "keywords": [
            "convert",
            "conversion",
            "csv",
            "json",
            "xml",
            "transform",
            "clean",
            "rename",
            "format",
        ],
        "canonical_modules": [
            "file_loader",
            "transform_service",
            "file_writer",
            "cli_controller",
        ],
        "aliases": {
            "loader": "file_loader",
            "reader": "file_loader",
            "converter": "transform_service",
            "transformer": "transform_service",
            "writer": "file_writer",
            "exporter": "file_writer",
            "main_loop": "cli_controller",
            "main_application_loop": "cli_controller",
        },
        "blueprint_prompts": {
            "file_loader": (
                "Create a file loading module. Export exactly load_input_file(path). "
                "The parameter name must be exactly path. "
                "Read source file content and return the in-memory representation needed by the transformer. "
                "Do not transform data, write files, or define CLI entry logic."
            ),
            "transform_service": (
                "Create a transform module. Export exactly transform_data(data). "
                "The parameter name must be exactly data. "
                "Receive loaded data and return transformed output data. "
                "Do not read files, write files, or define CLI entry logic."
            ),
            "file_writer": (
                "Create a file writing module. Export exactly write_output_file(path, data). "
                "The parameter names must be exactly path and data. "
                "Persist transformed data to the requested destination. "
                "Do not load files, transform data, or define CLI entry logic."
            ),
            "cli_controller": (
                "Create the entry module. Export exactly main_loop(). "
                "Assume the active output run directory itself is already on sys.path. "
                "Import functions using these exact import statements:\n"
                "from file_loader import load_input_file\n"
                "from transform_service import transform_data\n"
                "from file_writer import write_output_file\n"
                "Do not define load_input_file. "
                "Do not define transform_data. "
                "Do not define write_output_file. "
                "Do not define parse_cli_args unless explicitly needed as an internal helper. "
                "Do not use relative imports. "
                "Do not use the outputs. prefix in imports. "
                "main_loop() must orchestrate the transformation flow only."
            ),
        },
    },
    "data_analysis": {
        "name": "data_analysis",
        "keywords": [
            "analysis",
            "analyze",
            "statistics",
            "stats",
            "graph",
            "chart",
            "report",
            "dataset",
            "csv analysis",
        ],
        "canonical_modules": [
            "data_loader",
            "analysis_service",
            "visualizer",
            "reporter",
        ],
        "aliases": {
            "loader": "data_loader",
            "analyzer": "analysis_service",
            "analysis_engine": "analysis_service",
            "plotter": "visualizer",
            "chart_renderer": "visualizer",
            "summary_writer": "reporter",
            "main_loop": "reporter",
        },
        "blueprint_prompts": {
            "data_loader": (
                "Create a data loading module. Export exactly load_dataset(path). "
                "Load the source dataset and return an in-memory structure for downstream analysis. "
                "Do not analyze data, render charts, or write reports."
            ),
            "analysis_service": (
                "Create an analysis module. Export exactly analyze_dataset(dataset). "
                "Receive loaded data and return summary statistics or structured analysis results. "
                "Do not load files, render charts, or write reports."
            ),
            "visualizer": (
                "Create a visualization module. Export exactly build_visualizations(analysis_results). "
                "Return chart-ready or display-ready visualization artifacts from analysis results. "
                "Do not load data, compute analysis, or write reports."
            ),
            "reporter": (
                "Create the entry/report module. Export exactly main_loop(). "
                "Assume the active output run directory itself is already on sys.path. "
                "Import functions using these exact import statements:\n"
                "from data_loader import load_dataset\n"
                "from analysis_service import analyze_dataset\n"
                "from visualizer import build_visualizations\n"
                "Do not use relative imports. "
                "Do not use the outputs. prefix in imports. "
                "Coordinate analysis execution and present or save the final report output. "
                "Do not redefine loader, analysis, or visualization functions."
            ),
        },
    },
}
