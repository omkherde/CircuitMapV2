import { useState } from 'react';
import { Shield, ChevronDown, CheckCircle2, AlertCircle, XCircle, Clock } from 'lucide-react';
import type { ConfidenceDimension, ConfidenceLevel } from '../types';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

interface ConfidenceMetricRowProps {
  dimension: ConfidenceDimension;
  isExpanded: boolean;
  onToggle: () => void;
}

function ConfidenceMetricRow({ dimension, isExpanded, onToggle }: ConfidenceMetricRowProps) {
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

interface SidebarConfidencePanelProps {
  confidence: Record<string, ConfidenceDimension>;
}

export function SidebarConfidencePanel({ confidence }: SidebarConfidencePanelProps) {
  const [expandedDimension, setExpandedDimension] = useState<string | null>(null);

  const dimensions = Object.values(confidence);

  const handleToggle = (dimensionKey: string) => {
    setExpandedDimension(expandedDimension === dimensionKey ? null : dimensionKey);
  };

  return (
    <Card className="animate-fade-in">
      {/* Header */}
      <CardHeader className="py-3 flex flex-row items-center gap-2">
        <Shield className="w-4 h-4 text-primary" />
        <span className="text-sm font-semibold text-text-primary">Confidence Metrics</span>
      </CardHeader>

      {/* Confidence Dimensions */}
      <CardContent className="p-0">
        {dimensions.map((dim) => (
          <ConfidenceMetricRow
            key={dim.dimension}
            dimension={dim}
            isExpanded={expandedDimension === dim.dimension}
            onToggle={() => handleToggle(dim.dimension)}
          />
        ))}
      </CardContent>
    </Card>
  );
}
