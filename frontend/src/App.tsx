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

      <main className="p-4">
        <div className="grid grid-cols-[280px_1fr_340px] gap-4 max-w-[1600px] mx-auto">
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
          <div className="fixed bottom-4 left-1/2 -translate-x-1/2 bg-red-600 text-white px-6 py-3 rounded-lg shadow-lg">
            {state.error}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
