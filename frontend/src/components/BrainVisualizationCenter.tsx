import { useState } from 'react';
import { Brain, Dna, Layers, LayoutGrid, ZoomIn, TrendingUp, Download, Loader2, FileText, Box, Image } from 'lucide-react';
import type { BrainMapEvent, OverlapScoreEvent } from '../types';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { Brain3DViewer } from './Brain3DViewer';

type ViewMode = 'side-by-side' | 'overlay';
type RenderMode = '2d' | '3d';
type View3DMode = 'expression' | 'disease' | 'overlay';

interface BrainMapPanelProps {
  title: string;
  mapData: BrainMapEvent | null;
  icon: React.ReactNode;
  iconColorClass: string;
  isLoading?: boolean;
}

function BrainMapPanel({ title, mapData, icon, iconColorClass, isLoading }: BrainMapPanelProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className="relative flex-1 flex flex-col"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Title */}
      <div className="flex items-center gap-2 mb-2">
        <div className={cn(
          'w-6 h-6 rounded-lg flex items-center justify-center',
          iconColorClass
        )}>
          {icon}
        </div>
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
      </div>

      {/* Map Container */}
      <div className="relative flex-1 min-h-[350px] bg-bg-surface rounded-xl overflow-hidden border border-white/[0.08]">
        {!mapData ? (
          // Placeholder with scan line effect
          <div className="absolute inset-0 brain-placeholder flex items-center justify-center">
            {isLoading && <div className="brain-scan-overlay" />}
            <div className="flex flex-col items-center gap-2">
              <div className="w-16 h-16 rounded-full bg-bg-elevated flex items-center justify-center animate-neural-pulse">
                <Brain className="w-8 h-8 text-text-muted" />
              </div>
              <span className="text-xs text-text-muted font-medium">
                {isLoading ? 'Generating map...' : 'Awaiting data...'}
              </span>
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
                <Skeleton className="w-full h-full bg-bg-elevated" />
                <div className="brain-scan-overlay" />
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
              'flex items-end justify-center pb-4',
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

      {/* Top Regions */}
      {mapData && mapData.top_regions.length > 0 && (
        <div className="mt-2 px-1">
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
    </div>
  );
}

interface ColorScaleLegendProps {
  type: 'expression' | 'disease';
}

function ColorScaleLegend({ type }: ColorScaleLegendProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-muted">Low</span>
      <div className={cn(
        'flex-1 h-2 rounded-full',
        type === 'expression' ? 'heatmap-viridis' : 'heatmap-inferno'
      )} />
      <span className="text-xs text-text-muted">High</span>
    </div>
  );
}

interface OverlayViewProps {
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
  opacity: number;
}

function OverlayView({ expressionMap, diseaseMap, opacity }: OverlayViewProps) {
  const [expressionLoaded, setExpressionLoaded] = useState(false);
  const [diseaseLoaded, setDiseaseLoaded] = useState(false);

  if (!expressionMap || !diseaseMap) {
    return (
      <div className="relative flex-1 min-h-[400px] bg-bg-surface rounded-xl overflow-hidden border border-white/[0.08] flex items-center justify-center">
        <div className="flex flex-col items-center gap-2">
          <div className="w-16 h-16 rounded-full bg-bg-elevated flex items-center justify-center animate-neural-pulse">
            <Layers className="w-8 h-8 text-text-muted" />
          </div>
          <span className="text-xs text-text-muted font-medium">
            Both maps required for overlay
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex-1 min-h-[400px] bg-bg-surface rounded-xl overflow-hidden border border-white/[0.08]">
      {/* Expression Map (base layer) */}
      <img
        src={expressionMap.image_url}
        alt="Expression map"
        onLoad={() => setExpressionLoaded(true)}
        className={cn(
          'absolute inset-0 w-full h-full object-contain transition-opacity duration-500',
          expressionLoaded ? 'opacity-100' : 'opacity-0'
        )}
      />

      {/* Disease Map (overlay layer) */}
      <img
        src={diseaseMap.image_url}
        alt="Disease map"
        onLoad={() => setDiseaseLoaded(true)}
        className={cn(
          'absolute inset-0 w-full h-full object-contain transition-opacity duration-500',
          diseaseLoaded ? 'opacity-100' : 'opacity-0'
        )}
        style={{ opacity: opacity / 100, mixBlendMode: 'screen' }}
      />

      {/* Loading state */}
      {(!expressionLoaded || !diseaseLoaded) && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Skeleton className="w-full h-full bg-bg-elevated" />
        </div>
      )}
    </div>
  );
}

interface OverlapScoreDisplayProps {
  data: OverlapScoreEvent | null;
}

function OverlapScoreDisplay({ data }: OverlapScoreDisplayProps) {
  if (!data) return null;

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 75) return 'from-confidence-high to-emerald-400';
    if (percentile >= 50) return 'from-confidence-moderate to-amber-400';
    return 'from-confidence-low to-rose-400';
  };

  const getBadgeVariant = (percentile: number) => {
    if (percentile >= 75) return 'success';
    if (percentile >= 50) return 'warning';
    return 'destructive';
  };

  return (
    <div className="flex flex-col gap-2">
      {/* Section Title */}
      <h3 className="text-sm font-semibold text-text-primary flex items-center gap-2">
        <TrendingUp className="w-4 h-4 text-primary" />
        Pearson's Correlation Coefficient
      </h3>

      {/* Score Display */}
      <div className="flex items-center gap-6 px-4 py-3 bg-bg-surface rounded-xl border border-white/[0.08]">
        <div className="flex items-baseline gap-2">
          <span className="text-3xl font-bold text-text-primary animate-count-up">
            r = {data.r.toFixed(2)}
          </span>
          <Badge variant={getBadgeVariant(data.percentile)}>
            p{data.percentile}
          </Badge>
        </div>

        <div className="flex-1">
          <p className="text-sm text-text-secondary mb-2">{data.label}</p>
          <Progress
            value={data.percentile}
            className="h-2"
            indicatorClassName={cn('bg-gradient-to-r', getPercentileColor(data.percentile))}
            duration={2000}
          />
        </div>
      </div>
    </div>
  );
}

interface BrainVisualizationCenterProps {
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
  overlapScore: OverlapScoreEvent | null;
  isLoading?: boolean;
  showHeaderButtons?: boolean;
  pdfUrl?: string | null;
  sessionId?: string | null;
  onViewReport?: () => void;
  hasReport?: boolean;
}

export function BrainVisualizationCenter({
  expressionMap,
  diseaseMap,
  overlapScore,
  isLoading = false,
  showHeaderButtons = false,
  pdfUrl = null,
  sessionId = null,
  onViewReport,
  hasReport = false,
}: BrainVisualizationCenterProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('side-by-side');
  const [overlayOpacity, setOverlayOpacity] = useState(50);
  const [renderMode, setRenderMode] = useState<RenderMode>('3d');
  const [view3DMode, setView3DMode] = useState<View3DMode>('expression');

  const handleExportPdf = () => {
    if (!pdfUrl) return;
    const link = document.createElement('a');
    link.href = pdfUrl;
    link.download = `circuitmap-report-${sessionId || 'unknown'}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isPdfReady = pdfUrl !== null;

  return (
    <Card className="flex-1 flex flex-col overflow-hidden">
      <CardHeader className="py-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <Brain className="w-4 h-4 text-bg-base" />
          </div>
          <h2 className="text-base font-semibold text-text-primary">
            Brain Visualization
          </h2>
        </div>

        {/* Right side controls */}
        <div className="flex items-center gap-3">
          {/* Export/View buttons (when complete) */}
          {showHeaderButtons && (
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant={isPdfReady ? 'success' : 'secondary'}
                onClick={handleExportPdf}
                disabled={!isPdfReady}
              >
                {isPdfReady ? (
                  <>
                    <Download className="w-4 h-4" />
                    Export PDF
                  </>
                ) : (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Preparing...
                  </>
                )}
              </Button>
              {hasReport && onViewReport && (
                <Button size="sm" variant="action" onClick={onViewReport}>
                  <FileText className="w-4 h-4" />
                  View Report
                </Button>
              )}
            </div>
          )}

          {/* 2D/3D Render Mode Toggle */}
          <div className="flex items-center gap-1 bg-bg-surface rounded-lg p-1 border border-white/[0.08]">
            <button
              onClick={() => setRenderMode('3d')}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                renderMode === '3d'
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-muted hover:text-text-primary'
              )}
            >
              <Box className="w-3.5 h-3.5" />
              3D
            </button>
            <button
              onClick={() => setRenderMode('2d')}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                renderMode === '2d'
                  ? 'bg-primary/10 text-primary'
                  : 'text-text-muted hover:text-text-primary'
              )}
            >
              <Image className="w-3.5 h-3.5" />
              2D
            </button>
          </div>

          {/* View Mode Toggle (2D: side-by-side/overlay, 3D: expression/disease/overlay) */}
          <div className="flex items-center gap-1 bg-bg-surface rounded-lg p-1 border border-white/[0.08]">
            {renderMode === '2d' ? (
              <>
                <button
                  onClick={() => setViewMode('side-by-side')}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    viewMode === 'side-by-side'
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  )}
                >
                  <LayoutGrid className="w-3.5 h-3.5" />
                  Side by Side
                </button>
                <button
                  onClick={() => setViewMode('overlay')}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    viewMode === 'overlay'
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  )}
                >
                  <Layers className="w-3.5 h-3.5" />
                  Overlay
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setView3DMode('expression')}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    view3DMode === 'expression'
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  )}
                >
                  <Dna className="w-3.5 h-3.5" />
                  Expression
                </button>
                <button
                  onClick={() => setView3DMode('disease')}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    view3DMode === 'disease'
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  )}
                >
                  <Brain className="w-3.5 h-3.5" />
                  Disease
                </button>
                <button
                  onClick={() => setView3DMode('overlay')}
                  className={cn(
                    'flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all',
                    view3DMode === 'overlay'
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-muted hover:text-text-primary'
                  )}
                >
                  <Layers className="w-3.5 h-3.5" />
                  Overlay
                </button>
              </>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col gap-4">
        {renderMode === '3d' ? (
          /* 3D View */
          <div className="flex flex-col gap-4 flex-1">
            <Brain3DViewer
              expressionMap={expressionMap}
              diseaseMap={diseaseMap}
              viewMode={view3DMode}
              overlayOpacity={overlayOpacity}
              className="flex-1"
            />

            {/* Opacity Slider for 3D overlay mode */}
            {view3DMode === 'overlay' && expressionMap && diseaseMap && (
              <div className="flex items-center gap-4 px-2">
                <div className="flex items-center gap-2">
                  <Dna className="w-4 h-4 text-primary" />
                  <span className="text-xs text-text-secondary">Expression</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={overlayOpacity}
                  onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                  className="flex-1 h-2 rounded-full appearance-none bg-bg-surface cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-4
                    [&::-webkit-slider-thumb]:h-4
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-primary
                    [&::-webkit-slider-thumb]:shadow-glow-primary
                    [&::-webkit-slider-thumb]:cursor-pointer"
                />
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-secondary">Disease</span>
                  <Brain className="w-4 h-4 text-confidence-low" />
                </div>
              </div>
            )}
          </div>
        ) : viewMode === 'side-by-side' ? (
          /* 2D Side-by-Side View */
          <div className="flex gap-4 flex-1">
            <BrainMapPanel
              title="Target Expression"
              mapData={expressionMap}
              icon={<Dna className="w-3.5 h-3.5 text-bg-base" />}
              iconColorClass="bg-gradient-to-br from-primary to-cyan-400"
              isLoading={isLoading}
            />
            <BrainMapPanel
              title="Disease Anatomy"
              mapData={diseaseMap}
              icon={<Brain className="w-3.5 h-3.5 text-bg-base" />}
              iconColorClass="bg-gradient-to-br from-confidence-low to-rose-400"
              isLoading={isLoading}
            />
          </div>
        ) : (
          /* 2D Overlay View */
          <div className="flex flex-col gap-4 flex-1">
            <OverlayView
              expressionMap={expressionMap}
              diseaseMap={diseaseMap}
              opacity={overlayOpacity}
            />

            {/* Opacity Slider */}
            {expressionMap && diseaseMap && (
              <div className="flex items-center gap-4 px-2">
                <div className="flex items-center gap-2">
                  <Dna className="w-4 h-4 text-primary" />
                  <span className="text-xs text-text-secondary">Expression</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={overlayOpacity}
                  onChange={(e) => setOverlayOpacity(Number(e.target.value))}
                  className="flex-1 h-2 rounded-full appearance-none bg-bg-surface cursor-pointer
                    [&::-webkit-slider-thumb]:appearance-none
                    [&::-webkit-slider-thumb]:w-4
                    [&::-webkit-slider-thumb]:h-4
                    [&::-webkit-slider-thumb]:rounded-full
                    [&::-webkit-slider-thumb]:bg-primary
                    [&::-webkit-slider-thumb]:shadow-glow-primary
                    [&::-webkit-slider-thumb]:cursor-pointer"
                />
                <div className="flex items-center gap-2">
                  <span className="text-xs text-text-secondary">Disease</span>
                  <Brain className="w-4 h-4 text-confidence-low" />
                </div>
              </div>
            )}
          </div>
        )}

        {/* Color Scale Legends */}
        <div className="grid grid-cols-2 gap-4">
          <ColorScaleLegend type="expression" />
          <ColorScaleLegend type="disease" />
        </div>

        {/* Overlap Score */}
        <OverlapScoreDisplay data={overlapScore} />
      </CardContent>
    </Card>
  );
}
