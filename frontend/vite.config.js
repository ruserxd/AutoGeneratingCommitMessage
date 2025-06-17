import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";
import { fileURLToPath } from "url";
import * as path from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
  base: "./",
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../extension/out"), // 打包到專案的 out/
    emptyOutDir: true,
    rollupOptions: {
      input: {
        webview: resolve(__dirname, "index.html"),
      },
    },
  },
});
