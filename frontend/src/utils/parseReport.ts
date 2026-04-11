import type { ReportSections } from '../types';

const SECTION_ALIASES: Record<string, keyof ReportSections> = {
  'executive summary': 'executive_summary',
  'summary': 'executive_summary',
  'target identification': 'target_identification',
  'molecular target profile': 'target_identification',
  'target id': 'target_identification',
  'target': 'target_identification',
  'expression analysis': 'expression_analysis',
  'brain expression analysis': 'expression_analysis',
  'expression': 'expression_analysis',
  'spatial overlap': 'spatial_overlap',
  'target-pathology overlap': 'spatial_overlap',
  'overlap': 'spatial_overlap',
  'circuit interpretation': 'circuit_interpretation',
  'functional circuit context': 'circuit_interpretation',
  'circuit': 'circuit_interpretation',
  'off-target risk assessment': 'off_target_risk',
  'literature context': 'literature_context',
  'literature evidence summary': 'literature_context',
  'literature': 'literature_context',
  'confidence assessment': 'confidence_assessment',
  'confidence': 'confidence_assessment',
  'recommended clinical endpoints': 'recommendations',
  'limitations': 'limitations',
  'data sources & limitations': 'limitations',
  'caveats': 'limitations',
  'recommendations': 'recommendations',
  'next steps': 'recommendations',
  'pre-clinical validation recommendations': 'preclinical_validation',
  'references': 'preclinical_validation',
  'citations': 'preclinical_validation',
  'disease anatomy': 'disease_anatomy',
  'disease map': 'disease_anatomy',
};

function normalizeHeader(header: string): keyof ReportSections | null {
  const normalized = header.toLowerCase().trim();
  return SECTION_ALIASES[normalized] || null;
}

export function parseReport(text: string): ReportSections {
  const sections: ReportSections = {};

  // Split on markdown headers (## )
  const parts = text.split(/^## /m);

  for (const part of parts) {
    if (!part.trim()) continue;

    // First line is the header, rest is content
    const lines = part.split('\n');
    const header = lines[0]?.trim();
    const content = lines.slice(1).join('\n').trim();

    if (!header || !content) continue;

    const sectionKey = normalizeHeader(header);
    if (sectionKey) {
      sections[sectionKey] = content;
    }
  }

  return sections;
}

export function formatSection(content: string): string {
  // Basic markdown-like formatting
  return content
    // Bold: **text** or __text__
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/__(.*?)__/g, '$1')
    // Italic: *text* or _text_
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/_(.*?)_/g, '$1')
    // Lists: - item or * item
    .replace(/^[-*] /gm, '• ')
    // Clean up extra whitespace
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
