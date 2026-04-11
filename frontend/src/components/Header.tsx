import { Brain, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface HeaderProps {
  isDemo: boolean;
}

export function Header({ isDemo }: HeaderProps) {
  return (
    <header className="bg-gradient-header px-6 py-4 shadow-lg">
      <div className="max-w-[1600px] mx-auto flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-cyan-400 rounded-full animate-pulse-dot" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold text-white tracking-tight">
              CircuitMap
            </h1>
            <span className="text-xs text-slate-400 font-medium">
              AI-Powered Drug Target Validation
            </span>
          </div>
        </div>

        {/* Right side badges */}
        <div className="flex items-center gap-3">
          {isDemo && (
            <Badge
              variant="warning"
              className="animate-fade-in"
            >
              <Sparkles className="w-3 h-3" />
              Demo Mode
            </Badge>
          )}
          <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>System Online</span>
          </div>
        </div>
      </div>
    </header>
  );
}
