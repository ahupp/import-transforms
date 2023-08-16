import import_transforms
import ast


# Python's `ast.NodeTransformer` traverses and modifies the AST of a parsed source file.
# Here we match `Call` nodes and modify each one to add a call to our logging function.
class CallLoggerNodeTransformer(ast.NodeTransformer):
    def visit_Call(self, node: ast.Call) -> ast.Call:
        # Make sure to call generic_visit to ensure we traverse argument nodes first
        node = super().generic_visit(node)
        return ast.Call(
            func=ast.Name(id="_log_call", ctx=ast.Load()),
            args=[node, ast.Constant(value=ast.unparse(node))],
            keywords=[],
        )


class CallLogSourceTransform(import_transforms.SourceTransform):
    def __init__(self, log: list[(any, str)] = None):
        def log_call(value, call_str):
            if log is not None:
                log.append((value, call_str))
            print(value, call_str)
            return value

        self.log_call = log_call

    def transform(self, source: str) -> ast.AST:
        tree = ast.parse(source, mode="exec")
        tree_trans = CallLoggerNodeTransformer().visit(tree)
        tree_trans = ast.fix_missing_locations(tree_trans)
        return tree_trans

    def injected_globals(self) -> dict[str, any]:
        return {"_log_call": self.log_call}
