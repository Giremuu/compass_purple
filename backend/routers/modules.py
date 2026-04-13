from fastapi import APIRouter, HTTPException

from engine.loader import load_all_modules, load_modules

router = APIRouter()


@router.get("/")
def list_all_modules():
    """List all available modules grouped by type."""
    all_modules = load_all_modules()
    return {
        module_type: [instance.info() for instance in instances.values()]
        for module_type, instances in all_modules.items()
    }


@router.get("/{module_type}")
def list_modules_by_type(module_type: str):
    """List modules for a specific type: red, blue or purple."""
    if module_type not in ("red", "blue", "purple"):
        raise HTTPException(status_code=404, detail="Unknown module type")
    modules = load_modules(module_type)
    return [instance.info() for instance in modules.values()]


@router.get("/{module_type}/{name}")
def get_module(module_type: str, name: str):
    """Get details of a specific module."""
    if module_type not in ("red", "blue", "purple"):
        raise HTTPException(status_code=404, detail="Unknown module type")
    modules = load_modules(module_type)
    if name not in modules:
        raise HTTPException(status_code=404, detail=f"Module '{name}' not found")
    return modules[name].info()
