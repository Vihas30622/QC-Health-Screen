import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  // Relative base so the built assets resolve correctly whether the app is
  // served at the domain root or from a GitHub Pages project subpath
  // (https://<user>.github.io/<repo>/) — no need to hard-code the repo name.
  base: "./",
  server: {
    port: 5173,
  },
});
