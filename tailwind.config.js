/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/templates/**/*.{html,js}", // Memindai file HTML di folder templates
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Noto Sans JP', 'sans-serif'], // Font dari header_footer.html
      },
      backgroundImage: {
        'sakura-bg': `url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><path fill="%23fde8e8" d="M50 10 C30 30, 20 50, 40 70 C50 60, 60 60, 70 70 C90 50, 80 30, 60 10 C60 20, 50 25, 40 10 Z"/></svg>')`, // Sakura dari admin_kelas.html versi sebelumnya
      },
      animation: {
        'fade-in': 'fadeIn 1s ease-in-out',
        'pulse-slow': 'pulseSlow 3s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSlow: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.05)' },
        },
      },
    },
  },
  plugins: [],
}