import { useEffect, useRef } from 'react';
import { Activity, MessageSquare } from 'lucide-react';
import type { TraceEvent, SessionPhase } from '../types';
import { TraceEntry } from './TraceEntry';
import { Card, CardHeader } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ReasoningTraceProps {
  events: TraceEvent[];
  phase: SessionPhase;
}

export function ReasoningTrace({ events, phase }: ReasoningTraceProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length]);

  const isThinking = phase === 'running';

  return (
    <Card className="overflow-hidden animate-fade-in">
      <CardHeader className="py-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-trace-thought to-violet-600 flex items-center justify-center">
            <Activity className="w-3.5 h-3.5 text-bg-base" />
          </div>
          <h2 className="text-sm font-semibold text-text-primary uppercase tracking-wide">
            Reasoning Trace
          </h2>
        </div>
        {isThinking && (
          <div className="flex items-center gap-2 px-2.5 py-1 bg-primary/10 rounded-full border border-primary/30">
            <div className="w-2 h-2 bg-primary rounded-full animate-pulse-dot" />
            <span className="text-xs font-medium text-primary">Thinking...</span>
          </div>
        )}
      </CardHeader>

      {/* Content */}
      <ScrollArea className="h-[320px]">
        <div className="p-4">
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-[280px] gap-3 text-text-muted">
              <div className="w-12 h-12 rounded-full bg-bg-surface flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-text-muted" />
              </div>
              <p className="text-sm text-center">
                {phase === 'idle'
                  ? 'Start a validation to see reasoning trace'
                  : 'Waiting for events...'}
              </p>
            </div>
          ) : (
            <div className="flex flex-col">
              {events.map((event, index) => (
                <TraceEntry
                  key={`${event.type}-${index}`}
                  event={event}
                  isLast={index === events.length - 1}
                />
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>
      </ScrollArea>
    </Card>
  );
}
