from __future__ import annotations

import ast
from pathlib import Path

CORE_ROOT = Path(__file__).parents[1] / "src" / "mobilitylab" / "core"
FORBIDDEN_IMPORT_PREFIXES = (
    "mobilitylab.adapters",
    "mobilitylab.agents",
    "mobilitylab.environment",
    "mobilitylab.experiments",
    "mobilitylab.scenario",
    "mobilitylab.services",
    "mobilitylab.visualization",
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


def test_core_does_not_import_domain_or_service_layers() -> None:
    forbidden_imports: list[tuple[str, str]] = []
    for path in CORE_ROOT.glob("*.py"):
        for module_name in imported_module_names(path):
            if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                forbidden_imports.append((path.name, module_name))

    assert forbidden_imports == []
