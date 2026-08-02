import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#07111f",
        navy: "#0b1c35",
        orange: "#ff5a1f",
        electric: "#ff7438",
      },
      boxShadow: {
        glow: "0 24px 80px -36px rgba(255,90,31,.65)",
      },
    },
  },
  plugins: [],
} satisfies Config;
