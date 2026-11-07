import * as esbuild from "esbuild";
import { rm } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDir = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(frontendDir, "../bookEx/static/dist");
const args = process.argv.slice(2);
const watch = args.includes("--watch");

if (args.some((arg) => arg !== "--watch")) {
  console.error("Usage: node build.mjs [--watch]");
  process.exit(1);
}

const options = {
  absWorkingDir: frontendDir,
  // One entry loads both sources, producing main.js and main.css even before
  // application code imports any components. The entry exists only in memory.
  stdin: {
    contents: 'import "./src/main.ts";\nimport "./src/main.css";',
    resolveDir: frontendDir,
    sourcefile: "build-entry.ts",
    loader: "ts",
  },
  outfile: resolve(outputDir, "main.js"),
  bundle: true,
  platform: "browser",
  format: "esm",
  target: "es2022",
  splitting: false,
  minify: !watch,
  sourcemap: watch,
  tsconfig: resolve(frontendDir, "tsconfig.json"),
  assetNames: "assets/[name]-[hash]",
  loader: {
    ".woff": "file",
    ".woff2": "file",
    ".ttf": "file",
    ".otf": "file",
    ".eot": "file",
    ".svg": "file",
    ".png": "file",
    ".jpg": "file",
    ".jpeg": "file",
    ".gif": "file",
    ".webp": "file",
    ".ico": "file",
  },
  logLevel: "info",
};

try {
  // This directory contains generated output only. Never clean source static
  // files, including the existing uploads directory beside it.
  await rm(outputDir, { recursive: true, force: true });

  if (watch) {
    const context = await esbuild.context(options);
    const shutdown = async () => {
      await context.dispose();
      process.exit(0);
    };
    process.once("SIGINT", shutdown);
    process.once("SIGTERM", shutdown);
    await context.watch();
    console.log("Watching frontend sources. Run npm run typecheck:watch separately.");
  } else {
    await esbuild.build(options);
  }
} catch (error) {
  console.error(error);
  process.exitCode = 1;
}
