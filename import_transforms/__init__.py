from dataclasses import dataclass
from importlib.machinery import ModuleSpec
import sys
import fnmatch, re
import importlib
import importlib.abc
import ast
import types
import logging
from typing import Callable, TypeVar

SourceTransform: TypeVar = Callable[[str, str], str | ast.AST]


@dataclass
class SourceTransformState:
    transform: SourceTransform
    injected_values: dict[str, any]


class _TransformSourceLoader(importlib.abc.SourceLoader):
    def __init__(
        self,
        base_loader: importlib.abc.SourceLoader,
        source_transform: SourceTransform,
        injected: dict[str, any],
    ):
        self.base_loader = base_loader
        self.source_transform = source_transform
        self.injected = injected

    def get_filename(self, fullname: str) -> str:
        return self.base_loader.get_filename(fullname)

    def get_data(self, path: str) -> bytes:
        return self.base_loader.get_data(path)

    def source_to_code(self, data, path, *, _optimize=-1):
        data_trans = self.source_transform(data.decode("utf-8"))
        return compile(data_trans, path, mode="exec", optimize=_optimize)

    def exec_module(self, module: types.ModuleType) -> None:
        super().exec_module(module)
        module.__dict__.update(self.injected)


class _TransformLoaderMetaPathFinder(importlib.abc.MetaPathFinder):
    def find_spec(fullname, path, target=None):
        reg = _get_module_transform(fullname)
        if reg is None:
            return None
        source_transform, injected = reg

        for finder in sys.meta_path:
            # Find the finder that would be responsible for this package
            # if a custom loader wasn't being used. This ensures
            # we'll work with whatever loading mechanism you
            # were using.

            if finder == _TransformLoaderMetaPathFinder:
                continue
            spec = finder.find_spec(fullname, path, target)
            if spec is None:
                continue
            # Not much we can do if there's no source code, this might be surprising if it's your own package,
            # or not if you are matching everything
            if isinstance(spec.loader, importlib.abc.SourceLoader):
                spec.loader = _TransformSourceLoader(
                    spec.loader, source_transform, injected
                )
                # keep spec.loader_state unchanged since we don't know if the base loader
                # depends on it
            else:
                logging.debug(
                    f"Loader for {fullname} is not a SourceLoader, was {type(spec.loader)}"
                )

            return spec
        else:
            return None


_MODULE_TO_SOURCE_TRANSFORM: list[
    tuple[re.Pattern, (SourceTransform, dict[str, any])]
] = []

_HAS_INSERTED_MPF = False


def _get_module_transform(module_name) -> None | SourceTransform:
    global _MODULE_TO_SOURCE_TRANSFORM
    for regex, loader_transform in _MODULE_TO_SOURCE_TRANSFORM:
        if regex.match(module_name):
            return loader_transform
    else:
        return None


def register_module_source_transform(
    module_glob: str,
    transform: SourceTransform,
    injected: dict[str, any] = {},
    check_loaded: bool = True,
):
    """
    Registers a transformer to modify loaded source at import time.

    module_glob: a glob-style pattern describing which modules
                 this transform applies to.  Some examples:

                 "foo": only transform the module "foo"
                 "foo.*": transform any sub-module of foo, but not "foo" itself
                 "*": tranform every module import

    transform: a function that transforms the source into valid Python

    injected: key/value pairs to be inserted into the resulting module

    check_loaded: if True, raise an error if any already-loaded
                  module matches `module_glob`.
    """

    global _HAS_INSERTED_MPF
    if not _HAS_INSERTED_MPF:
        sys.meta_path.insert(0, _TransformLoaderMetaPathFinder)
        _HAS_INSERTED_MPF = True

    regex = re.compile(fnmatch.translate(module_glob))
    if check_loaded:
        for mod in sys.modules:
            if regex.match(mod):
                raise Exception(
                    f"Already loaded matching module: {mod} for prefix {module_glob}, re, {regex}"
                )

    global _MODULE_TO_SOURCE_TRANSFORM
    _MODULE_TO_SOURCE_TRANSFORM.append((regex, (transform, injected)))


def register_package_source_transform(
    pkg_name,
    transform: SourceTransform,
    injected: dict[str, any] = {},
    check_loaded: bool = True,
):
    return register_module_source_transform(
        f"{pkg_name}.*", transform, injected, check_loaded
    )
