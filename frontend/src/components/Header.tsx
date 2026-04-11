import { clsx } from 'clsx';

interface HeaderProps {
  isDemo: boolean;
}

export function Header({ isDemo }: HeaderProps) {
  return (
    <header className="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
      <h1 className="text-xl font-semibold text-gray-900">CircuitMap</h1>
      {isDemo && (
        <span
          className={clsx(
            'px-3 py-1 text-sm font-medium rounded-full',
            'bg-amber-100 text-amber-800'
          )}
        >
          Demo Mode
        </span>
      )}
    </header>
  );
}
