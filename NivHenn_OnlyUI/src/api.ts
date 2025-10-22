import type { SearchFilters, Listing, AnalyzeRequest, AnalysisResult } from './types';

const API_BASE = ((import.meta as ImportMeta & { env: Record<string, string | undefined> }).env.VITE_API_BASE)
  || 'http://localhost:8000';

export async function searchListings(filters: SearchFilters): Promise<Listing[]> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value === null || value === undefined) {
      return;
    }
    if (typeof value === 'boolean') {
      params.append(key, value ? 'true' : 'false');
    } else {
      params.append(key, String(value));
    }
  });

  const response = await fetch(`${API_BASE}/search?${params.toString()}`, {
    method: 'GET',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Failed to fetch listings');
  }

  return await response.json();
}

export async function analyzeListings(request: AnalyzeRequest): Promise<AnalysisResult[]> {
  const payload: AnalyzeRequest = {
    listingIds: request.listingIds,
    crews: request.crews,
    filters: request.filters,
    cityName: request.cityName,
  };

  const response = await fetch(`${API_BASE}/analyze/listings`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || 'Failed to analyze listings');
  }

  return await response.json();
}
