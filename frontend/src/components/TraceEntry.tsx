import {
  Brain,
  Wrench,
  CheckCircle2,
  Gauge,
  MapPin,
  BarChart3,
  FileText,
  Download,
  AlertCircle
} from 'lucide-react';
import type { TraceEvent } from '../types';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';

interface TraceEntryProps {
  event: TraceEvent;
  isLast?: boolean;
}

export function TraceEntry({ event, isLast = false }: TraceEntryProps) {
  const getIcon = () => {
    switch (event.type) {
      case 'agent_thought':
        return <Brain className="w-4 h-4" />;
      case 'tool_call':
        return <Wrench className="w-4 h-4" />;
      case 'tool_result':
        return <CheckCircle2 className="w-4 h-4" />;
      case 'confidence_update':
        return <Gauge className="w-4 h-4" />;
      case 'brain_map':
        return <MapPin className="w-4 h-4" />;
      case 'overlap_score':
        return <BarChart3 className="w-4 h-4" />;
      case 'report_ready':
        return <FileText className="w-4 h-4" />;
      case 'pdf_ready':
        return <Download className="w-4 h-4" />;
      case 'error':
        return <AlertCircle className="w-4 h-4" />;
      default:
        return <Brain className="w-4 h-4" />;
    }
  };

  const getDotClass = () => {
    switch (event.type) {
      case 'agent_thought':
        return 'timeline-dot-thought';
      case 'tool_call':
        return 'timeline-dot-tool';
      case 'tool_result':
        return 'timeline-dot-result';
      case 'confidence_update':
        return 'timeline-dot-confidence';
      case 'brain_map':
        return 'timeline-dot-map';
      case 'overlap_score':
        return 'timeline-dot-score';
      case 'report_ready':
      case 'pdf_ready':
        return 'timeline-dot-complete';
      case 'error':
        return 'timeline-dot-error';
      default:
        return 'timeline-dot-thought';
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
          <p className="text-sm text-slate-700 leading-relaxed">
            {event.content}
          </p>
        );

      case 'tool_call':
        return (
          <div className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-blue-700">
              {event.tool}
            </span>
            <code className="text-xs text-blue-600/80 bg-blue-50 px-2 py-1 rounded font-mono break-all">
              {JSON.stringify(event.input)}
            </code>
          </div>
        );

      case 'tool_result':
        return (
          <div className="flex flex-col gap-1">
            <span className="text-sm font-semibold text-emerald-700">
              {event.tool}
            </span>
            <span className="text-sm text-emerald-600">
              {event.summary}
            </span>
          </div>
        );

      case 'confidence_update':
        return (
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-slate-700">
              {event.dimension}:
            </span>
            <Badge variant={getBadgeVariant(event.level)}>
              {event.level}
            </Badge>
          </div>
        );

      case 'brain_map':
        return (
          <span className="text-sm text-purple-700 font-medium">
            Brain map generated: <span className="text-purple-600">{event.map_type}</span>
          </span>
        );

      case 'overlap_score':
        return (
          <div className="flex items-center gap-2">
            <span className="text-sm text-indigo-700 font-medium">
              Overlap calculated:
            </span>
            <span className="text-sm font-mono font-semibold text-indigo-600">
              r = {event.r.toFixed(2)}
            </span>
            <Badge variant="pending">
              p{event.percentile}
            </Badge>
          </div>
        );

      case 'report_ready':
        return (
          <span className="text-sm text-emerald-700 font-semibold">
            Validation report ready
          </span>
        );

      case 'pdf_ready':
        return (
          <span className="text-sm text-emerald-700 font-semibold">
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
    <div className="flex gap-3 animate-slide-in">
      {/* Timeline dot and line */}
      <div className="flex flex-col items-center">
        <div className={cn('timeline-dot', getDotClass())}>
          {getIcon()}
        </div>
        {!isLast && (
          <div className="w-0.5 flex-1 min-h-[8px] bg-gradient-to-b from-slate-200 to-slate-100" />
        )}
      </div>

      {/* Content */}
      <div className="flex-1 pb-3 pt-1">
        {content}
      </div>
    </div>
  );
}
