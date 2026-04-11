import { useEffect } from 'react';
import {
  FileText,
  X,
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
import { Button } from '@/components/ui/button';
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
}

const SECTION_CONFIG: SectionConfig[] = [
  {
    key: 'executive_summary',
    label: 'Executive Summary',
    icon: <ClipboardList className="w-4 h-4" />,
  },
  {
    key: 'target_identification',
    label: 'Target Identification',
    icon: <Target className="w-4 h-4" />,
  },
  {
    key: 'expression_analysis',
    label: 'Expression Analysis',
    icon: <Dna className="w-4 h-4" />,
  },
  {
    key: 'disease_anatomy',
    label: 'Disease Anatomy',
    icon: <Brain className="w-4 h-4" />,
  },
  {
    key: 'spatial_overlap',
    label: 'Spatial Overlap',
    icon: <GitCompareArrows className="w-4 h-4" />,
  },
  {
    key: 'circuit_interpretation',
    label: 'Circuit Interpretation',
    icon: <Network className="w-4 h-4" />,
  },
  {
    key: 'literature_context',
    label: 'Literature Context',
    icon: <BookOpen className="w-4 h-4" />,
  },
  {
    key: 'confidence_assessment',
    label: 'Confidence Assessment',
    icon: <Shield className="w-4 h-4" />,
  },
  {
    key: 'limitations',
    label: 'Limitations',
    icon: <AlertTriangle className="w-4 h-4" />,
  },
  {
    key: 'recommendations',
    label: 'Recommendations',
    icon: <Lightbulb className="w-4 h-4" />,
  },
  {
    key: 'references',
    label: 'References',
    icon: <Link2 className="w-4 h-4" />,
  },
];

interface ReportDrawerProps {
  sections: ReportSections | null;
  isOpen: boolean;
  onClose: () => void;
}

export function ReportDrawer({ sections, isOpen, onClose }: ReportDrawerProps) {
  // Close on escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const availableSections = sections
    ? SECTION_CONFIG.filter(({ key }) => sections[key])
    : [];
  const defaultOpenSections = ['executive_summary'];

  return (
    <>
      {/* Backdrop */}
      <div
        className="drawer-backdrop animate-fade-in"
        onClick={onClose}
      />

      {/* Drawer */}
      <div className={cn(
        'drawer animate-slide-in-right',
        'flex flex-col'
      )}>
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08] bg-bg-surface/50">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-confidence-high to-emerald-400 flex items-center justify-center">
              <FileText className="w-4 h-4 text-bg-base" />
            </div>
            <h2 className="text-base font-semibold text-text-primary">
              Validation Report
            </h2>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-text-muted hover:text-text-primary"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        {!sections ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
            <div className="w-16 h-16 rounded-full bg-bg-surface flex items-center justify-center mb-4">
              <FileText className="w-8 h-8 text-text-muted" />
            </div>
            <p className="text-sm text-text-secondary mb-2">
              Report will appear when validation completes
            </p>
            <p className="text-xs text-text-muted">
              The AI agent is analyzing your drug target
            </p>
          </div>
        ) : (
          <ScrollArea className="flex-1">
            <div className="p-4">
              <Accordion type="multiple" defaultValue={defaultOpenSections}>
                {availableSections.map((config) => (
                  <AccordionItem key={config.key} value={config.key}>
                    <AccordionTrigger>
                      <div className="flex items-center gap-2.5">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center bg-bg-surface border border-white/[0.08]">
                          <span className="text-primary">{config.icon}</span>
                        </div>
                        <span className="text-sm font-semibold text-text-primary">{config.label}</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="pl-10 pr-2">
                        <div className="text-sm text-text-secondary leading-relaxed whitespace-pre-wrap">
                          {sections[config.key]}
                        </div>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          </ScrollArea>
        )}
      </div>
    </>
  );
}
