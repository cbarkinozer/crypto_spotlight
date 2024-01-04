from typing import List
from pydantic import BaseModel

class Analysis(BaseModel):
    text_chunk: str
    coin: str
    guess: str

class Coin(BaseModel):
    coin:str
    change_percent: float

class AnalyzeYoutubeResponse(BaseModel):
    title: str
    author: str
    view_count: int
    publish_date: str
    transcription: str
    coin_names: List[str]
    analysis: List[Analysis]
    coin_change: List[Coin]