import { useState } from 'react';
import { clsx } from 'clsx';
import type { BrainMapEvent } from '../types';

interface BrainMapPanelProps {
  title: string;
  mapData: BrainMapEvent | null;
}

function BrainMapPanel({ title, mapData }: BrainMapPanelProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  return (
    <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">{title}</h3>
      </div>
      <div className="relative w-full h-[200px] bg-gray-100">
        {!mapData ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            Awaiting data...
          </div>
        ) : imageError ? (
          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-sm">
            Failed to load image
          </div>
        ) : (
          <>
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-8 h-8 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
              </div>
            )}
            <img
              src={mapData.image_url}
              alt={`${title} brain map`}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
              className={clsx(
                'w-full h-full object-contain transition-opacity duration-300',
                imageLoaded ? 'opacity-100' : 'opacity-0'
              )}
            />
          </>
        )}
      </div>
      {mapData && mapData.top_regions.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100">
          <p className="text-xs text-gray-500">
            Top regions:{' '}
            {mapData.top_regions
              .slice(0, 3)
              .map((r) => r.region)
              .join(', ')}
          </p>
        </div>
      )}
    </div>
  );
}

interface BrainMapsProps {
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
}

export function BrainMaps({ expressionMap, diseaseMap }: BrainMapsProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <BrainMapPanel title="Target Expression" mapData={expressionMap} />
      <BrainMapPanel title="Disease Anatomy" mapData={diseaseMap} />
    </div>
  );
}
