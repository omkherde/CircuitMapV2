import { clsx } from 'clsx';
import type { OverlapScoreEvent } from '../types';

interface OverlapScoreProps {
  data: OverlapScoreEvent | null;
}

export function OverlapScore({ data }: OverlapScoreProps) {
  const getPercentileColor = (percentile: number) => {
    if (percentile >= 75) return 'bg-green-500';
    if (percentile >= 50) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const getBadgeColor = (percentile: number) => {
    if (percentile >= 75) return 'bg-green-100 text-green-800';
    if (percentile >= 50) return 'bg-amber-100 text-amber-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
          Spatial Overlap
        </h2>
      </div>

      <div className="p-4">
        {!data ? (
          <div className="text-center text-gray-400 text-sm py-4">
            Awaiting overlap calculation...
          </div>
        ) : (
          <div className="flex flex-col gap-4">
            {/* R value display */}
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-semibold text-gray-900">
                r = {data.r.toFixed(2)}
              </span>
              <span
                className={clsx(
                  'px-2 py-0.5 text-sm font-medium rounded-full',
                  getBadgeColor(data.percentile)
                )}
              >
                p{data.percentile}
              </span>
            </div>

            {/* Label */}
            <p className="text-sm text-gray-600">{data.label}</p>

            {/* Animated bar */}
            <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={clsx(
                  'h-full rounded-full transition-all duration-500 ease-out',
                  getPercentileColor(data.percentile)
                )}
                style={{
                  width: `${data.percentile}%`,
                  animation: 'fillBar 500ms ease-out forwards',
                }}
              />
            </div>

            {/* Percentile markers */}
            <div className="flex justify-between text-xs text-gray-400">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
