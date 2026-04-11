import { useCallback, useState } from 'react';
import {
  Header,
  InputPanel,
  ReasoningTracePanel,
  BrainVisualizationCenter,
  ReportDrawer,
  Sidebar,
  SidebarConfidencePanel,
} from './components';
import { useAgentSession } from './hooks';
import type { DemoScenario } from './types';
import { AlertCircle, X } from 'lucide-react';

function App() {
  const {
    state,
    startSession,
    loadDemo,
    setDrugQuery,
    setQueryType,
    setIndication,
  } = useAgentSession();

  // Panel state
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [traceExpanded, setTraceExpanded] = useState(false);
  const [reportDrawerOpen, setReportDrawerOpen] = useState(false);

  // Auto-open report drawer when complete
  const handlePhaseChange = useCallback(() => {
    if (state.phase === 'complete' && state.reportSections) {
      setReportDrawerOpen(true);
    }
  }, [state.phase, state.reportSections]);

  // Effect to handle phase changes
  useState(() => {
    handlePhaseChange();
  });

  const handleValidate = useCallback(() => {
    if (state.drugQuery && state.indication) {
      startSession(state.drugQuery, state.queryType, state.indication);
    }
  }, [state.drugQuery, state.queryType, state.indication, startSession]);

  const handleLoadDemo = useCallback(
    (scenario: DemoScenario) => {
      loadDemo(scenario);
    },
    [loadDemo]
  );

  return (
    <div className="min-h-screen bg-bg-base bg-tractography flex flex-col">
      {/* Header */}
      <Header isDemo={state.isDemo} />

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Collapsible Sidebar */}
        <Sidebar
          expanded={sidebarExpanded}
          onToggle={() => setSidebarExpanded(!sidebarExpanded)}
        >
          <div className="flex flex-col gap-4 p-4 h-full">
            <InputPanel
              drugQuery={state.drugQuery}
              queryType={state.queryType}
              indication={state.indication}
              phase={state.phase}
              onDrugQueryChange={setDrugQuery}
              onQueryTypeChange={setQueryType}
              onIndicationChange={setIndication}
              onValidate={handleValidate}
              onLoadDemo={handleLoadDemo}
            />

            {/* Confidence Metrics (in sidebar) */}
            <SidebarConfidencePanel confidence={state.confidence} />
          </div>
        </Sidebar>

        {/* Main Content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Brain Visualization Center */}
          <div className="flex-1 p-4 overflow-hidden">
            <BrainVisualizationCenter
              expressionMap={state.expressionMap}
              diseaseMap={state.diseaseMap}
              overlapScore={state.overlapScore}
              isLoading={state.phase === 'running'}
              showHeaderButtons={state.phase === 'complete'}
              pdfUrl={state.pdfUrl}
              sessionId={state.sessionId}
              onViewReport={() => setReportDrawerOpen(true)}
              hasReport={!!state.reportSections}
            />
          </div>

          {/* Reasoning Trace Panel (bottom) */}
          <ReasoningTracePanel
            events={state.traceEvents}
            phase={state.phase}
            expanded={traceExpanded}
            onToggle={() => setTraceExpanded(!traceExpanded)}
          />
        </main>
      </div>

      {/* Report Drawer */}
      <ReportDrawer
        sections={state.reportSections}
        isOpen={reportDrawerOpen}
        onClose={() => setReportDrawerOpen(false)}
      />

      {/* Error display */}
      {state.error && (
        <div className="fixed bottom-4 left-1/2 -translate-x-1/2 animate-fade-in-scale z-50">
          <div className="flex items-center gap-3 bg-confidence-low text-bg-base px-5 py-3 rounded-xl shadow-2xl shadow-confidence-low/30">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span className="text-sm font-medium">{state.error}</span>
            <button className="ml-2 p-1 hover:bg-confidence-low/80 rounded-lg transition-colors">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Bottom gradient accent */}
      <div className="fixed bottom-0 left-0 right-0 h-px bg-gradient-to-r from-primary via-accent to-confidence-high opacity-30" />
    </div>
  );
}

export default App;
