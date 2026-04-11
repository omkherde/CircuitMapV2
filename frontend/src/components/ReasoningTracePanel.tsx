import { useEffect, useRef } from 'react';
import { Terminal, ChevronUp, ChevronDown } from 'lucide-react';
import type { TraceEvent, SessionPhase } from '../types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface TraceEntryTerminalProps {
  event: TraceEvent;
}

function TraceEntryTerminal({ event }: TraceEntryTerminalProps) {
  const getPrefix = () => {
    switch (event.type) {
      case 'agent_thought':
        return <span className="text-trace-thought">{'>'}</span>;
      case 'tool_call':
        return <span className="text-trace-tool-call">{'$'}</span>;
      case 'tool_result':
        return <span className="text-trace-tool-result">{'='}</span>;
      case 'confidence_update':
        return <span className="text-confidence-moderate">{'*'}</span>;
      case 'brain_map':
        return <span className="text-accent">{'#'}</span>;
      case 'overlap_score':
        return <span className="text-primary">{'%'}</span>;
      case 'report_ready':
      case 'pdf_ready':
        return <span className="text-confidence-high">{'!'}</span>;
      case 'error':
        return <span className="text-confidence-low">{'!'}</span>;
      default:
        return <span className="text-text-muted">{'>'}</span>;
    }
  };

  const getBadgeVariant = (level: string) => {
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

  const getContent = (): React.ReactNode => {
    switch (event.type) {
      case 'agent_thought':
        return (
          <span className="text-text-secondary">{event.content}</span>
        );

      case 'tool_call':
        return (
          <span>
            <span className="text-trace-tool-call font-semibold">{event.tool}</span>
            <span className="text-text-muted ml-2 font-mono text-xs">
              {JSON.stringify(event.input)}
            </span>
          </span>
        );

      case 'tool_result':
        return (
          <span>
            <span className="text-trace-tool-result font-semibold">{event.tool}</span>
            <span className="text-text-secondary ml-2">{event.summary}</span>
          </span>
        );

      case 'confidence_update':
        return (
          <span className="flex items-center gap-2">
            <span className="text-text-secondary">{event.dimension}</span>
            <Badge variant={getBadgeVariant(event.level)}>
              {event.level}
            </Badge>
          </span>
        );

      case 'brain_map':
        return (
          <span className="text-accent">
            Brain map generated: <span className="text-text-primary">{event.map_type}</span>
          </span>
        );

      case 'overlap_score':
        return (
          <span className="flex items-center gap-2">
            <span className="text-primary">Overlap calculated:</span>
            <span className="font-mono text-text-primary">r = {event.r.toFixed(2)}</span>
            <Badge variant="primary">p{event.percentile}</Badge>
          </span>
        );

      case 'report_ready':
        return (
          <span className="text-confidence-high font-semibold">
            Validation report ready
          </span>
        );

      case 'pdf_ready':
        return (
          <span className="text-confidence-high font-semibold">
            PDF ready for download
          </span>
        );

      case 'error':
        return (
          <span className="text-confidence-low">
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
    <div className="flex gap-2 py-1 font-mono text-sm leading-relaxed animate-fade-in">
      <span className="flex-shrink-0 w-4 text-center">{getPrefix()}</span>
      <div className="flex-1 break-words">{content}</div>
    </div>
  );
}

interface NeuralNetworkBackgroundProps {
  active: boolean;
}

function NeuralNetworkBackground({ active }: NeuralNetworkBackgroundProps) {
  if (!active) return null;

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none opacity-10">
      <svg className="w-full h-full" viewBox="0 0 400 200">
        {/* Neural network nodes */}
        {[0, 1, 2].map((layer) =>
          [0, 1, 2, 3].map((node) => (
            <circle
              key={`${layer}-${node}`}
              cx={80 + layer * 120}
              cy={25 + node * 50}
              r={6}
              className="fill-primary animate-neural-pulse"
              style={{ animationDelay: `${(layer * 4 + node) * 100}ms` }}
            />
          ))
        )}
        {/* Connections */}
        {[0, 1, 2, 3].map((fromNode) =>
          [0, 1, 2, 3].map((toNode) => (
            <line
              key={`0-${fromNode}-${toNode}`}
              x1={86}
              y1={25 + fromNode * 50}
              x2={194}
              y2={25 + toNode * 50}
              className="stroke-primary/30"
              strokeWidth={1}
            />
          ))
        )}
        {[0, 1, 2, 3].map((fromNode) =>
          [0, 1, 2, 3].map((toNode) => (
            <line
              key={`1-${fromNode}-${toNode}`}
              x1={206}
              y1={25 + fromNode * 50}
              x2={314}
              y2={25 + toNode * 50}
              className="stroke-primary/30"
              strokeWidth={1}
            />
          ))
        )}
      </svg>
    </div>
  );
}

interface ReasoningTracePanelProps {
  events: TraceEvent[];
  phase: SessionPhase;
  expanded: boolean;
  onToggle: () => void;
}

export function ReasoningTracePanel({ events, phase, expanded, onToggle }: ReasoningTracePanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const isThinking = phase === 'running';

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events.length]);

  return (
    <div
      className={cn(
        'relative bg-bg-base border-t border-white/[0.08] transition-all duration-300',
        expanded ? 'h-[320px]' : 'h-[160px]'
      )}
    >
      {/* Neural Network Background */}
      <NeuralNetworkBackground active={isThinking} />

      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-bg-elevated border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          {/* Terminal Dots */}
          <div className="flex items-center gap-1.5">
            <div className="w-3 h-3 rounded-full bg-confidence-low" />
            <div className="w-3 h-3 rounded-full bg-confidence-moderate" />
            <div className="w-3 h-3 rounded-full bg-confidence-high" />
          </div>

          <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-primary" />
            <span className="text-sm font-semibold text-text-primary font-mono">
              reasoning_trace
            </span>
          </div>

          {isThinking && (
            <div className="flex items-center gap-2 px-2.5 py-1 bg-primary/10 rounded-full border border-primary/30">
              <div className="w-2 h-2 bg-primary rounded-full animate-pulse-dot" />
              <span className="text-xs font-medium text-primary font-mono">thinking...</span>
            </div>
          )}
        </div>

        <button
          onClick={onToggle}
          className="flex items-center gap-1 px-2 py-1 text-text-muted hover:text-text-primary transition-colors"
        >
          <span className="text-xs font-mono">{expanded ? 'collapse' : 'expand'}</span>
          {expanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronUp className="w-4 h-4" />
          )}
        </button>
      </div>

      {/* Terminal Content */}
      <ScrollArea className={cn(
        'transition-all duration-300',
        expanded ? 'h-[268px]' : 'h-[108px]'
      )}>
        <div className="p-4 font-mono">
          {events.length === 0 ? (
            <div className="flex items-center gap-2 text-text-muted text-sm">
              <span className="text-primary">{'>'}</span>
              <span>
                {phase === 'idle'
                  ? 'awaiting_validation_input...'
                  : 'connecting_to_agent...'}
              </span>
              <span className="animate-terminal-cursor">_</span>
            </div>
          ) : (
            <>
              {events.map((event, index) => (
                <TraceEntryTerminal key={`${event.type}-${index}`} event={event} />
              ))}
              {isThinking && (
                <div className="flex gap-2 py-1 font-mono text-sm">
                  <span className="text-primary">{'>'}</span>
                  <span className="animate-terminal-cursor text-text-primary">_</span>
                </div>
              )}
              <div ref={bottomRef} />
            </>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
