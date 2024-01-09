from pydantic import BaseModel
from typing import List, Tuple

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
    coin_names: list[str]
    analysis: list[Analysis]
    coin_change: list[Coin]

class CompareInfluencerResponse(BaseModel):
    coin: str
    prices: List[Tuple[int, float]]
    analysis_results_by_coin: list[Analysis]