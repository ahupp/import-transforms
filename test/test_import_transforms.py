import pytest
import sys
from os import path

MEGATRON = "Megatron"
OPTIMUS = "Optimus Prime"


def do_transform(src):
    return src.replace(MEGATRON, OPTIMUS)


def test_module_filter():
    sys.path.append(path.join(path.dirname(__file__), "pkg"))
    from import_transforms import set_module_source_transform

    set_module_source_transform("test_pkg1", do_transform)
    set_module_source_transform("test_pkg2.sub_pkg2", do_transform)

    import test_pkg1.sub_pkg1
    import test_pkg1.sub_module

    assert test_pkg1.VALUE == OPTIMUS
    assert test_pkg1.sub_pkg1.VALUE == OPTIMUS
    assert test_pkg1.sub_module.VALUE == OPTIMUS

    import test_pkg2.sub_pkg2
    import test_pkg2.sub_module

    assert test_pkg2.VALUE == MEGATRON
    assert test_pkg2.sub_pkg2.VALUE == OPTIMUS
    assert test_pkg2.sub_module.VALUE == MEGATRON
