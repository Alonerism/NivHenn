import { useState } from 'react';
import { Search } from 'lucide-react';
import { Filters } from './components/Filters';
import { ListingsGrid } from './components/ListingsGrid';
import { AgentChooser } from './components/AgentChooser';
import { AnalysisResults } from './components/AnalysisResults';
import { searchListings, analyzeListings } from './api';
import type { SearchFilters, Listing, AnalysisResult, AnalyzeFilters } from './types';

const DEFAULT_FILTERS: SearchFilters = {
  cityName: null,
  locationId: null,
  locationType: 'city',
  page: 1,
  size: 5,
  priceMin: null,
  priceMax: 3000000,
  buildingSizeMin: null,
  buildingSizeMax: null,
  propertyType: 'multifamily',
  capRateMin: 8,
  capRateMax: null,
  yearBuiltMin: null,
  yearBuiltMax: null,
  auctions: false,
  excludePendingSales: null,
};

function App() {
  const [filters, setFilters] = useState<SearchFilters>(DEFAULT_FILTERS);
  const [listings, setListings] = useState<Listing[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [selectedCrews, setSelectedCrews] = useState<string[]>([]);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const handleSearch = async () => {
    setSearchLoading(true);
    setSelectedIds(new Set());
    setAnalysisResults([]);
    setSearchError(null);
    setAnalysisError(null);
    setHasSearched(true);
    try {
      const results = await searchListings(filters);
      setListings(results);
    } catch (error) {
      console.error('Search failed:', error);
      const message = error instanceof Error ? error.message : 'Search failed';
      setSearchError(message);
      setListings([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleAnalyze = async () => {
    if (selectedIds.size === 0 || selectedCrews.length === 0) return;

    setAnalyzeLoading(true);
    setAnalysisError(null);
    try {
  const { cityName, ...filterWithoutCity } = filters;
  const analyzeFilters: AnalyzeFilters = filterWithoutCity;

      const results = await analyzeListings({
        listingIds: Array.from(selectedIds),
        crews: selectedCrews,
        filters: analyzeFilters,
        cityName,
      });
      setAnalysisResults(results);
    } catch (error) {
      console.error('Analysis failed:', error);
      const message = error instanceof Error ? error.message : 'Analysis failed';
      setAnalysisError(message);
      setAnalysisResults([]);
    } finally {
      setAnalyzeLoading(false);
    }
  };

  const canAnalyze = selectedIds.size > 0 && selectedCrews.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center space-x-3">
            <Search className="w-8 h-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">NivHenn Analyzer</h1>
          </div>
          <p className="mt-2 text-gray-600">
            Search properties and analyze investment opportunities with AI-powered insights
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {searchError && (
          <div className="bg-red-100 text-red-700 border border-red-200 px-4 py-3 rounded-md">
            {searchError}
          </div>
        )}

        <Filters
          filters={filters}
          onFilterChange={setFilters}
          onSearch={handleSearch}
          loading={searchLoading}
        />

        {listings.length > 0 && (
          <>
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900">
                  Search Results ({listings.length})
                </h2>
                <p className="text-sm text-gray-600">
                  {selectedIds.size} selected
                </p>
              </div>
              <ListingsGrid
                listings={listings}
                selectedIds={selectedIds}
                onToggleSelection={toggleSelection}
              />
            </div>

            <AgentChooser
              selectedCrews={selectedCrews}
              onCrewsChange={setSelectedCrews}
              onAnalyze={handleAnalyze}
              canAnalyze={canAnalyze}
              loading={analyzeLoading}
            />
          </>
        )}

        {analysisError && (
          <div className="bg-red-100 text-red-700 border border-red-200 px-4 py-3 rounded-md">
            {analysisError}
          </div>
        )}

        {hasSearched && !searchLoading && listings.length === 0 && !searchError && (
          <div className="bg-white rounded-lg shadow p-6 text-center text-gray-600">
            No listings found for the current filters. Try adjusting your criteria.
          </div>
        )}

        {analysisResults.length > 0 && (
          <AnalysisResults results={analysisResults} listings={listings} />
        )}
      </main>
    </div>
  );
}

export default App;
