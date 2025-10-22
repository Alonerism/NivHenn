export interface SearchFilters {
  cityName: string | null;
  locationId: string | null;
  locationType: string;
  page: number;
  size: number;
  priceMin: number | null;
  priceMax: number | null;
  buildingSizeMin: number | null;
  buildingSizeMax: number | null;
  propertyType: string;
  capRateMin: number | null;
  capRateMax: number | null;
  yearBuiltMin: number | null;
  yearBuiltMax: number | null;
  auctions: boolean;
  excludePendingSales: boolean | null;
}

export type AnalyzeFilters = Omit<SearchFilters, 'cityName'>;

export interface Listing {
  id: string;
  address: string | null;
  price: number | null;
  capRate: number | null;
  units: number | null;
  size: number | null;
  city?: string | null;
  state?: string | null;
  photoUrl?: string | null;
}

export interface AgentResult {
  name: string;
  score: number;
  summary: string;
}

export interface AnalysisResult {
  listingId: string;
  agents: AgentResult[];
  final: {
    summary: string;
    overallScore: number;
  };
  rawJson: unknown;
}

export interface AnalyzeRequest {
  listingIds: string[];
  crews: string[];
  filters: AnalyzeFilters;
  cityName: string | null;
}
