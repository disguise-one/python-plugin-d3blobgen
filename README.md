# d3blobgen

Blob generation helper for D3 python plugin.

## Overview

This package offers an API `get_d3_function_blob` generating a blob of function body in `str` format. It can also be thought as a function template provider. This allows to leverage python stub file `d3.pyi` from Disguise for plugin development, so full type information can be accessed throughout the development process. 

The main functionality involves extracting Python functions, parsing their structure, and generating code templates with placeholder substitution.

## Project Structure

```
├── src/
│   ├── main.py                    # Entry point for demonstration
│   └── d3blobgen/                 # Core package
│       ├── __init__.py            # Package initialization
│       ├── core.py                # Function extraction and parsing logic
│       └── scripts/               # Directory to add any plugin python scripts
│           ├── d3.pyi             # D3 stubs file (replace with latest version)
│           ├── example.py         # Example plugin functions
│           └── <YOUR_SCRIPT>.py   # Any plugin python script can be added here
├── tests/
│   ├── __init__.py                # Test package initialization
│   └── test_core.py               # Comprehensive test suite for core functionality
├── pyproject.toml                 # Project configuration with pytest dependencies
├── uv.lock                        # Dependency lock file
└── README.md
```

**d3blobgen as package**

-  The directory structure below demonstrate how you can setup the stub file with scripts for the plugin development. The key take is that, d3 stub file must be located in the same directory as other script to generate blob from to access all type information.

```
<REPO_ROOT>
├── src/
│   └── main.py                    # Your entry point
│       └── scripts/               # Directory to add any plugin python scripts
│           ├── d3.pyi             # D3 stubs file (replace with latest version)
│           └── <YOUR_SCRIPT>.py   # Any plugin python script can be added here
└── .venv/               
    └── Lib/site-packages/d3blobgen/core.py # d3blobgen package
```

## Requirements

- **Python**: 3.11 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) for python package

## Installation

```bash
git clone https://github.com/disguise-one/python-plugin-d3blobgen.git
cd python-plugin-d3blobgen
uv sync
```

## Usage

### 1. Basic Example

```python
from d3blobgen import get_d3_function_blob

# Define your plugin function (no args)
def mrset_fn_with_args() -> dict[str, str]:
    import d3
    mr_set: d3.MixedRealitySet = d3.resourceManager.load(
        f'objects/mixedrealityset/mymrset.apx',
        d3.MixedRealitySet)
    # do anything with mrset
    return { "name": mr_set.name }

# Pass your plugin function to create d3 function blob
result = get_d3_function_blob(mrset_fn_with_args)

print(result)
"""
import d3
mr_set: d3.MixedRealitySet = d3.resourceManager.load(
    f'objects/mixedrealityset/mymrset.apx',
    d3.MixedRealitySet)
# do anything with mrset
return { "name": mr_set.name }
"""
```

### 2. Example with Argument

```python
from d3blobgen import get_d3_function_blob

# Define your plugin function (with arg mr_set_name)
def mrset_fn_with_args(mr_set_name: str) -> dict[str, str]:
    import d3
    mr_set: d3.MixedRealitySet = d3.resourceManager.load(
        f'objects/mixedrealityset/{mr_set_name}.apx',
        d3.MixedRealitySet)
    # do anything with mrset
    
    return { "name": mr_set.name }

# Pass your plugin function and argument to create d3 function blob
# - key: name of argument to replace in your function
# - val: value that will be replace the key
result = get_d3_function_blob(mrset_fn_with_args, {"mr_set_name": "my_scene"})

print(result)
"""
import d3
mr_set: d3.MixedRealitySet = d3.resourceManager.load(
    f'objects/mixedrealityset/my_scene.apx',
    d3.MixedRealitySet)
# do anything with mrset
return { "name": mr_set.name }
"""
```
- `{mr_set_name}` has been replaced with `my_scene`


### 3. Running the Demo

```bash
uv run python src/main.py
```

## Testing

This project uses pytest for testing. To run the tests:

**Install test dependencies**
```bash
uv sync --extra test
```

**Run tests**
```bash
uv run pytest
```

**Run tests with verbose output**
```bash
uv run pytest -v
```

## License

[MIT License](./LICENSE)
