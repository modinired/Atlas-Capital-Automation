import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0A1931',
        secondary: '#185ADB',
        accent: '#FFC947',
      },
    },
  },
  plugins: [],
}

export default config