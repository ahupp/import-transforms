import sys
import fnmatch, re
import importlib
import importlib.abc
import ast
from typing import Callable, TypeVar

SourceTransform: TypeVar = Callable[[str], str | ast.AST]
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
        data_trans = self.transform(data.decode("utf-8"))
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


_MODULE_TO_LOADER_TRANSFORM: list[tuple[re.Pattern, LoaderTransform]] = []

sys.meta_path.insert(0, CustomLoaderMetaPathFinder)


def get_module_loader_transform(fullname) -> None | LoaderTransform:
    global _MODULE_TO_LOADER_TRANSFORM
    for regex, loader_transform in _MODULE_TO_LOADER_TRANSFORM:
        if regex.match(fullname):
            return loader_transform
    else:
        return None


def set_module_loader_transform(
    module_glob: str, loader_transform: LoaderTransform, check_loaded: bool = True
):
    global _MODULE_TO_LOADER_TRANSFORM

    # prefix matches either exact string, or
    regex = re.compile(fnmatch.translate(module_glob))
    if check_loaded:
        for mod in sys.modules:
            if regex.match(mod):
                raise Exception(
                    f"Already loaded matching module: {mod} for prefix {module_glob}"
                )

    _MODULE_TO_LOADER_TRANSFORM.append((regex, loader_transform))


def set_module_source_transform(
    module_glob: str, transform: SourceTransform, check_loaded: bool = True
):
    def f(base_loader):
        return SourceTransformLoader(base_loader, transform)

    set_module_loader_transform(module_glob, f, check_loaded)
