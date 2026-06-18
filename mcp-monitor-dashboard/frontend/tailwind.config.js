/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#1677FF',
        'primary-hover': '#4096FF',
        'primary-active': '#0958D9',
      },
      fontFamily: {
        sans: [
          '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', '"PingFang SC"',
          '"Hiragino Sans GB"', '"Microsoft YaHei"', '"Helvetica Neue"',
          'Helvetica', 'Arial', 'sans-serif'
        ],
        mono: [
          '"SFMono-Regular"', 'Consolas', '"Liberation Mono"', 'Menlo',
          'Courier', 'monospace'
        ],
      },
    },
  },
  plugins: [],
}
