from pydantic import BaseModel
from typing import Optional

class StartupBase(BaseModel):
    company_name: str
    industry: str
    stage: str
    funding_needed: float
    minimum_investment: float
    equity_offering: float
    funding_timeline: str
    primary_use: str
    description: str

class StartupCreate(StartupBase):
    pass

class Startup(StartupBase):
    id: int

    class Config:
        from_attributes = True

class SearchQueryRequest(BaseModel):
    company_name: str
    industry: str
    stage: str
    funding_needed: int
    minimum_investment: int
    equity_offering: int
    funding_timeline: str
    primary_use: str
    description: str