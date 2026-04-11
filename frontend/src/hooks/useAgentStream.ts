import { useEffect, useRef, useCallback } from 'react';
import type { TraceEvent, TraceEventType } from '../types';
import { getStreamUrl } from '../api/client';

interface UseAgentStreamOptions {
  sessionId: string | null;
  enabled: boolean;
  onEvent: (event: TraceEvent) => void;
  onError: (error: string) => void;
  onComplete: () => void;
}

export function useAgentStream({
  sessionId,
  enabled,
  onEvent,
  onError,
  onComplete,
}: UseAgentStreamOptions) {
  const eventSourceRef = useRef<EventSource | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const cleanup = useCallback(() => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled || !sessionId) {
      cleanup();
      return;
    }

    const url = getStreamUrl(sessionId);
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    // All SSE event types we listen for
    const eventTypes: TraceEventType[] = [
      'agent_thought',
      'tool_call',
      'tool_result',
      'brain_map',
      'overlap_score',
      'confidence_update',
      'report_ready',
      'pdf_ready',
      'error',
      'done',
    ];

    // Create event handlers for each type
    const handlers: Record<string, (e: MessageEvent) => void> = {};

    for (const eventType of eventTypes) {
      handlers[eventType] = (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          const event: TraceEvent = {
            ...data,
            type: eventType,
            timestamp: data.timestamp || Date.now(),
          };

          if (eventType === 'done') {
            onComplete();
            cleanup();
          } else if (eventType === 'error') {
            onError(data.message || 'Unknown error');
            if (!data.recoverable) {
              cleanup();
            }
          } else {
            onEvent(event);
          }
        } catch (err) {
          console.error(`Failed to parse SSE event (${eventType}):`, err);
        }
      };

      eventSource.addEventListener(eventType, handlers[eventType]);
    }

    // Handle connection errors
    eventSource.onerror = () => {
      if (eventSource.readyState === EventSource.CLOSED) {
        cleanup();
        return;
      }
      onError('Connection to server lost');
      cleanup();
    };

    // Store cleanup function
    cleanupRef.current = () => {
      for (const eventType of eventTypes) {
        eventSource.removeEventListener(eventType, handlers[eventType]);
      }
    };

    return cleanup;
  }, [sessionId, enabled, onEvent, onError, onComplete, cleanup]);

  return { cleanup };
}
