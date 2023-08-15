from . import run_script
import ast
import sys
import importlib
from . import SourceTransform

if len(sys.argv) < 3:
    sys.exit(
        "usage: python -m import_transforms some_package.SomeSourceTransform file_to_run.xyz"
    )

transform_path = sys.argv[1]
script_path = sys.argv[2]
splat = transform_path.rsplit(".", 1)
if len(splat) != 2:
    sys.exit(
        'SourceTransform should be passed as fully qualified name, e.g, "some_module.SomeTransform"'
    )
(mod, name) = splat


m = importlib.import_module(mod)
transformer_class = m.__dict__.get(name)
if transformer_class is None:
    sys.exit(f"module '{mod}' exists, but does not contain '{name}'")

if not issubclass(transformer_class, SourceTransform):
    sys.exit(
        f"{transformer_class} is not a subclass of import_transforms.SourceTransform"
    )


transform = transformer_class()
# print(ast.unparse(transform.transform(open(script_path).read())))

run_script(script_path, transform)
