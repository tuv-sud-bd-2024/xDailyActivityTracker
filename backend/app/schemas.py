from typing import List, Optional
from pydantic import BaseModel
import datetime


class ParsedClientCandidate(BaseModel):
    client_name: str
    client_match_score: float


class ParsedDealCandidate(BaseModel):
    deal_name: str
    deal_match_score: float


class ParsedItem(BaseModel):
    item_id: str
    source_sender: Optional[str]
    source_timestamp: Optional[datetime.datetime]
    activity_date: Optional[datetime.date]
    start_time: Optional[str]
    end_time: Optional[str]
    description: Optional[str]
    is_client_activity: bool = False
    client_candidates: List[ParsedClientCandidate] = []
    deal_candidates: List[ParsedDealCandidate] = []
    parsing_notes: Optional[str]
    confidence: float = 0.0


class LLMResponse(BaseModel):
    source_block: str
    parsed_items: List[ParsedItem] = []
    overall_confidence: float = 0.0
