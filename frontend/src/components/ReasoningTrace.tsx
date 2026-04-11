import { useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import type { TraceEvent, SessionPhase } from '../types';
import { TraceEntry } from './TraceEntry';

interface ReasoningTraceProps {
  events: TraceEvent[];
  phase: SessionPhase;
}

export function ReasoningTrace({ events, phase }: ReasoningTraceProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length]);

  const isThinking = phase === 'running';

  return (
    <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
          Reasoning Trace
        </h2>
        {isThinking && (
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse-dot" />
            <span className="text-xs text-gray-500">Thinking...</span>
          </div>
        )}
      </div>

      <div
        ref={containerRef}
        className={clsx(
          'flex-1 overflow-y-auto p-2',
          'min-h-[320px] max-h-[320px]'
        )}
      >
        {events.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            {phase === 'idle'
              ? 'Start a validation to see reasoning trace'
              : 'Waiting for events...'}
          </div>
        ) : (
          <div className="flex flex-col">
            {events.map((event, index) => (
              <TraceEntry key={`${event.type}-${index}`} event={event} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
    </div>
  );
}
