import { useState } from 'react';
import { Brain, Dna, ZoomIn } from 'lucide-react';
import type { BrainMapEvent } from '../types';
import { cn } from '@/lib/utils';
import { Card, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface BrainMapPanelProps {
  title: string;
  mapData: BrainMapEvent | null;
  icon: React.ReactNode;
  gradientFrom: string;
  gradientTo: string;
}

function BrainMapPanel({ title, mapData, icon, gradientFrom, gradientTo }: BrainMapPanelProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Card
      className="overflow-hidden hover-lift animate-fade-in"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <CardHeader className="py-2.5">
        <div className="flex items-center gap-2">
          <div className={cn(
            'w-6 h-6 rounded-lg flex items-center justify-center',
            `bg-gradient-to-br ${gradientFrom} ${gradientTo}`
          )}>
            {icon}
          </div>
          <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        </div>
      </CardHeader>

      {/* Map Container */}
      <div className="relative w-full h-[180px] bg-bg-surface overflow-hidden">
        {!mapData ? (
          // Placeholder with skeleton
          <div className="absolute inset-0 brain-placeholder flex items-center justify-center">
            <div className="flex flex-col items-center gap-2">
              <div className="w-16 h-16 rounded-full bg-bg-elevated flex items-center justify-center">
                <Brain className="w-8 h-8 text-text-muted animate-pulse" />
              </div>
              <span className="text-xs text-text-muted font-medium">Awaiting data...</span>
            </div>
          </div>
        ) : imageError ? (
          <div className="absolute inset-0 flex items-center justify-center bg-confidence-low/5">
            <div className="flex flex-col items-center gap-2">
              <div className="w-12 h-12 rounded-full bg-confidence-low/10 flex items-center justify-center">
                <Brain className="w-6 h-6 text-confidence-low" />
              </div>
              <span className="text-xs text-confidence-low font-medium">Failed to load image</span>
            </div>
          </div>
        ) : (
          <>
            {/* Loading skeleton */}
            {!imageLoaded && (
              <div className="absolute inset-0 flex items-center justify-center">
                <Skeleton className="w-full h-full" />
              </div>
            )}

            {/* Image */}
            <img
              src={mapData.image_url}
              alt={`${title} brain map`}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
              className={cn(
                'w-full h-full object-contain transition-all duration-700',
                imageLoaded ? 'opacity-100' : 'opacity-0',
                isHovered && 'scale-105'
              )}
            />

            {/* Hover overlay */}
            <div className={cn(
              'absolute inset-0 bg-gradient-to-t from-bg-base/80 via-transparent to-transparent',
              'flex items-end justify-center pb-3',
              'transition-opacity duration-500',
              isHovered ? 'opacity-100' : 'opacity-0'
            )}>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-elevated/90 rounded-full text-xs font-medium text-text-primary border border-white/[0.08]">
                <ZoomIn className="w-3 h-3" />
                View Details
              </div>
            </div>
          </>
        )}
      </div>

      {/* Top Regions Footer */}
      {mapData && mapData.top_regions.length > 0 && (
        <div className="px-4 py-2.5 bg-bg-surface border-t border-white/[0.08]">
          <p className="text-xs text-text-muted">
            <span className="font-medium text-text-secondary">Top regions: </span>
            {mapData.top_regions
              .slice(0, 3)
              .map((r, i) => (
                <span key={r.region}>
                  <span className="text-text-primary">{r.region}</span>
                  {i < Math.min(mapData.top_regions.length, 3) - 1 && ', '}
                </span>
              ))}
          </p>
        </div>
      )}
    </Card>
  );
}

interface BrainMapsProps {
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
}

export function BrainMaps({ expressionMap, diseaseMap }: BrainMapsProps) {
  return (
    <div className="grid grid-cols-2 gap-4">
      <BrainMapPanel
        title="Target Expression"
        mapData={expressionMap}
        icon={<Dna className="w-3.5 h-3.5 text-bg-base" />}
        gradientFrom="from-primary"
        gradientTo="to-cyan-400"
      />
      <BrainMapPanel
        title="Disease Anatomy"
        mapData={diseaseMap}
        icon={<Brain className="w-3.5 h-3.5 text-bg-base" />}
        gradientFrom="from-confidence-low"
        gradientTo="to-rose-400"
      />
    </div>
  );
}
