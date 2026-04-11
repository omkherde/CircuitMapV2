import { GitCompareArrows, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import type { OverlapScoreEvent } from '../types';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface OverlapScoreProps {
  data: OverlapScoreEvent | null;
}

export function OverlapScore({ data }: OverlapScoreProps) {
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

  const getTrendIcon = (percentile: number) => {
    if (percentile >= 75) return <TrendingUp className="w-4 h-4" />;
    if (percentile >= 50) return <Minus className="w-4 h-4" />;
    return <TrendingDown className="w-4 h-4" />;
  };

  const getInterpretation = (percentile: number) => {
    if (percentile >= 75) return 'Strong anatomical alignment';
    if (percentile >= 50) return 'Moderate anatomical alignment';
    return 'Weak anatomical alignment';
  };

  return (
    <Card className="overflow-hidden animate-fade-in">
      <CardHeader className="py-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
            <GitCompareArrows className="w-3.5 h-3.5 text-bg-base" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wide">
            Spatial Overlap
          </h2>
        </div>
      </CardHeader>

      <CardContent>
        {!data ? (
          // Empty state
          <div className="flex flex-col items-center justify-center py-6 gap-3">
            <div className="w-12 h-12 rounded-full bg-bg-surface flex items-center justify-center">
              <GitCompareArrows className="w-6 h-6 text-text-muted" />
            </div>
            <p className="text-sm text-text-muted text-center">
              Awaiting overlap calculation...
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-4 animate-fade-in-scale">
            {/* Main score display */}
            <div className="flex items-center justify-between">
              <div className="flex items-baseline gap-3">
                <span className="text-4xl font-bold text-text-primary animate-count-up">
                  r = {data.r.toFixed(2)}
                </span>
                <Badge variant={getBadgeVariant(data.percentile)}>
                  p{data.percentile}
                </Badge>
              </div>
              <div className={cn(
                'w-10 h-10 rounded-full flex items-center justify-center',
                data.percentile >= 75 ? 'bg-confidence-high/10 text-confidence-high' :
                data.percentile >= 50 ? 'bg-confidence-moderate/10 text-confidence-moderate' :
                'bg-confidence-low/10 text-confidence-low'
              )}>
                {getTrendIcon(data.percentile)}
              </div>
            </div>

            {/* Interpretation */}
            <p className="text-sm text-text-secondary font-medium">
              {getInterpretation(data.percentile)}
            </p>

            {/* Label */}
            <p className="text-sm text-text-muted">{data.label}</p>

            {/* Progress bar */}
            <div className="space-y-2">
              <Progress
                value={data.percentile}
                className="h-3"
                indicatorClassName={cn('bg-gradient-to-r', getPercentileColor(data.percentile))}
              />

              {/* Percentile markers */}
              <div className="flex justify-between text-xs text-text-muted">
                <span>0%</span>
                <span className="text-text-secondary font-medium">50%</span>
                <span>100%</span>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
