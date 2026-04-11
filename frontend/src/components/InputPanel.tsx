import {
  FlaskConical,
  Stethoscope,
  Play,
  Loader2,
  Beaker
} from 'lucide-react';
import type { QueryType, DemoScenario, SessionPhase, InputPanelConfig } from '../types';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface InputPanelProps {
  config: InputPanelConfig | null;
  drugQuery: string;
  queryType: QueryType;
  indication: string;
  phase: SessionPhase;
  onDrugQueryChange: (value: string) => void;
  onQueryTypeChange: (value: QueryType) => void;
  onIndicationChange: (value: string) => void;
  onValidate: () => void;
  onLoadDemo: (scenario: DemoScenario) => void;
}

export function InputPanel({
  config,
  drugQuery,
  queryType,
  indication,
  phase,
  onDrugQueryChange,
  onQueryTypeChange,
  onIndicationChange,
  onValidate,
  onLoadDemo,
}: InputPanelProps) {
  if (!config) {
    return (
      <Card className="overflow-hidden animate-fade-in">
        <CardHeader className="py-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
              <Beaker className="w-3.5 h-3.5 text-white" />
            </div>
            <Skeleton className="h-4 w-16" />
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="flex gap-4">
            <Skeleton className="h-5 w-24" />
            <Skeleton className="h-5 w-16" />
          </div>
          <div className="flex flex-col gap-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-10 w-full" />
          </div>
          <div className="flex flex-col gap-2.5 mt-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  const isRunning = phase === 'running';
  const isFormValid = drugQuery.trim() !== '' && indication !== '';

  return (
    <Card className="overflow-hidden animate-fade-in">
      <CardHeader className="py-3">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-600 flex items-center justify-center">
            <Beaker className="w-3.5 h-3.5 text-white" />
          </div>
          <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wide">
            {config.title}
          </h2>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        {/* Drug Query Input */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="drug-query">{config.drug_query_label}</Label>
          <div className="relative">
            <FlaskConical className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
            <Input
              id="drug-query"
              type="text"
              value={drugQuery}
              onChange={(e) => onDrugQueryChange(e.target.value)}
              disabled={isRunning}
              placeholder={queryType === 'smiles' ? config.smiles_placeholder : config.drug_name_placeholder}
              className={cn(
                'pl-10',
                queryType === 'smiles' && 'font-mono text-sm'
              )}
            />
          </div>
        </div>

        {/* Query Type Toggle */}
        <div className="flex gap-4">
          <label className="flex items-center gap-2.5 cursor-pointer group">
            <input
              type="radio"
              name="query-type"
              value="name"
              checked={queryType === 'name'}
              onChange={() => onQueryTypeChange('name')}
              disabled={isRunning}
              className="radio-custom"
            />
            <span className={cn(
              'text-sm font-medium transition-colors',
              queryType === 'name' ? 'text-indigo-600' : 'text-slate-600 group-hover:text-slate-800'
            )}>
              {config.query_type_labels.name}
            </span>
          </label>
          <label className="flex items-center gap-2.5 cursor-pointer group">
            <input
              type="radio"
              name="query-type"
              value="smiles"
              checked={queryType === 'smiles'}
              onChange={() => onQueryTypeChange('smiles')}
              disabled={isRunning}
              className="radio-custom"
            />
            <span className={cn(
              'text-sm font-medium transition-colors',
              queryType === 'smiles' ? 'text-indigo-600' : 'text-slate-600 group-hover:text-slate-800'
            )}>
              {config.query_type_labels.smiles}
            </span>
          </label>
        </div>

        {/* Indication Dropdown */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="indication">{config.indication_label}</Label>
          <div className="relative">
            <Stethoscope className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
            <Select
              value={indication}
              onValueChange={onIndicationChange}
              disabled={isRunning}
            >
              <SelectTrigger className="pl-10">
                <SelectValue placeholder={config.indication_placeholder} />
              </SelectTrigger>
              <SelectContent>
                {config.indications.map((disease) => (
                  <SelectItem key={disease} value={disease}>
                    {disease}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-2.5 mt-2">
          <Button
            onClick={onValidate}
            disabled={!isFormValid || isRunning}
            className={cn(
              'w-full',
              isRunning && 'animate-pulse-glow'
            )}
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                {config.validating_button_label}
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                {config.validate_button_label}
              </>
            )}
          </Button>
          <Button
            variant="secondary"
            onClick={() => onLoadDemo('alzheimers')}
            disabled={isRunning}
            className="w-full"
          >
            <Beaker className="w-4 h-4" />
            {config.load_demo_button_label}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
