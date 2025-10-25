"""Pydantic schemas for Zyana API."""
from typing import Optional, List, Literal
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator


class ParsedMessage(BaseModel):
    """Parsed message schema from natural language input."""
    intent: Literal[
        "transaction", "calendar", "loan", "repayment", "goal",
        "create_business", "query", "status", "report", "other"
    ]
    business: Optional[str] = None
    type: Optional[Literal["income", "expense", "transfer"]] = None
    amount: Optional[float] = None
    currency: Optional[str] = "PKR"
    category: Optional[str] = None
    person: Optional[str] = None
    date: Optional[date] = None
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    raw_text: str
    missing_fields: List[str] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_memory_request: bool = Field(default=False)  # True if user says "remember"
    
    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        """Parse date from various formats."""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            from dateutil import parser
            try:
                return parser.parse(v).date()
            except:
                return None
        return v


class TransactionCreate(BaseModel):
    """Schema for creating a transaction."""
    business_id: int
    type: Literal["income", "expense", "transfer"]
    amount: float = Field(gt=0)
    currency: str = "PKR"
    category: str
    person: Optional[str] = None
    date: date
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: int
    business_id: int
    business_name: str
    type: str
    amount: float
    currency: str
    category: str
    person: Optional[str]
    date: date
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class LoanCreate(BaseModel):
    """Schema for creating a loan."""
    business_id: int
    person: str
    amount: float = Field(gt=0)
    currency: str = "PKR"
    date: date
    description: Optional[str] = None
    status: Literal["active", "partially_paid", "paid"] = "active"


class LoanResponse(BaseModel):
    """Loan response schema."""
    id: int
    business_id: int
    business_name: str
    person: str
    amount: float
    currency: str
    date: date
    status: str
    remaining_amount: float
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EventCreate(BaseModel):
    """Schema for creating a calendar event."""
    user_id: int
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str] = None
    location: Optional[str] = None
    google_event_id: Optional[str] = None


class EventResponse(BaseModel):
    """Event response schema."""
    id: int
    user_id: int
    title: str
    start_time: datetime
    end_time: datetime
    description: Optional[str]
    location: Optional[str]
    google_event_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class BusinessCreate(BaseModel):
    """Schema for creating a business."""
    name: str
    slug: str
    type: str = "general"
    description: Optional[str] = None


class BusinessResponse(BaseModel):
    """Business response schema."""
    id: int
    name: str
    slug: str
    type: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class MemorySearchRequest(BaseModel):
    """Memory search request schema."""
    query: str
    limit: int = Field(default=5, ge=1, le=20)
    filters: Optional[dict] = None


class MemorySearchResult(BaseModel):
    """Memory search result item."""
    id: str
    snippet: str
    table: str
    date: Optional[date]
    business: Optional[str]
    score: float


class MemorySearchResponse(BaseModel):
    """Memory search response with results and summary."""
    query: str
    results: List[MemorySearchResult]
    summary: str
    total_found: int


class HabitProfile(BaseModel):
    """Habit profile entry."""
    id: int
    user_id: int
    key: str
    value: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    occurrences: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentLog(BaseModel):
    """Agent action log."""
    id: int
    agent_type: str
    action: str
    input_data: dict
    output_data: Optional[dict]
    status: Literal["success", "error", "pending"]
    error_message: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


class WebhookMessage(BaseModel):
    """Incoming webhook message."""
    user_id: str
    message: str
    platform: Literal["telegram", "web", "desktop"] = "telegram"
    metadata: Optional[dict] = None


class AgentResponse(BaseModel):
    """Standard agent response."""
    success: bool
    message: str
    data: Optional[dict] = None
    next_action: Optional[str] = None

