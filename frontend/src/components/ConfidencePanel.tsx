import { clsx } from 'clsx';
import type { ConfidenceDimension, ConfidenceLevel } from '../types';

interface ConfidenceRowProps {
  dimension: ConfidenceDimension;
}

function ConfidenceRow({ dimension }: ConfidenceRowProps) {
  const getBadgeStyle = (level: ConfidenceLevel) => {
    switch (level) {
      case 'HIGH':
        return 'bg-green-100 text-green-800';
      case 'MODERATE':
        return 'bg-amber-100 text-amber-800';
      case 'LOW':
        return 'bg-red-100 text-red-800';
      case 'PENDING':
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <div className="flex flex-col gap-1 py-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700">{dimension.label}</span>
        <span
          className={clsx(
            'px-2 py-0.5 text-xs font-semibold rounded-full',
            getBadgeStyle(dimension.level)
          )}
        >
          {dimension.level}
        </span>
      </div>
      {dimension.rationale && (
        <p className="text-xs text-gray-500 leading-relaxed">{dimension.rationale}</p>
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

  return (
    <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
          Confidence Assessment
        </h2>
      </div>

      <div
        className={clsx(
          'divide-y divide-gray-100 px-4 transition-all duration-300',
          hasAnyUpdate ? 'max-h-96 opacity-100' : 'max-h-12 opacity-50'
        )}
      >
        {!hasAnyUpdate ? (
          <div className="py-3 text-center text-gray-400 text-sm">
            Awaiting confidence assessment...
          </div>
        ) : (
          dimensions.map((dim) => (
            <ConfidenceRow key={dim.dimension} dimension={dim} />
          ))
        )}
      </div>
    </div>
  );
}
