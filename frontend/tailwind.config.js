/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        legal: {
          50: '#f4f6f9',
          100: '#e6ebf2',
          200: '#c8d4e3',
          700: '#1e3a8a',
          800: '#1e293b',
          900: '#0f172a'
        }
      }
    },
  },
  plugins: [],
}
