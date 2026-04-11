import { clsx } from 'clsx';
import type { QueryType, DemoScenario, SessionPhase } from '../types';
import { DISEASE_INDICATIONS } from '../types';

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
    <div className="flex flex-col gap-4 p-4 bg-white rounded-lg shadow-sm">
      <h2 className="text-sm font-medium text-gray-700 uppercase tracking-wide">
        Input
      </h2>

      {/* Drug Query Input */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="drug-query" className="text-sm font-medium text-gray-600">
          Drug Molecule
        </label>
        <input
          id="drug-query"
          type="text"
          value={drugQuery}
          onChange={(e) => onDrugQueryChange(e.target.value)}
          disabled={isRunning}
          placeholder={queryType === 'smiles' ? 'Enter SMILES...' : 'Enter drug name...'}
          className={clsx(
            'px-3 py-2 border border-gray-300 rounded-md',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'disabled:bg-gray-100 disabled:cursor-not-allowed',
            queryType === 'smiles' && 'font-mono text-sm'
          )}
        />
      </div>

      {/* Query Type Toggle */}
      <div className="flex gap-4">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="query-type"
            value="name"
            checked={queryType === 'name'}
            onChange={() => onQueryTypeChange('name')}
            disabled={isRunning}
            className="text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">Drug name</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="radio"
            name="query-type"
            value="smiles"
            checked={queryType === 'smiles'}
            onChange={() => onQueryTypeChange('smiles')}
            disabled={isRunning}
            className="text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">SMILES</span>
        </label>
      </div>

      {/* Indication Dropdown */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="indication" className="text-sm font-medium text-gray-600">
          Disease Indication
        </label>
        <select
          id="indication"
          value={indication}
          onChange={(e) => onIndicationChange(e.target.value)}
          disabled={isRunning}
          className={clsx(
            'px-3 py-2 border border-gray-300 rounded-md',
            'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'disabled:bg-gray-100 disabled:cursor-not-allowed',
            !indication && 'text-gray-400'
          )}
        >
          <option value="">Select indication...</option>
          {DISEASE_INDICATIONS.map((disease) => (
            <option key={disease} value={disease}>
              {disease}
            </option>
          ))}
        </select>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col gap-2 mt-2">
        <button
          onClick={onValidate}
          disabled={!isFormValid || isRunning}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            isFormValid && !isRunning
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          )}
        >
          {isRunning ? 'Validating...' : 'Validate Target'}
        </button>
        <button
          onClick={() => onLoadDemo('alzheimers')}
          disabled={isRunning}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-md transition-colors',
            'border border-gray-300 bg-white text-gray-700',
            'hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500',
            'disabled:bg-gray-100 disabled:text-gray-400 disabled:cursor-not-allowed'
          )}
        >
          Load Demo
        </button>
      </div>
    </div>
  );
}
