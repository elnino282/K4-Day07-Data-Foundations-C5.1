import sys
from importlib import import_module

_student_package = import_module("src.2A202601356_HoangVanHuy")

for _module_name in ("agent", "chunking", "embeddings", "models", "store"):
    sys.modules[f"{__name__}.{_module_name}"] = import_module(
        f"src.2A202601356_HoangVanHuy.{_module_name}"
    )

for _name in getattr(_student_package, "__all__", []):
    globals()[_name] = getattr(_student_package, _name)

__all__ = list(getattr(_student_package, "__all__", []))
