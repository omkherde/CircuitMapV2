import { useState } from 'react';
import { Shield, ChevronDown, CheckCircle2, AlertCircle, XCircle, Clock } from 'lucide-react';
import type { ConfidenceDimension, ConfidenceLevel } from '../types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface ConfidenceBadgeProps {
  confidence: Record<string, ConfidenceDimension>;
}

export function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const [showBreakdown, setShowBreakdown] = useState(false);

  const dimensions = Object.values(confidence);
  const hasAnyUpdate = dimensions.some((d) => d.level !== 'PENDING');

  // Calculate overall confidence
  const getOverallLevel = (): ConfidenceLevel => {
    const levels = dimensions.map(d => d.level);
    if (levels.every(l => l === 'PENDING')) return 'PENDING';
    if (levels.every(l => l === 'HIGH')) return 'HIGH';
    if (levels.some(l => l === 'LOW')) return 'LOW';
    return 'MODERATE';
  };

  const overallLevel = getOverallLevel();

  const getGlowClass = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'glow-confidence-high';
      case 'MODERATE':
        return 'glow-confidence-moderate';
      case 'LOW':
        return 'glow-confidence-low';
      default:
        return '';
    }
  };

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
        return <CheckCircle2 className="w-3.5 h-3.5" />;
      case 'MODERATE':
        return <AlertCircle className="w-3.5 h-3.5" />;
      case 'LOW':
        return <XCircle className="w-3.5 h-3.5" />;
      default:
        return <Clock className="w-3.5 h-3.5" />;
    }
  };

  if (!hasAnyUpdate) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 bg-bg-surface rounded-full border border-white/[0.08]">
        <Shield className="w-4 h-4 text-text-muted" />
        <span className="text-sm text-text-muted">Awaiting analysis</span>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Main Badge Button */}
      <button
        onClick={() => setShowBreakdown(!showBreakdown)}
        className={cn(
          'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all duration-300',
          'hover:scale-105 active:scale-100',
          overallLevel === 'HIGH' && 'bg-confidence-high/10 border-confidence-high/30 text-confidence-high',
          overallLevel === 'MODERATE' && 'bg-confidence-moderate/10 border-confidence-moderate/30 text-confidence-moderate',
          overallLevel === 'LOW' && 'bg-confidence-low/10 border-confidence-low/30 text-confidence-low',
          overallLevel === 'PENDING' && 'bg-bg-surface border-white/[0.08] text-text-muted',
          getGlowClass(overallLevel)
        )}
      >
        <Shield className="w-4 h-4" />
        <span className="text-sm font-semibold">{overallLevel}</span>
        <ChevronDown className={cn(
          'w-3.5 h-3.5 transition-transform duration-200',
          showBreakdown && 'rotate-180'
        )} />
      </button>

      {/* Breakdown Dropdown */}
      {showBreakdown && (
        <div className={cn(
          'absolute top-full right-0 mt-2 w-72',
          'bg-bg-elevated border border-white/[0.08] rounded-xl shadow-xl',
          'animate-fade-in-scale z-50'
        )}>
          <div className="p-3 border-b border-white/[0.08]">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-primary" />
              <span className="text-sm font-semibold text-text-primary">Confidence Breakdown</span>
            </div>
          </div>

          <div className="p-2">
            {dimensions.map((dim) => (
              <div
                key={dim.dimension}
                className={cn(
                  'flex items-center justify-between p-2 rounded-lg',
                  'hover:bg-bg-surface-hover transition-colors'
                )}
              >
                <span className="text-sm text-text-secondary">{dim.label}</span>
                <Badge variant={getBadgeVariant(dim.level)}>
                  {getIcon(dim.level)}
                  {dim.level}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {showBreakdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowBreakdown(false)}
        />
      )}
    </div>
  );
}
