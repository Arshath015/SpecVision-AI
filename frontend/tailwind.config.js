/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f4f6fb",
          100: "#e6eaf5",
          200: "#c9d3e8",
          300: "#a0b1d5",
          400: "#7488bd",
          500: "#52699f",
          600: "#3f5280",
          700: "#334267",
          800: "#2b3655",
          900: "#272f47",
        },
      },
    },
  },
  plugins: [],
};
