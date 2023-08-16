import subprocess
import ast
import pytest
import sys
from os import path
from import_transforms import SourceTransform

MEGATRON = "Megatron"
OPTIMUS = "Optimus Prime"

THIS_DIR = path.dirname(__file__)
sys.path.append(path.join(THIS_DIR, "pkgs"))


class OptimusSourceTransform(SourceTransform):
    def transform(self, source: str):
        return source.replace(MEGATRON, OPTIMUS)


def test_module_filter():
    from import_transforms import register_module_source_transform

    register_module_source_transform("test_pkg1.*", OptimusSourceTransform())
    register_module_source_transform("test_pkg2.sub_pkg2", OptimusSourceTransform())

    import test_pkg1.sub_pkg1
    import test_pkg1.sub_module

    assert test_pkg1.VALUE == MEGATRON
    assert test_pkg1.sub_pkg1.VALUE == OPTIMUS
    assert test_pkg1.sub_module.VALUE == OPTIMUS

    import test_pkg2.sub_pkg2
    import test_pkg2.sub_module

    assert test_pkg2.VALUE == MEGATRON
    assert test_pkg2.sub_pkg2.VALUE == OPTIMUS
    assert test_pkg2.sub_module.VALUE == MEGATRON


def register_call_logger(module_glob):
    from call_log import CallLogSourceTransform
    from import_transforms import register_module_source_transform

    log = []
    transform = CallLogSourceTransform(log)
    register_module_source_transform(module_glob, transform)
    return log


def test_call_log():
    log = register_call_logger("call_log_example")
    import call_log_example

    assert log == [
        (6, "bottom(value + 2)"),
        (6, "middle(1)"),
        (6, "top()"),
    ]


def test_main():
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "import_transforms",
            "call_log.CallLogSourceTransform",
            path.join(THIS_DIR, "call_log_example.py"),
        ],
        cwd=THIS_DIR,
    )
    assert out == b"6 bottom(value + 2)\n6 middle(1)\n6 top()\n"
