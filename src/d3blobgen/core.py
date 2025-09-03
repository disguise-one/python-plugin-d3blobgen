import ast
import inspect
from pydantic import BaseModel, Field
from typing import Callable, Any


class FunctionInfo(BaseModel):
    name: str = Field(description="name of extracted function")
    body: str = Field(description="body of extracted function in str format")
    args: list[str] = Field(default=[], description="list of arguments from extracted function")

def extract_function_blob(func: Callable[..., Any]) -> str:
    """Extract the complete source code of a function using inspect.getsource().
    
    Args:
        func: Any callable function object
        
    Returns:
        str: Complete source code of the function including def line and body
    """
    source:str = inspect.getsource(func)
    return source

def extract_function_info(source_code: str) -> FunctionInfo:
    """Parse function source code and extract name, body statements, and argument list.
    
    Args:
        source_code: String containing Python function source code
        
    Returns:
        FunctionInfo: Object containing function name, body code, and argument names
        
    Raises:
        ValueError: If source code is not a function blob
    """
    
    tree: ast.Module = ast.parse(source_code)
    
    # Check if first node exists and is a function
    if not tree.body:
        raise ValueError(f"Given input is not a function\ninput:{source_code}")
    
    first_node = tree.body[0]
    if not isinstance(first_node, ast.FunctionDef):
        node_type = type(first_node).__name__
        raise ValueError(f"Given input is not a function\ninput:{source_code}")
    
    # Extract function name
    function_name = first_node.name

    # Extract body statements
    body_nodes = first_node.body
    
    # Convert back to source code
    body_source = ""
    for stmt in body_nodes:
        body_source += ast.unparse(stmt) + "\n"

    # Extract function arguments
    args: list[str] = []
    for arg in first_node.args.args:
        args.append(arg.arg)
    
    return FunctionInfo(
        name=function_name,
        body=body_source.strip(),
        args=args
    )

def get_d3_function_blob(func: Callable[..., Any], args: dict[str,str]={}) -> str:
    """Extract function body and replace placeholder arguments with provided values.
    
    Args:
        func: Function object to extract code from
        args: Dictionary mapping argument names to replacement values.
            Used to substitute template placeholders in the function code.
            Keys are the placeholder names, values are the strings to replace them with.
        
    Returns:
        str: Function body code with placeholders replaced
        
    Raises:
        ValueError: If provided args don't match function's argument list
    """
    blob = extract_function_blob(func)
    info = extract_function_info(blob)

    if set(args.keys()) != set(info.args):
        raise ValueError(f"mismatch between args and function args\nargs: {args}\nfunc: {info.args}")
    
    for key, val in args.items():
        info.body = info.body.replace(f'{{{key}}}', val)

    return info.body
