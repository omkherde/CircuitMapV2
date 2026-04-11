import { clsx } from 'clsx';
import type { TraceEvent } from '../types';

interface TraceEntryProps {
  event: TraceEvent;
}

export function TraceEntry({ event }: TraceEntryProps) {
  const getContent = (): React.ReactNode => {
    switch (event.type) {
      case 'agent_thought':
        return (
          <span className="text-gray-700">{event.content}</span>
        );

      case 'tool_call':
        return (
          <span className="font-mono text-sm text-blue-700">
            <span className="font-semibold">{event.tool}</span>
            <span className="text-blue-500">({JSON.stringify(event.input)})</span>
          </span>
        );

      case 'tool_result':
        return (
          <span className="font-mono text-sm text-green-700">
            <span className="font-semibold">{event.tool}</span>
            <span className="text-green-600"> → {event.summary}</span>
          </span>
        );

      case 'confidence_update':
        return (
          <span
            className={clsx(
              'text-sm',
              event.level === 'HIGH' && 'text-green-700',
              event.level === 'MODERATE' && 'text-amber-700',
              event.level === 'LOW' && 'text-red-700',
              event.level === 'PENDING' && 'text-gray-500'
            )}
          >
            <span className="font-medium">{event.dimension}:</span> {event.level}
          </span>
        );

      case 'brain_map':
        return (
          <span className="text-sm text-purple-700">
            Brain map ready: {event.map_type}
          </span>
        );

      case 'overlap_score':
        return (
          <span className="text-sm text-indigo-700">
            Overlap calculated: r = {event.r.toFixed(2)} (p{event.percentile})
          </span>
        );

      case 'report_ready':
        return (
          <span className="text-sm text-emerald-700 font-medium">
            Report ready
          </span>
        );

      case 'pdf_ready':
        return (
          <span className="text-sm text-emerald-700 font-medium">
            PDF ready for download
          </span>
        );

      case 'error':
        return (
          <span className="text-sm text-red-600 font-medium">
            Error: {event.message}
          </span>
        );

      default:
        return null;
    }
  };

  const content = getContent();
  if (!content) return null;

  return (
    <div className="animate-fade-in py-1.5 px-2 border-l-2 border-transparent hover:border-gray-300 hover:bg-gray-50">
      {content}
    </div>
  );
}
