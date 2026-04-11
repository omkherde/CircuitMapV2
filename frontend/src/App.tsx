import { useCallback } from 'react';
import {
  Header,
  InputPanel,
  ReasoningTrace,
  BrainMaps,
  OverlapScore,
  ConfidencePanel,
  ReportPanel,
  ExportButton,
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
    <div className="min-h-screen bg-background">
      <Header isDemo={state.isDemo} />

      <main className="p-4 md:p-6">
        <div className="grid grid-cols-[280px_1fr_340px] gap-5 max-w-[1600px] mx-auto">
          {/* Left Panel - Input */}
          <aside className="flex flex-col gap-4">
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

            <ConfidencePanel confidence={state.confidence} />

            {state.phase === 'complete' && (
              <ExportButton pdfUrl={state.pdfUrl} sessionId={state.sessionId} />
            )}
          </aside>

          {/* Center Panel - Trace & Visualizations */}
          <section className="flex flex-col gap-4">
            <ReasoningTrace events={state.traceEvents} phase={state.phase} />
            <BrainMaps
              expressionMap={state.expressionMap}
              diseaseMap={state.diseaseMap}
            />
            <OverlapScore data={state.overlapScore} />
          </section>

          {/* Right Panel - Report */}
          <aside className="flex flex-col">
            <ReportPanel sections={state.reportSections} />
          </aside>
        </div>

        {/* Error display */}
        {state.error && (
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 animate-fade-in-scale z-50">
            <div className="flex items-center gap-3 bg-red-600 text-white px-5 py-3 rounded-xl shadow-2xl shadow-red-600/30">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm font-medium">{state.error}</span>
              <button className="ml-2 p-1 hover:bg-red-500 rounded-lg transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer gradient accent */}
      <div className="fixed bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-500 opacity-50" />
    </div>
  );
}

export default App;
