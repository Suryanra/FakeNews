from pydantic import BaseModel
from typing import List

class NewsQuery(BaseModel):
    text: str

class SourceDocument(BaseModel):
    content: str
    metadata: dict

class AnalysisResponse(BaseModel):
    assessment: str
    sources: List[SourceDocument]

class AddNewsRequest(BaseModel):
    text: str
    title: str = "User Added Fact"
    subject: str = "User Submitted"
