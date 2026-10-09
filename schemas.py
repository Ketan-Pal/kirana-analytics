from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class SaleItemIn(BaseModel):
    raw_text: Optional[str] = None
    standardized_name: Optional[str] = None
    category: Optional[str] = "Other"
    quantity: float = 1.0
    unit: Optional[str] = "packet"
    pack_size: Optional[str] = "Standard"
    unit_price: float = 0.0
    line_total: Optional[float] = None

class SaleEntryIn(BaseModel):
    sale_no: int = 1
    time: Optional[str] = "12:00 PM"
    time_period: Optional[str] = "Evening"
    bill_total: float = 0.0
    weather: Optional[str] = "Normal"
    festival: Optional[str] = "None"
    items: List[SaleItemIn] = Field(default_factory=list)

class SalesIngestPayload(BaseModel):
    date: Optional[str] = None
    day_weather: Optional[str] = "Normal"
    day_festival: Optional[str] = "None"
    sales: List[SaleEntryIn] = Field(default_factory=list)

class GenericApiResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Any] = None
