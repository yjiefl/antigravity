/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'energy-dark': '#0a0a0c',
        'energy-surface': '#16161a',
        'energy-primary': '#3b82f6',
        'energy-accent': '#f59e0b',
        'energy-success': '#10b981',
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05))',
      }
    },
  },
  plugins: [],
}
