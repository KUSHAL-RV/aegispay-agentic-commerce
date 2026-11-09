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
        aegis: {
          bg: "#0B0E14",
          surface: "#121824",
          card: "#182234",
          border: "#202E44",
          accent: "#00E599",
          "accent-dim": "#00B377",
          paypal: "#0070BA",
          "paypal-dark": "#003087",
          warning: "#F59E0B",
          danger: "#EF4444",
          success: "#10B981",
          info: "#38BDF8",
          muted: "#64748B",
        },
      },
      fontFamily: {
        mono: [
          "JetBrains Mono",
          "ui-monospace",
          "SFMono-Regular",
          "Menlo",
          "Monaco",
          "Consolas",
          "monospace",
        ],
      },
      keyframes: {
        flashGreen: {
          "0%": { backgroundColor: "rgba(0, 229, 153, 0.35)", transform: "scale(1.01)" },
          "100%": { backgroundColor: "transparent", transform: "scale(1)" },
        },
        pulseGlow: {
          "0%, 100%": { opacity: "1", filter: "drop-shadow(0 0 8px rgba(0, 229, 153, 0.6))" },
          "50%": { opacity: "0.6", filter: "drop-shadow(0 0 2px rgba(0, 229, 153, 0.2))" },
        },
      },
      animation: {
        flash: "flashGreen 1.6s cubic-bezier(0.4, 0, 0.2, 1)",
        "pulse-glow": "pulseGlow 2.5s infinite",
      },
    },
  },
  plugins: [],
};

export default config;

