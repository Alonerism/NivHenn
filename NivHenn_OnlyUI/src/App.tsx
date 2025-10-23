import { useEffect, useState } from 'react';
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
  const [analyzeProgress, setAnalyzeProgress] = useState<number>(0);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [dark, setDark] = useState<boolean>(true);

  useEffect(() => {
    const root = document.documentElement;
    if (dark) root.classList.add('dark');
    else root.classList.remove('dark');
  }, [dark]);

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
    setAnalyzeProgress(0);
    setAnalysisError(null);
    try {
  const { cityName, ...filterWithoutCity } = filters;
  const analyzeFilters: AnalyzeFilters = filterWithoutCity;

      // Simulated progress while the backend processes
      const progressTimer = setInterval(() => {
        setAnalyzeProgress((p) => (p < 90 ? p + 5 : p));
      }, 500);

      const results = await analyzeListings({
        listingIds: Array.from(selectedIds),
        crews: selectedCrews,
        filters: analyzeFilters,
        cityName,
      });
      setAnalysisResults(results);
      setAnalyzeProgress(100);
      clearInterval(progressTimer);
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <header className="bg-white dark:bg-gray-900 shadow-sm border-b border-gray-200 dark:border-gray-800">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Search className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">NivHenn Analyzer</h1>
            </div>
            <button
              className="text-sm px-3 py-1 rounded border border-gray-300 dark:border-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800"
              onClick={() => setDark((d) => !d)}
            >
              {dark ? 'Light Mode' : 'Dark Mode'}
            </button>
          </div>
          <p className="mt-2 text-gray-600 dark:text-gray-300">
            Search properties and analyze investment opportunities with AI-powered insights
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 space-y-8">
        {searchError && (
          <div className="bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-200 border border-red-200 dark:border-red-800 px-4 py-3 rounded-md">
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
                <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Search Results ({listings.length})
                </h2>
                <p className="text-sm text-gray-600 dark:text-gray-300">
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

            {analyzeLoading && (
              <div className="w-full bg-gray-200 dark:bg-gray-800 rounded h-3 overflow-hidden">
                <div
                  className="h-3 bg-green-600 transition-all"
                  style={{ width: `${analyzeProgress}%` }}
                />
              </div>
            )}
          </>
        )}

        {analysisError && (
          <div className="bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-200 border border-red-200 dark:border-red-800 px-4 py-3 rounded-md">
            {analysisError}
          </div>
        )}

        {hasSearched && !searchLoading && listings.length === 0 && !searchError && (
          <div className="bg-white dark:bg-gray-900 rounded-lg shadow p-6 text-center text-gray-600 dark:text-gray-300">
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
