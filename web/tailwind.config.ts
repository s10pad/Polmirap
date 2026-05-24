import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        syncopate: ['Syncopate', 'sans-serif'],
        barlow: ['Barlow', 'sans-serif'],
        'barlow-condensed': ['Barlow Condensed', 'sans-serif'],
        mono: ['DM Mono', 'monospace'],
      },
      colors: {
        border: 'hsl(var(--border))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
      },
      keyframes: {
        'holo-spin': { to: { transform: 'rotate(360deg)' } },
        'float-y': {
          '0%, 100%': { transform: 'translateY(0) rotate(0deg)' },
          '50%':      { transform: 'translateY(-14px) rotate(4deg)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.7', transform: 'translate(-50%,-50%) scale(1)' },
          '50%':       { opacity: '1',   transform: 'translate(-50%,-50%) scale(1.12)' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%':       { opacity: '0.18' },
        },
        'ray-fade': {
          '0%, 100%': { opacity: '0.25' },
          '50%':       { opacity: '0.85' },
        },
        'fade-up': {
          from: { opacity: '0', transform: 'translateY(22px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        'reveal': {
          from: { opacity: '0', transform: 'translateY(28px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
      },
      animation: {
        'holo-spin':  'holo-spin var(--spin-duration, 8s) linear infinite',
        'float-y':    'float-y var(--float-duration, 7s) ease-in-out infinite',
        'glow-pulse': 'glow-pulse 4.5s ease-in-out infinite',
        blink:        'blink 2.2s ease-in-out infinite',
        'ray-fade':   'ray-fade var(--ray-duration, 3s) ease-in-out infinite',
        'fade-up':    'fade-up 0.8s ease forwards',
        'fade-up-1':  'fade-up 0.6s ease 0.2s forwards',
        'fade-up-2':  'fade-up 0.8s ease 0.38s forwards',
        'fade-up-3':  'fade-up 0.7s ease 0.54s forwards',
        'fade-up-4':  'fade-up 0.6s ease 0.85s forwards',
        reveal:       'reveal 0.9s ease forwards',
      },
    },
  },
  plugins: [],
}

export default config
