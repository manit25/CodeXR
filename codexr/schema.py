from typing import List, Optional
from pydantic import BaseModel

class DocRef(BaseModel):
    title: str
    url: str

class Snippet(BaseModel):
    language: str
    filename: str
    code: str
    explanation: Optional[str] = None

class Subtask(BaseModel):
    title: str
    details: str
    steps: List[str] = []  # always required, even if empty

class Answer(BaseModel):
    context: str  # ✅ new field for explicit classification
    target: str
    difficulty: str
    subtasks: List[Subtask]
    snippet: Optional[Snippet] = None
    best_practices: List[str] = []
    gotchas: List[str] = []
    docs: List[DocRef] = []
