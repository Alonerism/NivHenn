"""Pydantic models for API contracts and data structures."""
from typing import Optional
from pydantic import BaseModel, Field


class SearchParams(BaseModel):
    """Parameters for LoopNet property search."""
    
    locationId: Optional[str] = Field(default=None, description="Location ID from LoopNet")
    locationType: str = Field(default="city", description="Type: city, state, zipcode, etc.")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Results per page")
    
    # Optional filters
    priceMin: Optional[float] = Field(default=None, description="Minimum price")
    priceMax: Optional[float] = Field(default=None, description="Maximum price")
    buildingSizeMin: Optional[float] = Field(default=None, description="Min building SF")
    buildingSizeMax: Optional[float] = Field(default=None, description="Max building SF")
    propertyType: Optional[str] = Field(default=None, description="Property type filter")
    capRateMin: Optional[float] = Field(default=None, description="Min cap rate")
    capRateMax: Optional[float] = Field(default=None, description="Max cap rate")
    yearBuiltMin: Optional[int] = Field(default=None, description="Minimum year built")
    yearBuiltMax: Optional[int] = Field(default=None, description="Maximum year built")
    auctions: Optional[bool] = Field(default=None, description="Include auctions")
    excludePendingSales: Optional[bool] = Field(default=None, description="Exclude pending")


class FilterUpdate(BaseModel):
    """Partial update payload for stored SearchParams."""

    locationId: Optional[str] = None
    locationType: Optional[str] = None
    page: Optional[int] = Field(default=None, ge=1)
    size: Optional[int] = Field(default=None, ge=1, le=100)
    priceMin: Optional[float] = None
    priceMax: Optional[float] = None
    buildingSizeMin: Optional[float] = None
    buildingSizeMax: Optional[float] = None
    propertyType: Optional[str] = None
    capRateMin: Optional[float] = None
    capRateMax: Optional[float] = None
    yearBuiltMin: Optional[int] = None
    yearBuiltMax: Optional[int] = None
    auctions: Optional[bool] = None
    excludePendingSales: Optional[bool] = None


class Listing(BaseModel):
    """Simplified listing data from LoopNet."""
    
    listing_id: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    ask_price: Optional[float] = None
    building_size: Optional[float] = None
    property_type: Optional[str] = None
    cap_rate: Optional[float] = None
    year_built: Optional[int] = None
    units: Optional[int] = None
    raw: dict = Field(default_factory=dict, description="Raw API response")


class AgentOutput(BaseModel):
    """Standardized output from each specialist agent."""
    
    score_1_to_100: int = Field(..., ge=1, le=100, description="Integer score 1-100")
    rationale: str = Field(..., description="Short explanation of the score")
    notes: list[str] = Field(default_factory=list, description="3-6 key bullet points")


class AgentScores(BaseModel):
    """Collection of all agent scores."""
    
    investment: int = Field(..., ge=1, le=100)
    location: int = Field(..., ge=1, le=100)
    news_signal: int = Field(..., ge=1, le=100)
    risk_return: int = Field(..., ge=1, le=100)
    construction: int = Field(..., ge=1, le=100)
    overall: int = Field(..., ge=1, le=100)


class FinalReport(BaseModel):
    """Complete analysis report for a single listing."""
    
    listing_id: str
    address: Optional[str] = None
    ask_price: Optional[float] = None
    raw: dict = Field(default_factory=dict, description="Raw listing data")
    scores: AgentScores
    memo_markdown: str = Field(..., description="Consolidated investment memo")
    summary: Optional[str] = Field(default=None, description="High-level aggregated summary")
    
    # Individual agent outputs for reference
    investment_output: Optional[AgentOutput] = None
    location_output: Optional[AgentOutput] = None
    news_output: Optional[AgentOutput] = None
    vc_risk_output: Optional[AgentOutput] = None
    construction_output: Optional[AgentOutput] = None


class ListingPreview(BaseModel):
    """Listing payload optimized for the web UI."""

    id: str
    address: Optional[str] = None
    price: Optional[float] = None
    capRate: Optional[float] = None
    units: Optional[int] = None
    size: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    photoUrl: Optional[str] = None


class AgentSummary(BaseModel):
    """Simplified agent output for the UI."""

    name: str
    score: int
    summary: str


class FinalSummary(BaseModel):
    """Top-level portfolio manager summary for a listing."""

    summary: str
    overallScore: int


class AnalysisPayload(BaseModel):
    """UI friendly analysis response."""

    listingId: str
    agents: list[AgentSummary]
    final: FinalSummary
    rawJson: dict


class AnalyzeSelectionRequest(BaseModel):
    """Request payload for analyzing specific listings with chosen crews."""

    listingIds: list[str]
    crews: list[str]
    filters: Optional[SearchParams] = None
    cityName: Optional[str] = None
