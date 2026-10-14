import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
// @ts-expect-error plain ES module without type declarations
import { apiMiddleware } from "./server/api.mjs";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "strata-engine-api",
      configureServer(server) {
        server.middlewares.use(apiMiddleware);
      },
    },
  ],
  server: { port: 5199, host: "127.0.0.1" },
});
