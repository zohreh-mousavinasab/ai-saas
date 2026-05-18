/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        paper: "#f7f9f7",
        moss: "#3d6f5d",
        coral: "#d9674e",
      },
      boxShadow: {
        panel: "0 16px 40px rgba(23, 32, 38, 0.08)",
      },
    },
  },
  plugins: [],
};
