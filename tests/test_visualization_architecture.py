from __future__ import annotations

import ast
from pathlib import Path

VISUALIZATION_ROOT = Path(__file__).parents[1] / "src" / "mobilitylab" / "visualization"
FORBIDDEN_IMPORT_PREFIXES = (
    "mobilitylab.adapters",
    "mobilitylab.services",
)


def imported_module_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module is not None
        ):
            names.add(node.module)
    return names


def test_visualization_keeps_external_backends_out_of_data_contracts() -> None:
    forbidden_imports: list[tuple[str, str]] = []
    for path in VISUALIZATION_ROOT.glob("*.py"):
        for module_name in imported_module_names(path):
            if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                forbidden_imports.append((path.name, module_name))

    assert forbidden_imports == []
