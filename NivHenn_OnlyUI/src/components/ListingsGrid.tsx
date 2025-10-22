import { Building2 } from 'lucide-react';
import type { Listing } from '../types';
import type { ChangeEvent, SyntheticEvent } from 'react';

interface ListingsGridProps {
  listings: Listing[];
  selectedIds: Set<string>;
  onToggleSelection: (id: string) => void;
}

export function ListingsGrid({ listings, selectedIds, onToggleSelection }: ListingsGridProps) {
  if (listings.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        No listings found. Try adjusting your filters.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {listings.map((listing) => (
        <div
          key={listing.id}
          className={`bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden cursor-pointer ${
            selectedIds.has(listing.id) ? 'ring-2 ring-blue-500' : ''
          }`}
          onClick={() => onToggleSelection(listing.id)}
        >
          <div className="relative h-48 bg-gray-200">
            {listing.photoUrl ? (
              <img
                src={listing.photoUrl}
                alt={listing.address ?? undefined}
                className="w-full h-full object-cover"
                onError={(e: SyntheticEvent<HTMLImageElement>) => {
                  e.currentTarget.style.display = 'none';
                  e.currentTarget.nextElementSibling?.classList.remove('hidden');
                }}
              />
            ) : null}
            <div className={`${listing.photoUrl ? 'hidden' : ''} absolute inset-0 flex items-center justify-center`}>
              <Building2 className="w-16 h-16 text-gray-400" />
            </div>
            <div className="absolute top-2 right-2">
              <input
                type="checkbox"
                checked={selectedIds.has(listing.id)}
                onChange={(e: ChangeEvent<HTMLInputElement>) => {
                  e.stopPropagation();
                  onToggleSelection(listing.id);
                }}
                className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="p-4 space-y-2">
            <h3 className="font-semibold text-gray-900 text-sm line-clamp-2">{listing.address}</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Price:</span>
                <p className="font-medium text-gray-900">
                  {listing.price ? `$${(listing.price / 1_000_000).toFixed(2)}M` : 'N/A'}
                </p>
              </div>
              <div>
                <span className="text-gray-600">Cap Rate:</span>
                <p className="font-medium text-gray-900">{listing.capRate ?? 'N/A'}%</p>
              </div>
              <div>
                <span className="text-gray-600">Units:</span>
                <p className="font-medium text-gray-900">{listing.units ?? 'N/A'}</p>
              </div>
              <div>
                <span className="text-gray-600">Size:</span>
                <p className="font-medium text-gray-900">
                  {listing.size ? `${listing.size.toLocaleString()} sqft` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
