// Query types
export type QueryType = 'name' | 'smiles';

// Demo scenarios
export type DemoScenario = 'alzheimers' | 'schizophrenia' | 'depression';

// Confidence levels
export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW' | 'PENDING';

// Session phases
export type SessionPhase = 'idle' | 'running' | 'complete' | 'error';

// Trace event types
export type TraceEventType =
  | 'agent_thought'
  | 'tool_call'
  | 'tool_result'
  | 'brain_map'
  | 'overlap_score'
  | 'confidence_update'
  | 'report_ready'
  | 'pdf_ready'
  | 'error'
  | 'done';

// Base event interface
interface BaseEvent {
  timestamp: number;
}

// Agent thought event
export interface AgentThoughtEvent extends BaseEvent {
  type: 'agent_thought';
  content: string;
}

// Tool call event
export interface ToolCallEvent extends BaseEvent {
  type: 'tool_call';
  tool: string;
  input: Record<string, unknown>;
}

// Tool result event
export interface ToolResultEvent extends BaseEvent {
  type: 'tool_result';
  tool: string;
  summary: string;
}

// Brain region data
export interface BrainRegion {
  region: string;
  percentile?: number;
  value?: number;
}

// Brain map event
export interface BrainMapEvent extends BaseEvent {
  type: 'brain_map';
  map_type: 'expression' | 'disease';
  image_url: string;
  top_regions: BrainRegion[];
}

// Overlap score event
export interface OverlapScoreEvent extends BaseEvent {
  type: 'overlap_score';
  r: number;
  percentile: number;
  label: string;
}

// Confidence dimension types
export type ConfidenceDimensionType =
  | 'target_resolution'
  | 'circuit_alignment'
  | 'literature_support';

// Confidence update event
export interface ConfidenceUpdateEvent extends BaseEvent {
  type: 'confidence_update';
  dimension: ConfidenceDimensionType;
  level: ConfidenceLevel;
  rationale: string;
}

// Report sections
export interface ReportSections {
  executive_summary?: string;
  target_identification?: string;
  expression_analysis?: string;
  spatial_overlap?: string;
  circuit_interpretation?: string;
  off_target_risk?: string;
  literature_context?: string;
  confidence_assessment?: string;
  limitations?: string;
  recommendations?: string;
  preclinical_validation?: string;

  // Legacy/demo-only keys kept for backwards compatibility.
  disease_anatomy?: string;
  references?: string;
}

// Report ready event
export interface ReportReadyEvent extends BaseEvent {
  type: 'report_ready';
  report_sections: ReportSections;
}

// PDF ready event
export interface PdfReadyEvent extends BaseEvent {
  type: 'pdf_ready';
  pdf_url: string;
  filename: string;
}

// Error event
export interface ErrorEvent extends BaseEvent {
  type: 'error';
  message: string;
  recoverable: boolean;
}

// Done event
export interface DoneEvent extends BaseEvent {
  type: 'done';
}

// Union type for all trace events
export type TraceEvent =
  | AgentThoughtEvent
  | ToolCallEvent
  | ToolResultEvent
  | BrainMapEvent
  | OverlapScoreEvent
  | ConfidenceUpdateEvent
  | ReportReadyEvent
  | PdfReadyEvent
  | ErrorEvent
  | DoneEvent;

// Confidence dimension with full data
export interface ConfidenceDimension {
  dimension: ConfidenceDimensionType;
  label: string;
  level: ConfidenceLevel;
  rationale: string;
}

// Session state interface
export interface SessionState {
  sessionId: string | null;
  phase: SessionPhase;
  isDemo: boolean;
  drugQuery: string;
  queryType: QueryType;
  indication: string;
  traceEvents: TraceEvent[];
  expressionMap: BrainMapEvent | null;
  diseaseMap: BrainMapEvent | null;
  overlapScore: OverlapScoreEvent | null;
  confidence: Record<ConfidenceDimensionType, ConfidenceDimension>;
  reportSections: ReportSections | null;
  pdfUrl: string | null;
  error: string | null;
}

// API request/response types
export interface ValidateRequest {
  drug_query: string;
  query_type: QueryType;
  indication: string;
}

export interface ValidateResponse {
  session_id: string;
  stream_url: string;
  mode: 'live';
}

export interface DemoResponse {
  session_id: string;
  mode: 'demo';
  events: TraceEvent[];
  drug_query: string;
  query_type: QueryType;
  indication: string;
  expression_map_url?: string;
  disease_map_url?: string;
}

// Disease indication options
export const DISEASE_INDICATIONS = [
  "Alzheimer's disease",
  "Parkinson's disease",
  "Schizophrenia",
  "Major depressive disorder",
  "Bipolar disorder",
  "PTSD",
  "Epilepsy",
  "ALS",
  "Huntington's disease",
  "Treatment-resistant depression",
  "Anxiety disorders",
  "Frontotemporal dementia",
] as const;

export type DiseaseIndication = (typeof DISEASE_INDICATIONS)[number];
