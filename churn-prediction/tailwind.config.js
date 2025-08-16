/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          light: 'var(--brand-primary, #DAA520)',
          dark: 'var(--brand-primary-dark, #F4D03F)',
          DEFAULT: 'var(--brand-primary, #DAA520)'
        },
        secondary: {
          light: 'var(--brand-secondary, #B8860B)',
          dark: 'var(--brand-secondary-dark, #F7DC6F)',
          DEFAULT: 'var(--brand-secondary, #B8860B)'
        },
        background: {
          light: 'var(--background-light, #FFFFFF)',
          dark: 'var(--background-dark, #0F0F0F)',
          DEFAULT: 'var(--background, #FFFFFF)'
        },
        surface: {
          light: 'var(--surface-light, #F8F9FA)',
          dark: 'var(--surface-dark, #1A1A1A)',
          DEFAULT: 'var(--surface, #F8F9FA)'
        }
      }
    },
  },
  plugins: [],
}

