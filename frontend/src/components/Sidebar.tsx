import { ChevronLeft, ChevronRight, Beaker } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  children: React.ReactNode;
  expanded: boolean;
  onToggle: () => void;
}

export function Sidebar({ children, expanded, onToggle }: SidebarProps) {
  return (
    <aside
      className={cn(
        'relative flex flex-col bg-bg-elevated border-r border-white/[0.08] transition-all duration-300 ease-in-out',
        expanded ? 'w-[280px]' : 'w-[64px]'
      )}
    >
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className={cn(
          'absolute -right-3 top-4 z-10',
          'w-6 h-6 rounded-full',
          'bg-bg-surface border border-white/[0.08]',
          'flex items-center justify-center',
          'text-text-muted hover:text-text-primary hover:border-primary/30',
          'transition-all duration-200'
        )}
      >
        {expanded ? (
          <ChevronLeft className="w-3.5 h-3.5" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5" />
        )}
      </button>

      {/* Content */}
      <div
        className={cn(
          'flex-1 overflow-hidden transition-opacity duration-300',
          expanded ? 'opacity-100' : 'opacity-0'
        )}
      >
        {expanded && children}
      </div>

      {/* Collapsed State Icon */}
      {!expanded && (
        <div className="flex flex-col items-center pt-4 gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-cyan-400 flex items-center justify-center">
            <Beaker className="w-5 h-5 text-bg-base" />
          </div>
        </div>
      )}
    </aside>
  );
}
