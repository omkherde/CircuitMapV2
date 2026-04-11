import { Brain, Sparkles } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface HeaderProps {
  isDemo: boolean;
}

export function Header({ isDemo }: HeaderProps) {
  return (
    <header className="bg-bg-elevated border-b border-white/[0.08] px-6 py-3">
      <div className="max-w-[1800px] mx-auto flex items-center justify-between">
        {/* Logo and Title */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow-primary">
              <Brain className="w-6 h-6 text-bg-base" />
            </div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full animate-pulse-dot" />
          </div>
          <div className="flex flex-col">
            <h1 className="text-xl font-bold text-text-primary tracking-tight">
              CircuitMap
            </h1>
            <span className="text-xs text-text-muted font-medium">
              AI-Powered Drug Target Validation
            </span>
          </div>
        </div>

        {/* Right side - Status */}
        <div className="flex items-center gap-4">
          {/* Demo Mode Badge */}
          {isDemo && (
            <Badge
              variant="warning"
              className="animate-fade-in"
            >
              <Sparkles className="w-3 h-3" />
              Demo Mode
            </Badge>
          )}

          {/* System Status */}
          <div className="hidden sm:flex items-center gap-2 text-xs text-text-muted px-3 py-1.5 bg-bg-surface rounded-full border border-white/[0.08]">
            <div className="w-2 h-2 rounded-full bg-confidence-high animate-pulse" />
            <span>System Online</span>
          </div>
        </div>
      </div>
    </header>
  );
}
