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
  ClipboardList
} from 'lucide-react';
import type { ReportSections } from '../types';
import { cn } from '@/lib/utils';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

interface SectionConfig {
  key: keyof ReportSections;
  label: string;
  icon: React.ReactNode;
  color: string;
}

const SECTION_CONFIG: SectionConfig[] = [
  {
    key: 'executive_summary',
    label: 'Executive Summary',
    icon: <ClipboardList className="w-4 h-4" />,
    color: 'from-indigo-500 to-blue-600'
  },
  {
    key: 'target_identification',
    label: 'Target Identification',
    icon: <Target className="w-4 h-4" />,
    color: 'from-violet-500 to-purple-600'
  },
  {
    key: 'expression_analysis',
    label: 'Expression Analysis',
    icon: <Dna className="w-4 h-4" />,
    color: 'from-cyan-500 to-teal-600'
  },
  {
    key: 'disease_anatomy',
    label: 'Disease Anatomy',
    icon: <Brain className="w-4 h-4" />,
    color: 'from-rose-500 to-pink-600'
  },
  {
    key: 'spatial_overlap',
    label: 'Spatial Overlap',
    icon: <GitCompareArrows className="w-4 h-4" />,
    color: 'from-amber-500 to-orange-600'
  },
  {
    key: 'circuit_interpretation',
    label: 'Circuit Interpretation',
    icon: <Network className="w-4 h-4" />,
    color: 'from-emerald-500 to-green-600'
  },
  {
    key: 'literature_context',
    label: 'Literature Context',
    icon: <BookOpen className="w-4 h-4" />,
    color: 'from-blue-500 to-indigo-600'
  },
  {
    key: 'confidence_assessment',
    label: 'Confidence Assessment',
    icon: <Shield className="w-4 h-4" />,
    color: 'from-teal-500 to-cyan-600'
  },
  {
    key: 'limitations',
    label: 'Limitations',
    icon: <AlertTriangle className="w-4 h-4" />,
    color: 'from-orange-500 to-red-600'
  },
  {
    key: 'recommendations',
    label: 'Recommendations',
    icon: <Lightbulb className="w-4 h-4" />,
    color: 'from-yellow-500 to-amber-600'
  },
  {
    key: 'references',
    label: 'References',
    icon: <Link2 className="w-4 h-4" />,
    color: 'from-slate-500 to-gray-600'
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

        {/* Empty state */}
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

  const availableSections = SECTION_CONFIG.filter(({ key }) => sections[key]);
  const defaultOpenSections = ['executive_summary'];

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

      {/* Sections */}
      <ScrollArea className="flex-1">
        <div className="px-3 py-2">
          <Accordion type="multiple" defaultValue={defaultOpenSections}>
            {availableSections.map((config) => (
              <AccordionItem key={config.key} value={config.key}>
                <AccordionTrigger>
                  <div className="flex items-center gap-2.5">
                    <div className={cn(
                      'w-7 h-7 rounded-lg flex items-center justify-center bg-gradient-to-br',
                      config.color
                    )}>
                      <span className="text-white">{config.icon}</span>
                    </div>
                    <span className="text-sm font-semibold text-slate-800">{config.label}</span>
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <div className="pl-10 pr-2">
                    <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
                      {sections[config.key]}
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
