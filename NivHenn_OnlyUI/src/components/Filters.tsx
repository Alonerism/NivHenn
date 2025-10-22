import { SearchFilters } from '../types';

interface FiltersProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  onSearch: () => void;
  loading: boolean;
}

export function Filters({ filters, onFilterChange, onSearch, loading }: FiltersProps) {
  const updateFilter = (key: keyof SearchFilters, value: string | number | boolean | null) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 mb-4">Search Filters</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">City Name</label>
          <input
            type="text"
            value={filters.cityName || ''}
            onChange={(e) => updateFilter('cityName', e.target.value || null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Los Angeles"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location ID</label>
          <input
            type="text"
            value={filters.locationId || ''}
            onChange={(e) => updateFilter('locationId', e.target.value || null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Optional"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Location Type</label>
          <select
            value={filters.locationType}
            onChange={(e) => updateFilter('locationType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="city">City</option>
            <option value="state">State</option>
            <option value="zip">ZIP</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Property Type</label>
          <select
            value={filters.propertyType}
            onChange={(e) => updateFilter('propertyType', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="multifamily">Multifamily</option>
            <option value="retail">Retail</option>
            <option value="office">Office</option>
            <option value="industrial">Industrial</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price Min ($)</label>
          <input
            type="number"
            value={filters.priceMin || ''}
            onChange={(e) => updateFilter('priceMin', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No minimum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Price Max ($)</label>
          <input
            type="number"
            value={filters.priceMax || ''}
            onChange={(e) => updateFilter('priceMax', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="3,000,000"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Building Size Min (sqft)</label>
          <input
            type="number"
            value={filters.buildingSizeMin || ''}
            onChange={(e) => updateFilter('buildingSizeMin', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No minimum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Building Size Max (sqft)</label>
          <input
            type="number"
            value={filters.buildingSizeMax || ''}
            onChange={(e) => updateFilter('buildingSizeMax', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No maximum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cap Rate Min (%)</label>
          <input
            type="number"
            step="0.1"
            value={filters.capRateMin || ''}
            onChange={(e) => updateFilter('capRateMin', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="8"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Cap Rate Max (%)</label>
          <input
            type="number"
            step="0.1"
            value={filters.capRateMax || ''}
            onChange={(e) => updateFilter('capRateMax', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No maximum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Year Built Min</label>
          <input
            type="number"
            value={filters.yearBuiltMin || ''}
            onChange={(e) => updateFilter('yearBuiltMin', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No minimum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Year Built Max</label>
          <input
            type="number"
            value={filters.yearBuiltMax || ''}
            onChange={(e) => updateFilter('yearBuiltMax', e.target.value ? Number(e.target.value) : null)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="No maximum"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Page</label>
          <input
            type="number"
            min="1"
            value={filters.page}
            onChange={(e) => updateFilter('page', Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Results per Page</label>
          <input
            type="number"
            min="1"
            max="50"
            value={filters.size}
            onChange={(e) => updateFilter('size', Number(e.target.value))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="flex items-center space-x-6 pt-2">
        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={filters.auctions}
            onChange={(e) => updateFilter('auctions', e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">Include Auctions</span>
        </label>

        <label className="flex items-center space-x-2">
          <input
            type="checkbox"
            checked={filters.excludePendingSales || false}
            onChange={(e) => updateFilter('excludePendingSales', e.target.checked)}
            className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">Exclude Pending Sales</span>
        </label>
      </div>

      <button
        onClick={onSearch}
        disabled={loading}
        className="w-full mt-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-3 px-6 rounded-md transition-colors"
      >
        {loading ? 'Searching...' : 'Search Listings'}
      </button>
    </div>
  );
}
