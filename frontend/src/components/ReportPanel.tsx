import {
  FileText,
  Target,
  Dna,
  Brain,
  GitCompareArrows,
  Network,
  BookOpen,
  Shield,
  AlertTriangle,
  Lightbulb,
  Link2,
  ClipboardList,
} from 'lucide-react';
import type { ReportSections } from '../types';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

interface SectionConfig {
  keys: (keyof ReportSections)[];
  value: string;
  label: string;
  icon: React.ReactNode;
}

const SECTION_CONFIG: SectionConfig[] = [
  {
    keys: ['executive_summary'],
    value: 'executive_summary',
    label: 'Executive Summary',
    icon: <ClipboardList className="w-4 h-4" />,
  },
  {
    keys: ['target_identification'],
    value: 'target_identification',
    label: 'Molecular Target Profile',
    icon: <Target className="w-4 h-4" />,
  },
  {
    keys: ['expression_analysis'],
    value: 'expression_analysis',
    label: 'Brain Expression Analysis',
    icon: <Dna className="w-4 h-4" />,
  },
  {
    keys: ['circuit_interpretation'],
    value: 'circuit_interpretation',
    label: 'Functional Circuit Context',
    icon: <Network className="w-4 h-4" />,
  },
  {
    keys: ['spatial_overlap'],
    value: 'spatial_overlap',
    label: 'Target-Pathology Overlap',
    icon: <GitCompareArrows className="w-4 h-4" />,
  },
  {
    keys: ['off_target_risk', 'disease_anatomy'],
    value: 'off_target_risk',
    label: 'Off-Target Risk Assessment',
    icon: <Brain className="w-4 h-4" />,
  },
  {
    keys: ['literature_context'],
    value: 'literature_context',
    label: 'Literature Evidence Summary',
    icon: <BookOpen className="w-4 h-4" />,
  },
  {
    keys: ['confidence_assessment'],
    value: 'confidence_assessment',
    label: 'Confidence Assessment',
    icon: <Shield className="w-4 h-4" />,
  },
  {
    keys: ['limitations'],
    value: 'limitations',
    label: 'Data Sources & Limitations',
    icon: <AlertTriangle className="w-4 h-4" />,
  },
  {
    keys: ['recommendations'],
    value: 'recommendations',
    label: 'Recommended Clinical Endpoints',
    icon: <Lightbulb className="w-4 h-4" />,
  },
  {
    keys: ['preclinical_validation', 'references'],
    value: 'preclinical_validation',
    label: 'Pre-Clinical Validation Recommendations',
    icon: <Link2 className="w-4 h-4" />,
  },
];

interface ReportPanelProps {
  sections: ReportSections | null;
}

export function ReportPanel({ sections }: ReportPanelProps) {
  if (!sections) {
    return (
      <Card className="overflow-hidden h-full animate-fade-in">
        <CardHeader className="py-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
              <FileText className="w-3.5 h-3.5 text-white" />
            </div>
            <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
              Validation Report
            </h2>
          </div>
        </CardHeader>

        <CardContent className="flex-1 flex flex-col items-center justify-center text-center min-h-[300px]">
          <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
            <FileText className="w-8 h-8 text-slate-300" />
          </div>
          <p className="text-sm text-slate-500 mb-2">
            Report will appear when validation completes
          </p>
          <p className="text-xs text-slate-400">
            The AI agent is analyzing your drug target
          </p>
        </CardContent>
      </Card>
    );
  }

  const availableSections = SECTION_CONFIG.map((config) => ({
    ...config,
    content: config.keys.map((key) => sections[key]).find(Boolean),
  })).filter((config) => config.content);

  return (
    <Card className="overflow-hidden h-full flex flex-col animate-fade-in-scale">
      <CardHeader className="py-3 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
            <FileText className="w-3.5 h-3.5 text-white" />
          </div>
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
            Validation Report
          </h2>
        </div>
      </CardHeader>

      <ScrollArea className="flex-1">
        <div className="px-3 py-2">
          <Accordion type="multiple" defaultValue={['executive_summary']}>
            {availableSections.map((section) => (
              <AccordionItem key={section.value} value={section.value}>
                <AccordionTrigger>
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br from-slate-400 to-slate-500">
                      <span className="text-white">{section.icon}</span>
                    </div>
                    <span className="text-sm font-semibold text-slate-800">{section.label}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="pl-10 pr-2">
                    <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
                      {section.content}
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </ScrollArea>
    </Card>
  );
}
