`import-transforms` is a Python library for intercepting and transforming source code at import time. Its main use is [unit-syntax](https://github.com/ahupp/unit-syntax), which modifies the Python syntax to support units of measure.

# Usage

Transforms are defined by extending `import_transforms.SourceTransform`. For a small example that adds logging of every single function call, see [call_log.py](https://github.com/ahupp/import-transforms/blob/main/test/call_log.py).

To apply a transform to future module imports:

```python
register_module_source_transform("target_module", my_transform)
import target_module # transform applied!
```

The first argument is a glob-style pattern on the fully-qualified module name:

- "foo" matches just that single module.
- "foo.\*" matches all sub-modules of "foo" (but not "foo" itself).
- "\*" will match all modules.

As a shorthand to apply a transform to all sub-modules of your package, place this in `**init**.py``:

```python
register_package_source_transform(__name__, my_transform)
```

# TODO

- check/support bytecode cached files
