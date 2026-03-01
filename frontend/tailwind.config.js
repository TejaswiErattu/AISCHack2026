/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          primary: '#0A0F1E',
          secondary: '#111827',
          card: '#1A2235',
          elevated: '#1E2D45',
        },
        accent: {
          primary: '#00D4AA',   // Climate Active
          financial: '#3B82F6', // Blue
          warning: '#F59E0B',   // Amber
          danger: '#EF4444',    // Red
          positive: '#10B981',  // Green
        },
        text: {
          primary: '#F1F5F9',
          secondary: '#94A3B8',
          muted: '#475569',
        },
        border: {
          DEFAULT: '#1E3A5F',
          active: '#00D4AA',
        }
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        'card': '12px',
        'button': '8px',
        'badge': '6px',
      },
      boxShadow: {
        'glow-teal': '0 0 12px rgba(0, 212, 170, 0.2)',
      }
    },
  },
  plugins: [],
}