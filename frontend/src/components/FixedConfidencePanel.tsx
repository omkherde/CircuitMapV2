import { useState } from 'react';
import { Shield, ChevronDown, CheckCircle2, AlertCircle, XCircle, Clock, TrendingUp } from 'lucide-react';
import type { ConfidenceDimension, ConfidenceLevel, OverlapScoreEvent } from '../types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface ConfidenceMetricRowProps {
  dimension: ConfidenceDimension;
  isExpanded: boolean;
  onToggle: () => void;
}

function ConfidenceMetricRow({ dimension, isExpanded, onToggle }: ConfidenceMetricRowProps) {
  // Animation is driven by whether level is not PENDING
  const shouldAnimate = dimension.level !== 'PENDING';

  const getBadgeVariant = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'success';
      case 'MODERATE':
        return 'warning';
      case 'LOW':
        return 'destructive';
      default:
        return 'pending';
    }
  };

  const getIcon = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return <CheckCircle2 className="w-3 h-3" />;
      case 'MODERATE':
        return <AlertCircle className="w-3 h-3" />;
      case 'LOW':
        return <XCircle className="w-3 h-3" />;
      default:
        return <Clock className="w-3 h-3" />;
    }
  };

  const getProgressValue = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 100;
      case 'MODERATE':
        return 60;
      case 'LOW':
        return 30;
      default:
        return 0;
    }
  };

  const getProgressColor = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'bg-gradient-to-r from-confidence-high to-emerald-400';
      case 'MODERATE':
        return 'bg-gradient-to-r from-confidence-moderate to-amber-400';
      case 'LOW':
        return 'bg-gradient-to-r from-confidence-low to-rose-400';
      default:
        return 'bg-text-muted/30';
    }
  };

  return (
    <div className="border-b border-white/[0.05] last:border-b-0">
      <button
        onClick={onToggle}
        className={cn(
          'w-full flex items-center justify-between p-3 transition-colors',
          'hover:bg-white/[0.02]',
          isExpanded && 'bg-white/[0.02]'
        )}
      >
        <div className="flex flex-col items-start gap-1.5 flex-1 mr-3">
          <div className="flex items-center gap-2 w-full">
            <span className="text-sm font-medium text-text-primary">{dimension.label}</span>
            <Badge variant={getBadgeVariant(dimension.level)} className="ml-auto">
              {getIcon(dimension.level)}
              {dimension.level}
            </Badge>
            <ChevronDown
              className={cn(
                'w-3.5 h-3.5 text-text-muted transition-transform duration-200',
                isExpanded && 'rotate-180'
              )}
            />
          </div>
          <Progress
            value={shouldAnimate ? getProgressValue(dimension.level) : 0}
            className="h-1.5 bg-bg-surface"
            indicatorClassName={getProgressColor(dimension.level)}
            duration={1500}
          />
        </div>
      </button>

      {/* Expandable rationale */}
      <div
        className={cn(
          'overflow-hidden transition-all duration-300',
          isExpanded ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
        )}
      >
        <div className="px-3 pb-3">
          <p className="text-xs text-text-muted leading-relaxed">
            {dimension.rationale || 'Awaiting analysis...'}
          </p>
        </div>
      </div>
    </div>
  );
}

interface OverlapScoreSectionProps {
  data: OverlapScoreEvent | null;
}

function OverlapScoreSection({ data }: OverlapScoreSectionProps) {
  // Animation is driven by whether data exists
  const shouldAnimate = !!data;

  const getPercentileColor = (percentile: number) => {
    if (percentile >= 75) return 'bg-gradient-to-r from-confidence-high to-emerald-400';
    if (percentile >= 50) return 'bg-gradient-to-r from-confidence-moderate to-amber-400';
    return 'bg-gradient-to-r from-confidence-low to-rose-400';
  };

  const getBadgeVariant = (percentile: number) => {
    if (percentile >= 75) return 'success';
    if (percentile >= 50) return 'warning';
    return 'destructive';
  };

  return (
    <div className="p-3 border-t border-white/[0.08]">
      <div className="flex items-center gap-2 mb-2">
        <TrendingUp className="w-4 h-4 text-primary" />
        <span className="text-sm font-medium text-text-primary">Spatial Correlation</span>
      </div>

      {data ? (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-2xl font-bold text-text-primary animate-count-up">
              r = {data.r.toFixed(2)}
            </span>
            <Badge variant={getBadgeVariant(data.percentile)}>
              p{data.percentile}
            </Badge>
          </div>
          <Progress
            value={shouldAnimate ? data.percentile : 0}
            className="h-1.5 bg-bg-surface"
            indicatorClassName={getPercentileColor(data.percentile)}
            duration={2000}
          />
          <p className="text-xs text-text-muted">{data.label}</p>
        </div>
      ) : (
        <div className="flex items-center gap-2 text-text-muted">
          <Clock className="w-3.5 h-3.5" />
          <span className="text-xs">Awaiting analysis...</span>
        </div>
      )}
    </div>
  );
}

interface FixedConfidencePanelProps {
  confidence: Record<string, ConfidenceDimension>;
  overlapScore: OverlapScoreEvent | null;
}

export function FixedConfidencePanel({ confidence, overlapScore }: FixedConfidencePanelProps) {
  const [expandedDimension, setExpandedDimension] = useState<string | null>(null);

  const dimensions = Object.values(confidence);

  const handleToggle = (dimensionKey: string) => {
    setExpandedDimension(expandedDimension === dimensionKey ? null : dimensionKey);
  };

  return (
    <div
      className={cn(
        'fixed top-[72px] right-4 w-[280px] z-30',
        'bg-bg-elevated/95 backdrop-blur-xl',
        'border border-white/[0.08] rounded-xl',
        'shadow-xl shadow-black/20',
        'animate-fade-in'
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2 p-3 border-b border-white/[0.08]">
        <Shield className="w-4 h-4 text-primary" />
        <span className="text-sm font-semibold text-text-primary">Confidence Metrics</span>
      </div>

      {/* Confidence Dimensions */}
      <div>
        {dimensions.map((dim) => (
          <ConfidenceMetricRow
            key={dim.dimension}
            dimension={dim}
            isExpanded={expandedDimension === dim.dimension}
            onToggle={() => handleToggle(dim.dimension)}
          />
        ))}
      </div>

      {/* Overlap Score Section */}
      <OverlapScoreSection data={overlapScore} />
    </div>
  );
}
