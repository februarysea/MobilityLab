import react from "@vitejs/plugin-react";
import fs from "node:fs";
import path from "node:path";
import { defineConfig, type Plugin } from "vite";

const RUN_ARTIFACTS_STATUS_HEADER = "X-MobilityLab-Run-Artifacts";

function runArtifactsPlugin(): Plugin {
  return {
    name: "mobilitylab-run-artifacts",
    configureServer(server) {
      const configuredRunDir = process.env.MOBILITYLAB_RUN_DIR;
      const root = configuredRunDir ? resolveRunDir(configuredRunDir) : null;
      server.middlewares.use("/run-artifacts", (request, response, _next) => {
        if (!root) {
          response.statusCode = 404;
          response.setHeader(RUN_ARTIFACTS_STATUS_HEADER, "not-configured");
          response.setHeader("Content-Type", "text/plain; charset=utf-8");
          response.end("MOBILITYLAB_RUN_DIR is not set");
          return;
        }
        response.setHeader(RUN_ARTIFACTS_STATUS_HEADER, "configured");
        let requestPath = decodeURIComponent(
          (request.url ?? "/").split("?")[0] ?? "/",
        );
        if (requestPath.startsWith("/run-artifacts")) {
          requestPath = requestPath.slice("/run-artifacts".length) || "/";
        }
        if (requestPath === "/") {
          requestPath = "/visualization_manifest.json";
        }
        const filePath = path.resolve(root, `.${requestPath}`);
        if (!isInside(root, filePath)) {
          response.statusCode = 403;
          response.end("Forbidden");
          return;
        }
        fs.stat(filePath, (statError, stats) => {
          if (statError || !stats.isFile()) {
            response.statusCode = 404;
            response.setHeader("Content-Type", "text/plain; charset=utf-8");
            response.end(`Run artifact not found: ${requestPath}`);
            return;
          }
          response.setHeader("Content-Type", contentType(filePath));
          fs.createReadStream(filePath).pipe(response);
        });
      });
    },
  };
}

function resolveRunDir(configuredRunDir: string): string {
  const invocationCwd = process.env.INIT_CWD ?? process.cwd();
  return path.resolve(invocationCwd, configuredRunDir);
}

function isInside(root: string, candidate: string): boolean {
  const relative = path.relative(root, candidate);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

function contentType(filePath: string): string {
  if (filePath.endsWith(".json")) {
    return "application/json; charset=utf-8";
  }
  if (filePath.endsWith(".jsonl")) {
    return "application/x-ndjson; charset=utf-8";
  }
  if (filePath.endsWith(".geojson")) {
    return "application/geo+json; charset=utf-8";
  }
  return "application/octet-stream";
}

export default defineConfig({
  plugins: [react(), runArtifactsPlugin()],
  server: {
    port: 5173,
  },
});
