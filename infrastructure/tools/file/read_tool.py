"""Read file tool."""

from pathlib import Path
from typing import Any, Type, Optional
from pydantic import BaseModel, Field

from core.base.base_tool import BaseTool
from core.models.tool_context import ExecutionResult, ToolContext, SafetyTier

class ReadFileParams(BaseModel):
    """Parameters for reading a file."""
    file_path: str = Field(..., description="Absolute or relative path to the file to read.")

class ReadFileTool(BaseTool):
    """Tool to read the contents of a file."""
    
    @property
    def name(self) -> str:
        return "read_file"
        
    @property
    def description(self) -> str:
        return "Reads the textual contents of a file."
        
    @property
    def safety_tier(self) -> SafetyTier: return SafetyTier.READ_ONLY
        
    @property
    def input_schema(self) -> Type[BaseModel]:
        return ReadFileParams

    def _execute_impl(self, context: ToolContext, parsed_kwargs: Any) -> ExecutionResult:
        params: ReadFileParams = parsed_kwargs
        path = Path(params.file_path)
        
        if not path.is_absolute():
            path = Path(context.working_directory) / path
            
        if not path.exists():
            return ExecutionResult(success=False, error=f"File not found: {path}")
            
        if not path.is_file():
            return ExecutionResult(success=False, error=f"Path is not a file: {path}")
            
        try:
            if path.suffix.lower() == '.pdf':
                try:
                    import PyPDF2
                    text = ""
                    with open(path, 'rb') as f:
                        try:
                            reader = PyPDF2.PdfReader(f)
                            for page in reader.pages:
                                try:
                                    extracted = page.extract_text()
                                    if extracted:
                                        text += extracted + "\n"
                                except Exception as pdf_e:
                                    text += f"\n[Error extracting text from page: {pdf_e}]\n"
                        except Exception as reader_e:
                            return ExecutionResult(success=False, error=f"PyPDF2 failed to parse the file: {reader_e}")
                    if not text.strip():
                        return ExecutionResult(success=True, output="[PDF is an image or contains no extractable text]")
                    return ExecutionResult(success=True, output=text)
                except ImportError:
                    return ExecutionResult(success=False, error="PyPDF2 is not installed. Cannot read PDF files directly.")
            elif path.suffix.lower() == '.docx':
                try:
                    import docx
                    text = ""
                    doc = docx.Document(path)
                    for para in doc.paragraphs:
                        text += para.text + "\n"
                    if not text.strip():
                        return ExecutionResult(success=True, output="[DOCX contains no extractable text]")
                    return ExecutionResult(success=True, output=text)
                except ImportError:
                    return ExecutionResult(success=False, error="python-docx is not installed. Cannot read DOCX files directly.")
                except Exception as docx_e:
                    return ExecutionResult(success=False, error=f"python-docx failed to parse the file: {docx_e}")
            else:
                content = path.read_text(encoding="utf-8")
                return ExecutionResult(success=True, output=content)
        except Exception as e:
            return ExecutionResult(success=False, error=f"Failed to read file: {e}")
