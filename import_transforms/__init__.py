import sys
import importlib
import importlib.abc
import ast
from typing import Callable, TypeVar

SourceTransform: TypeVar = Callable[[bytes], str | ast.AST]
LoaderTransform: TypeVar = Callable[
    [importlib.abc.SourceLoader], importlib.abc.SourceLoader
]


# TODO: support bytecode cached files
class SourceTransformLoader(importlib.abc.SourceLoader):
    def __init__(
        self,
        base_loader: importlib.abc.SourceLoader,
        transform: SourceTransform,
    ):
        self.base_loader = base_loader
        self.transform = transform

    def get_filename(self, fullname: str) -> str:
        return self.base_loader.get_filename(fullname)

    def get_data(self, path: str) -> bytes:
        return self.base_loader.get_data(path)

    def source_to_code(self, data, path, *, _optimize=-1):
        data_trans = self.transform(data)
        return compile(data_trans, path, mode="exec", optimize=_optimize)


class CustomLoaderMetaPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(fullname, path, target=None):
        loader_transform = get_module_loader_transform(fullname)
        if loader_transform is None:
            return None

        # Find the finder that would be responsible for this package
        # if a custom loader wasn't being used. This ensures
        # we'll work with whatever loading mechanism you
        # were using.
        for finder in sys.meta_path:
            if finder == CustomLoaderMetaPathFinder:
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is not None:
                if not isinstance(spec.loader, importlib.abc.SourceLoader):
                    raise ImportError(
                        f"import_transforms only supports SourceLoader, got {type(spec.loader)}"
                    )
                spec.loader = loader_transform(spec.loader)
                return spec
        else:
            return None


_MODULE_TO_LOADER_TRANSFORM = {}

sys.meta_path.insert(0, CustomLoaderMetaPathFinder)


def get_module_loader_transform(fullname) -> None | LoaderTransform:
    global _MODULE_TO_LOADER_TRANSFORM
    name_parts = fullname.split(".")
    for i in range(1, len(name_parts) + 1):
        loader = _MODULE_TO_LOADER_TRANSFORM.get(tuple(name_parts[0:i]))
        if loader is not None:
            return loader
    else:
        return None


def set_module_loader_transform(
    module_name: str,
    loader_transform: LoaderTransform,
):
    global _MODULE_TO_LOADER_TRANSFORM

    key = tuple(module_name.split("."))
    if key in _MODULE_TO_LOADER_TRANSFORM:
        raise Exception(f"transform already defined for {module_name}")
    _MODULE_TO_LOADER_TRANSFORM[key] = loader_transform


def set_module_source_transform(module_name: str, transform: SourceTransform):
    def f(base_loader):
        return SourceTransformLoader(base_loader, transform)

    set_module_loader_transform(module_name, f)

