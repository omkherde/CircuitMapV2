import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Base backgrounds
        'bg-base': '#0a0a0f',
        'bg-elevated': '#12121a',
        'bg-surface': '#1a1a24',
        'bg-surface-hover': '#22222e',

        // Primary (Cyan)
        primary: {
          DEFAULT: '#00d4ff',
          hover: '#00a8cc',
          glow: 'rgba(0, 212, 255, 0.3)',
        },

        // Secondary (Neon Green)
        secondary: {
          DEFAULT: '#39ff14',
          glow: 'rgba(57, 255, 20, 0.3)',
        },

        // Accent (Magenta)
        accent: {
          DEFAULT: '#ff00ff',
          glow: 'rgba(255, 0, 255, 0.3)',
        },

        // Confidence levels
        confidence: {
          high: '#00ff88',
          'high-glow': 'rgba(0, 255, 136, 0.4)',
          moderate: '#ffaa00',
          'moderate-glow': 'rgba(255, 170, 0, 0.4)',
          low: '#ff3366',
          'low-glow': 'rgba(255, 51, 102, 0.4)',
          pending: '#6a6a7a',
        },

        // Text colors
        text: {
          primary: '#f0f0f5',
          secondary: '#a0a0b0',
          muted: '#6a6a7a',
        },

        // Trace event colors
        trace: {
          thought: '#c4b5fd',
          'tool-call': '#67e8f9',
          'tool-result': '#6ee7b7',
        },

        // Border
        border: {
          DEFAULT: 'rgba(255, 255, 255, 0.08)',
          focus: 'rgba(0, 212, 255, 0.5)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'Liberation Mono', 'Courier New', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-out',
        'fade-in-slow': 'fadeIn 300ms ease-out',
        'fade-in-scale': 'fadeInScale 600ms ease-out backwards',
        'pulse-dot': 'pulseDot 1.5s ease-in-out infinite',
        'fill-bar': 'fillBar 500ms ease-out forwards',
        'action-potential': 'actionPotential 1.5s linear infinite',
        'neural-pulse': 'neuralPulse 2s ease-in-out infinite',
        'scan-line': 'scanLine 2s ease-in-out infinite',
        'confidence-glow': 'confidenceGlow 2s ease-in-out infinite',
        'slide-in-right': 'slideInFromRight 300ms ease-out forwards',
        'slide-out-right': 'slideOutToRight 300ms ease-in forwards',
        'terminal-cursor': 'terminalCursor 1s step-end infinite',
        'accordion-down': 'accordion-down 0.4s ease-out',
        'accordion-up': 'accordion-up 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        fadeInScale: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        pulseDot: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.3' },
        },
        fillBar: {
          '0%': { width: '0%' },
          '100%': { width: 'var(--fill-width)' },
        },
        actionPotential: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        neuralPulse: {
          '0%, 100%': { opacity: '0.3', transform: 'scale(1)' },
          '50%': { opacity: '0.8', transform: 'scale(1.05)' },
        },
        scanLine: {
          '0%': { transform: 'translateY(-100%)', opacity: '0' },
          '10%': { opacity: '1' },
          '90%': { opacity: '1' },
          '100%': { transform: 'translateY(100%)', opacity: '0' },
        },
        confidenceGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 var(--glow-color, rgba(0, 255, 136, 0.4))' },
          '50%': { boxShadow: '0 0 20px 4px var(--glow-color, rgba(0, 255, 136, 0.4))' },
        },
        slideInFromRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideOutToRight: {
          '0%': { transform: 'translateX(0)', opacity: '1' },
          '100%': { transform: 'translateX(100%)', opacity: '0' },
        },
        terminalCursor: {
          '0%, 50%': { opacity: '1' },
          '51%, 100%': { opacity: '0' },
        },
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
      },
      boxShadow: {
        'glow-primary': '0 0 20px rgba(0, 212, 255, 0.3)',
        'glow-secondary': '0 0 20px rgba(57, 255, 20, 0.3)',
        'glow-accent': '0 0 20px rgba(255, 0, 255, 0.3)',
        'glow-high': '0 0 15px rgba(0, 255, 136, 0.4)',
        'glow-moderate': '0 0 15px rgba(255, 170, 0, 0.4)',
        'glow-low': '0 0 15px rgba(255, 51, 102, 0.4)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'heatmap-inferno': 'linear-gradient(90deg, #000004, #420a68, #932667, #dd513a, #fca50a, #fcffa4)',
        'heatmap-viridis': 'linear-gradient(90deg, #440154, #414487, #2a788e, #22a884, #7ad151, #fde725)',
      },
    },
  },
  plugins: [],
} satisfies Config
