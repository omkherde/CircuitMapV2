import { Shield, ChevronRight, CheckCircle2, AlertCircle, XCircle, Clock } from 'lucide-react';
import type { ConfidenceDimension, ConfidenceLevel } from '../types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface ConfidenceRowProps {
  dimension: ConfidenceDimension;
  index: number;
}

function ConfidenceRow({ dimension, index }: ConfidenceRowProps) {
  const getBadgeVariant = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'success';
      case 'MODERATE':
        return 'warning';
      case 'LOW':
        return 'destructive';
      case 'PENDING':
      default:
        return 'pending';
    }
  };

  const getIcon = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return <CheckCircle2 className="w-3.5 h-3.5" />;
      case 'MODERATE':
        return <AlertCircle className="w-3.5 h-3.5" />;
      case 'LOW':
        return <XCircle className="w-3.5 h-3.5" />;
      case 'PENDING':
      default:
        return <Clock className="w-3.5 h-3.5" />;
    }
  };

  const getProgressColor = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'from-confidence-high to-emerald-400';
      case 'MODERATE':
        return 'from-confidence-moderate to-amber-400';
      case 'LOW':
        return 'from-confidence-low to-rose-400';
      case 'PENDING':
      default:
        return 'from-bg-surface to-bg-elevated';
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
      case 'PENDING':
      default:
        return 0;
    }
  };

  return (
    <div
      className={cn(
        'flex flex-col gap-2 py-3 animate-fade-in',
        `stagger-${Math.min(index + 1, 5)}`
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ChevronRight className="w-3 h-3 text-text-muted" />
          <span className="text-sm font-medium text-text-secondary">{dimension.label}</span>
        </div>
        <Badge variant={getBadgeVariant(dimension.level)}>
          {getIcon(dimension.level)}
          {dimension.level}
        </Badge>
      </div>

      {/* Mini progress bar */}
      <div className="ml-5">
        <Progress
          value={getProgressValue(dimension.level)}
          className="h-1"
          indicatorClassName={cn('bg-gradient-to-r', getProgressColor(dimension.level))}
        />
      </div>

      {dimension.rationale && (
        <p className="text-xs text-text-muted leading-relaxed ml-5 mt-1">
          {dimension.rationale}
        </p>
      )}
    </div>
  );
}

interface ConfidencePanelProps {
  confidence: Record<string, ConfidenceDimension>;
}

export function ConfidencePanel({ confidence }: ConfidencePanelProps) {
  const dimensions = Object.values(confidence);
  const hasAnyUpdate = dimensions.some((d) => d.level !== 'PENDING');

  // Calculate overall confidence
  const getOverallLevel = (): ConfidenceLevel => {
    const levels = dimensions.map(d => d.level);
    if (levels.some(l => l === 'PENDING')) return 'PENDING';
    if (levels.every(l => l === 'HIGH')) return 'HIGH';
    if (levels.some(l => l === 'LOW')) return 'LOW';
    return 'MODERATE';
  };

  const overallLevel = getOverallLevel();

  const getBadgeVariant = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'success';
      case 'MODERATE':
        return 'warning';
      case 'LOW':
        return 'destructive';
      case 'PENDING':
      default:
        return 'pending';
    }
  };

  return (
    <Card className="overflow-hidden animate-fade-in">
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-confidence-moderate to-amber-400 flex items-center justify-center">
              <Shield className="w-3.5 h-3.5 text-bg-base" />
            </div>
            <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wide">
              Confidence
            </h2>
          </div>
          {hasAnyUpdate && (
            <Badge variant={getBadgeVariant(overallLevel)}>
              {overallLevel}
            </Badge>
          )}
        </div>
      </CardHeader>

      <CardContent className="px-4 py-0">
        {!hasAnyUpdate ? (
          <div className="py-6 text-center">
            <div className="w-10 h-10 mx-auto rounded-full bg-bg-surface flex items-center justify-center mb-2">
              <Clock className="w-5 h-5 text-text-muted" />
            </div>
            <p className="text-sm text-text-muted">
              Awaiting confidence assessment...
            </p>
          </div>
        ) : (
          <div className="divide-y divide-white/[0.08]">
            {dimensions.map((dim, index) => (
              <ConfidenceRow key={dim.dimension} dimension={dim} index={index} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
