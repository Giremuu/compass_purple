import importlib
import inspect
import pkgutil
from pathlib import Path

from engine.base import BlueModule, PurpleModule, RedModule

_BASE_CLASSES = {
    "red": RedModule,
    "blue": BlueModule,
    "purple": PurpleModule
}


def load_modules(module_type: str) -> dict[str, RedModule | BlueModule | PurpleModule]:
    """
    Auto-discover and instantiate all modules in engine/<module_type>/.
    Returns a dict mapping module name -> module instance.
    """
    base_class = _BASE_CLASSES[module_type]
    package_path = Path(__file__).parent / module_type
    package_name = f"engine.{module_type}"

    modules = {}

    for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
        full_name = f"{package_name}.{module_name}"
        mod = importlib.import_module(full_name)

        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, base_class) and obj is not base_class:
                instance = obj()
                modules[instance.name] = instance

    return modules


def load_all_modules() -> dict[str, dict]:
    """Load all red, blue and purple modules. Returns them grouped by type."""
    return {
        module_type: load_modules(module_type)
        for module_type in _BASE_CLASSES
    }
