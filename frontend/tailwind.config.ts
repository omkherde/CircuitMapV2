import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#F8F8F7',
        trace: {
          thought: '#374151',
          toolCall: '#1d4ed8',
          toolResult: '#15803d',
        },
        confidence: {
          high: '#16a34a',
          moderate: '#d97706',
          low: '#dc2626',
          pending: '#6b7280',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'fade-in-slow': 'fadeIn 300ms ease-out',
        'pulse-dot': 'pulseDot 1.5s ease-in-out infinite',
        'fill-bar': 'fillBar 500ms ease-out forwards',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
        fillBar: {
          '0%': { width: '0%' },
          '100%': { width: 'var(--fill-width)' },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
