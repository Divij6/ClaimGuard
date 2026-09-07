import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      boxShadow: { card: "0 10px 28px rgba(25, 34, 29, 0.07)" },
      colors: {
        ink: "#17231D",
        canvas: "#F7F8F5",
        line: "#E7E9E3",
        accent: "#13795B",
        "accent-soft": "#E7F4EE",
      },
    },
  },
  plugins: [],
};

export default config;
