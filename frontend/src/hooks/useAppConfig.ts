import { useEffect, useState } from 'react';
import type { AppConfig } from '../types';
import { loadAppConfig } from '../api/client';

interface AppConfigState {
  config: AppConfig | null;
  isLoading: boolean;
  error: string | null;
}

export function useAppConfig(): AppConfigState {
  const [state, setState] = useState<AppConfigState>({
    config: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    let isCancelled = false;

    async function fetchConfig() {
      try {
        const config = await loadAppConfig();
        if (!isCancelled) {
          setState({
            config,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        if (!isCancelled) {
          setState({
            config: null,
            isLoading: false,
            error: error instanceof Error ? error.message : null,
          });
        }
      }
    }

    fetchConfig();

    return () => {
      isCancelled = true;
    };
  }, []);

  return state;
}
