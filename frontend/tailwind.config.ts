import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        aether: {
          950: "#050505",
          900: "#0A0A0A",
          850: "#121212",
          800: "#1A1A1A",
          700: "#262626",
          600: "#404040",
          500: "#737373",
          400: "#A3A3A3",
          300: "#D4D4D4",
          200: "#E5E5E5",
          100: "#F5F5F5",
          50: "#FAFAFA",
        },
        street: {
          red: "#E11D48",
          orange: "#F97316",
          amber: "#F59E0B",
          emerald: "#10B981",
          cyan: "#06B6D4",
          purple: "#8B5CF6",
        },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
      },
    },
  },
  plugins: [],
};
export default config;
