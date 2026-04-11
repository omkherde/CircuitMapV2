import {
  FlaskConical,
  Stethoscope,
  Play,
  Loader2,
  Beaker
} from 'lucide-react';
import type { QueryType, DemoScenario, SessionPhase } from '../types';
import { DISEASE_INDICATIONS } from '../types';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface InputPanelProps {
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
            Input
          </h2>
        </div>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        {/* Drug Query Input */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="drug-query">Drug Molecule</Label>
          <div className="relative">
            <FlaskConical className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
            <Input
              id="drug-query"
              type="text"
              value={drugQuery}
              onChange={(e) => onDrugQueryChange(e.target.value)}
              disabled={isRunning}
              placeholder={queryType === 'smiles' ? 'Enter SMILES string...' : 'Enter drug name...'}
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
              Drug name
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
              SMILES
            </span>
          </label>
        </div>

        {/* Indication Dropdown */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="indication">Disease Indication</Label>
          <div className="relative">
            <Stethoscope className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none z-10" />
            <Select
              value={indication}
              onValueChange={onIndicationChange}
              disabled={isRunning}
            >
              <SelectTrigger className="pl-10">
                <SelectValue placeholder="Select indication..." />
              </SelectTrigger>
              <SelectContent>
                {DISEASE_INDICATIONS.map((disease) => (
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
                Validating...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Validate Target
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
            Load Demo
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
