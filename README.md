`import-transforms` is a Python library for intercepting and transforming source code at import time. The main use case is [unit-syntax](https://github.com/ahupp/unit-syntax), which modifies the Python syntax to support units of measure.

# Usage

Transforms are a function that takes the raw module source as input and returns the transformed source as a `str` or `ast.AST`. So for example, this transform would print the name of the module when it is imported:

```python
def print_name(source, path):
    return f'print(f"{__name__}")\n' + source
```

Transforms are registed with a glob-style module pattern:

- "foo" matches just that single module.
- "foo.\*" matches all sub-modules of "foo" (but not "foo" itself).
- "\*" will match all modules.

Typically you'll want to register the transform in your pacakge's `__init__.py`, with a pattern that applies to just the sub-modules of your package, e.g:

```python
register_package_source_transform(__name__, my_transform)
```

# Example

# TODO

- check/support bytecode cached files
- how do I define a type parameter that matches a function?
- bare module import fails check_module?
