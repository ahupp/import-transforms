import ast
import pytest
import sys
from os import path

MEGATRON = "Megatron"
OPTIMUS = "Optimus Prime"

sys.path.append(path.join(path.dirname(__file__), "pkgs"))


def do_transform(src):
    return src.replace(MEGATRON, OPTIMUS)


def test_module_filter():
    from import_transforms import register_module_source_transform

    register_module_source_transform("test_pkg1.*", do_transform)
    register_module_source_transform("test_pkg2.sub_pkg2", do_transform)

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


class CallLoggerNodeTransform(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.Call:
        node = super().generic_visit(node)
        return ast.Call(
            func=ast.Name(id="_log_call", ctx=ast.Load()),
            args=[node, ast.Constant(value=ast.unparse(node))],
            keywords=[],
        )


def call_log_transform(source):
    tree = ast.parse(source, mode="exec")
    tree_trans = CallLoggerNodeTransform().visit(tree)
    tree_trans = ast.fix_missing_locations(tree_trans)
    print("unpars", ast.unparse(tree_trans))
    return tree_trans


def register_call_logger(module_glob):
    from import_transforms import register_module_source_transform

    log = []

    def do_log(value, call_str):
        log.append((call_str, value))
        return value

    register_module_source_transform(
        module_glob,
        call_log_transform,
        {"_log_call": do_log},
    )

    return log


def test_call_log():
    log = register_call_logger("test_call_logger")
    import test_call_logger

    #    from test_call_logger import top

    assert 6 == test_call_logger.top()
    assert log == [("bottom(value + 2)", 6), ("middle(1)", 6)]
