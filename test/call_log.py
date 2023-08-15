import import_transforms
import ast


class CallLoggerNodeTransform(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.Call:
        node = super().generic_visit(node)
        return ast.Call(
            func=ast.Name(id="_log_call", ctx=ast.Load()),
            args=[node, ast.Constant(value=ast.unparse(node))],
            keywords=[],
        )


class CallLogSourceTransform(import_transforms.SourceTransform):
    def __init__(self, log=None):
        self.log = log

        def log_call(value, call_str):
            if log is not None:
                log.append((value, call_str))
            print(value, call_str)
            return value

        self.log_call = log_call

    def transform(self, source):
        tree = ast.parse(source, mode="exec")
        tree_trans = CallLoggerNodeTransform().visit(tree)
        tree_trans = ast.fix_missing_locations(tree_trans)
        return tree_trans

    def injected_globals(self):
        return {"_log_call": self.log_call}
