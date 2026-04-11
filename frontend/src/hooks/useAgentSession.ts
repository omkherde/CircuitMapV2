import { useState, useCallback, useRef } from 'react';
import type {
  SessionState,
  TraceEvent,
  ConfidenceDimensionType,
  ConfidenceDimension,
  QueryType,
  DemoScenario,
  BrainMapEvent,
  OverlapScoreEvent,
  ConfidenceUpdateEvent,
  ReportReadyEvent,
  PdfReadyEvent,
} from '../types';
import { startValidation, loadDemoData } from '../api/client';
import { useAgentStream } from './useAgentStream';
import { demoScenarios } from '../mocks/demoEvents';

const initialConfidence: Record<ConfidenceDimensionType, ConfidenceDimension> = {
  target_resolution: {
    dimension: 'target_resolution',
    label: 'Target Resolution',
    level: 'PENDING',
    rationale: '',
  },
  circuit_alignment: {
    dimension: 'circuit_alignment',
    label: 'Circuit Alignment',
    level: 'PENDING',
    rationale: '',
  },
  literature_support: {
    dimension: 'literature_support',
    label: 'Literature Support',
    level: 'PENDING',
    rationale: '',
  },
};

const initialState: SessionState = {
  sessionId: null,
  phase: 'idle',
  isDemo: false,
  drugQuery: '',
  queryType: 'name',
  indication: '',
  traceEvents: [],
  expressionMap: null,
  diseaseMap: null,
  overlapScore: null,
  confidence: { ...initialConfidence },
  reportSections: null,
  pdfUrl: null,
  error: null,
};

// Demo scenario metadata — must match backend scripts/precompute_demo.py
const demoMetadata: Record<DemoScenario, { drugQuery: string; queryType: QueryType; indication: string }> = {
  alzheimers: {
    drugQuery: 'Chaetocin',
    queryType: 'name',
    indication: "Alzheimer's disease",
  },
  schizophrenia: {
    drugQuery: 'Tolcapone',
    queryType: 'name',
    indication: 'Schizophrenia',
  },
  depression: {
    drugQuery: 'Vorinostat',
    queryType: 'name',
    indication: 'Major depressive disorder',
  },
};

export function useAgentSession() {
  const [state, setState] = useState<SessionState>(initialState);
  const demoTimeoutRef = useRef<number | null>(null);
  const demoEventsRef = useRef<TraceEvent[]>([]);
  const demoIndexRef = useRef<number>(0);

  // Handle incoming events
  const handleEvent = useCallback((event: TraceEvent) => {
    setState((prev) => {
      const newState = { ...prev };

      // Merge consecutive agent_thought chunks into one entry so the trace
      // doesn't fill up with hundreds of tiny fragments from the SSE stream.
      if (event.type === 'agent_thought') {
        const last = prev.traceEvents[prev.traceEvents.length - 1];
        if (last?.type === 'agent_thought') {
          const merged = { ...last, content: last.content + event.content };
          newState.traceEvents = [...prev.traceEvents.slice(0, -1), merged];
        } else {
          newState.traceEvents = [...prev.traceEvents, event];
        }
        return newState;
      }

      newState.traceEvents = [...prev.traceEvents, event];

      switch (event.type) {
        case 'brain_map': {
          const mapEvent = event as BrainMapEvent;
          if (mapEvent.map_type === 'expression') {
            newState.expressionMap = mapEvent;
          } else {
            newState.diseaseMap = mapEvent;
          }
          break;
        }
        case 'overlap_score':
          newState.overlapScore = event as OverlapScoreEvent;
          break;
        case 'confidence_update': {
          const confEvent = event as ConfidenceUpdateEvent;
          newState.confidence = {
            ...prev.confidence,
            [confEvent.dimension]: {
              dimension: confEvent.dimension,
              label: prev.confidence[confEvent.dimension].label,
              level: confEvent.level,
              rationale: confEvent.rationale,
            },
          };
          break;
        }
        case 'report_ready': {
          const reportEvent = event as ReportReadyEvent;
          newState.reportSections = reportEvent.report_sections;
          break;
        }
        case 'pdf_ready': {
          const pdfEvent = event as PdfReadyEvent;
          newState.pdfUrl = pdfEvent.pdf_url;
          break;
        }
      }

      return newState;
    });
  }, []);

  // Handle errors
  const handleError = useCallback((message: string) => {
    setState((prev) => ({
      ...prev,
      phase: 'error',
      error: message,
    }));
  }, []);

  // Handle completion
  const handleComplete = useCallback(() => {
    setState((prev) => ({
      ...prev,
      phase: 'complete',
    }));
  }, []);

  // Use the SSE stream hook
  useAgentStream({
    sessionId: state.sessionId,
    enabled: state.phase === 'running' && !state.isDemo,
    onEvent: handleEvent,
    onError: handleError,
    onComplete: handleComplete,
  });

  // Play demo events at 800ms intervals
  const playDemoEvents = useCallback(() => {
    const playNext = () => {
      if (demoIndexRef.current >= demoEventsRef.current.length) {
        handleComplete();
        return;
      }

      const event = demoEventsRef.current[demoIndexRef.current];
      demoIndexRef.current++;

      if (event.type === 'done') {
        handleComplete();
        return;
      }

      handleEvent(event);
      demoTimeoutRef.current = window.setTimeout(playNext, 800);
    };

    playNext();
  }, [handleEvent, handleComplete]);

  // Start a new validation session
  const startSession = useCallback(
    async (drugQuery: string, queryType: QueryType, indication: string) => {
      // Reset state
      setState({
        ...initialState,
        drugQuery,
        queryType,
        indication,
        phase: 'running',
      });

      try {
        const response = await startValidation({
          drug_query: drugQuery,
          query_type: queryType,
          indication,
        });

        setState((prev) => ({
          ...prev,
          sessionId: response.session_id,
        }));
      } catch (err) {
        handleError(err instanceof Error ? err.message : 'Failed to start session');
      }
    },
    [handleError]
  );

  // Load and play demo - with fallback to local mock data
  const loadDemo = useCallback(
    async (scenario: DemoScenario) => {
      // Clear any existing demo timeout
      if (demoTimeoutRef.current) {
        clearTimeout(demoTimeoutRef.current);
      }

      const metadata = demoMetadata[scenario];

      setState({
        ...initialState,
        phase: 'running',
        isDemo: true,
        drugQuery: metadata.drugQuery,
        queryType: metadata.queryType,
        indication: metadata.indication,
      });

      try {
        // Try to load from API first
        const response = await loadDemoData(scenario);

        setState((prev) => ({
          ...prev,
          sessionId: response.session_id,
          drugQuery: response.drug_query,
          queryType: response.query_type,
          indication: response.indication,
        }));

        // Store demo events and start playback
        demoEventsRef.current = response.events;
        demoIndexRef.current = 0;
        playDemoEvents();
      } catch {
        // Fall back to local mock data if API is unavailable
        console.log('API unavailable, using local mock data');

        setState((prev) => ({
          ...prev,
          sessionId: `demo-${scenario}-${Date.now()}`,
        }));

        // Use local mock events
        demoEventsRef.current = demoScenarios[scenario];
        demoIndexRef.current = 0;
        playDemoEvents();
      }
    },
    [playDemoEvents]
  );

  // Reset session
  const resetSession = useCallback(() => {
    if (demoTimeoutRef.current) {
      clearTimeout(demoTimeoutRef.current);
    }
    setState(initialState);
  }, []);

  // Update form fields
  const setDrugQuery = useCallback((value: string) => {
    setState((prev) => ({ ...prev, drugQuery: value }));
  }, []);

  const setQueryType = useCallback((value: QueryType) => {
    setState((prev) => ({ ...prev, queryType: value }));
  }, []);

  const setIndication = useCallback((value: string) => {
    setState((prev) => ({ ...prev, indication: value }));
  }, []);

  return {
    state,
    startSession,
    loadDemo,
    resetSession,
    setDrugQuery,
    setQueryType,
    setIndication,
  };
}
