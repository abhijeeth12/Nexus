"""AST-aware code reading tool."""

import ast
from pathlib import Path
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ReadAstParams(BaseModel):
    """Parameters for reading code structure."""
    file_path: str = Field(..., description="Path to the python file to analyze.")
    target_node: Optional[str] = Field(None, description="Optional name of class or function to extract specifically.")

class ReadAstTool(BaseTool):
    """Tool to read the abstract syntax tree of a python file to extract classes and functions."""
    
    @property
    def name(self) -> str:
        return "read_ast"
        
    @property
    def description(self) -> str:
        return "Parses a python file to understand its structure, classes, and functions. DO NOT PASS A DIRECTORY PATH. IT ONLY ACCEPTS A SINGLE .py FILE."
        
    @property
    def safety_tier(self) -> SafetyTier:
        return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ReadAstParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ReadAstParams = parsed_kwargs
        path = Path(params.file_path)
        
        if not path.is_absolute():
            path = Path(context.working_directory) / path
            
        if not path.exists():
            return ExecutionResult(success=False, error=f"File not found: {path}")
            
        if path.suffix != ".py":
            return ExecutionResult(success=False, error="Currently only python (.py) files are supported for AST parsing.")
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            tree = ast.parse(source, filename=str(path))
            
            output_lines = []
            if params.target_node:
                # Find specific class or function and extract source
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        if node.name == params.target_node:
                            output_lines.append(f"--- {node.__class__.__name__}: {node.name} ---")
                            output_lines.append(ast.get_source_segment(source, node) or "Source unavailable.")
                            return ExecutionResult(success=True, output="\n".join(output_lines))
                
                return ExecutionResult(success=False, error=f"Target node '{params.target_node}' not found in file.")
            
            # List all classes and functions
            output_lines.append(f"AST Structure for {path.name}:")
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    output_lines.append(f"Class: {node.name}")
                    for child in node.body:
                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            output_lines.append(f"  Method: {child.name}")
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    output_lines.append(f"Function: {node.name}")
                    
            if len(output_lines) == 1:
                output_lines.append("(No classes or functions defined)")
                
            return ExecutionResult(success=True, output="\n".join(output_lines))
        except SyntaxError as e:
            return ExecutionResult(success=False, error=f"Syntax error in file: {e}")
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to parse AST: {e}")
            
    def _rollback_impl(self, context: ToolContext) -> ExecutionResult:
        return ExecutionResult(success=True, output="Nothing to rollback.")
