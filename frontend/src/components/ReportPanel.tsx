import type { ReportSections } from '../types';

interface ReportPanelProps {
  sections: ReportSections | null;
}

const SECTION_ORDER: { key: keyof ReportSections; label: string }[] = [
  { key: 'executive_summary', label: 'Executive Summary' },
  { key: 'target_identification', label: 'Target Identification' },
  { key: 'expression_analysis', label: 'Expression Analysis' },
  { key: 'disease_anatomy', label: 'Disease Anatomy' },
  { key: 'spatial_overlap', label: 'Spatial Overlap' },
  { key: 'circuit_interpretation', label: 'Circuit Interpretation' },
  { key: 'literature_context', label: 'Literature Context' },
  { key: 'confidence_assessment', label: 'Confidence Assessment' },
  { key: 'limitations', label: 'Limitations' },
  { key: 'recommendations', label: 'Recommendations' },
  { key: 'references', label: 'References' },
];

export function ReportPanel({ sections }: ReportPanelProps) {
  if (!sections) {
    return (
      <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden h-full">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
            Validation Report
          </h2>
        </div>
        <div className="flex-1 flex items-center justify-center text-gray-400 text-sm p-4">
          Report will appear when validation completes
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col bg-white rounded-lg shadow-sm overflow-hidden h-full">
      <div className="px-4 py-3 border-b border-gray-200">
        <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
          Validation Report
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <div className="flex flex-col gap-6">
          {SECTION_ORDER.map(({ key, label }) => {
            const content = sections[key];
            if (!content) return null;

            return (
              <section key={key} className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold text-gray-900">{label}</h3>
                <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {content}
                </div>
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}
