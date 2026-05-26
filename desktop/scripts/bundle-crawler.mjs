#!/usr/bin/env node
/**
 * Bundles src-crawler/cli.js into standalone executables via esbuild + pkg.
 * Output: src-tauri/binaries/crawler-{tauri-target}[.exe]
 *
 * Run: node scripts/bundle-crawler.mjs
 * Or:  npm run bundle:crawler
 */
import { build } from "esbuild";
import { execSync } from "child_process";
import { mkdirSync, readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { createRequire } from "module";

const _require = createRequire(import.meta.url);
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const distDir = join(root, "src-crawler/dist");
const binDir = join(root, "src-tauri/binaries");

mkdirSync(distDir, { recursive: true });
mkdirSync(binDir, { recursive: true });

// Read the real playwright-core version so we can inline it.
const pwPkgPath = join(root, "node_modules/playwright-core/package.json");
const pwPkg = JSON.parse(readFileSync(pwPkgPath, "utf-8"));

// playwright-core/lib/package.js does:
//   const packageRoot = path.join(__dirname, "..");
//   const packageJSON = require(path.join(packageRoot, "package.json")); // dynamic!
//
// Inside a pkg snapshot __dirname resolves to the bundle directory, so that
// dynamic require looks for a file that doesn't exist in the snapshot.
// We replace the entire module with a shim that inlines the version and keeps
// the other helpers working (they use __dirname at runtime which is fine for
// system-browser launches that never call libPath for Chromium helpers).
// playwright-core/lib/package.js does require(path.join(__dirname, '..', 'package.json'))
// which becomes a dynamic require that fails inside a pkg snapshot.
// We intercept the RESOLVED file and return a shim with the version inlined.
const playwrightPkgShimPlugin = {
  name: "playwright-pkg-shim",
  setup(pluginBuild) {
    pluginBuild.onLoad(
      { filter: /node_modules[/\\]playwright-core[/\\]lib[/\\]package\.js$/ },
      () => ({
        contents: `
"use strict";
const path = require("path");
const packageRoot = path.join(__dirname, "..");
module.exports = {
  packageRoot,
  packageJSON: ${JSON.stringify({ name: "playwright-core", version: pwPkg.version })},
  binPath: path.join(packageRoot, "bin"),
  libPath: (...parts) => path.join(packageRoot, "lib", ...parts),
  __esModule: true,
};
`,
        loader: "js",
      })
    );
  },
};

// ── Step 1: esbuild → single CJS bundle ────────────────────────────────────
console.log("esbuild: bundling crawler…");
const buildResult = await build({
  entryPoints: [join(root, "src-crawler/cli.js")],
  bundle: true,
  platform: "node",
  format: "cjs",
  external: [
    "fsevents",        // macOS-only optional watcher
    "chromium-bidi/*", // optional bidi transport, not needed
  ],
  write: false,
  plugins: [playwrightPkgShimPlugin],
});

// Post-process: replace dynamic require()s that use runtime-computed paths like
// `require(path.join(packageRoot, "file.json"))` — pkg can't include these statically
// since the path is a variable. Inline the file content at bundle time instead.
const pwPkgJsonInline  = JSON.stringify({ name: "playwright-core", version: pwPkg.version });
const pwBrowsersInline = readFileSync(join(root, "node_modules/playwright-core/browsers.json"), "utf-8")
  .replace(/\s*\/\/.*$/gm, "").replace(/\n/g, " "); // strip comments, compact

const bundleText = buildResult.outputFiles[0].text
  // playwright-core/lib/package.js and coreBundle.js: require(path.join(packageRoot, "package.json"))
  .replace(
    /require\(import_path\d+\.default\.join\(\w+,\s*"package\.json"\)\)/g,
    pwPkgJsonInline
  )
  // playwright-core/lib/server/registry/index.js: require(path.join(packageRoot, "browsers.json"))
  .replace(
    /require\(import_path\d+\.default\.join\(\w+,\s*"browsers\.json"\)\)/g,
    pwBrowsersInline
  )
  // playwright CLI api.json (only used for debug output, never hit in normal use — stub it)
  .replace(
    /require\(import_path\d+\.default\.join\(\w+,\s*"api\.json"\)\)/g,
    "{}"
  );

const bundleOutPath = join(distDir, "crawler-bundle.cjs");
writeFileSync(bundleOutPath, bundleText);
console.log("✓ esbuild done");

// ── Step 2: pkg → native executables ───────────────────────────────────────
const targets = [
  { pkg: "node18-win-x64",     tauri: "x86_64-pc-windows-msvc",   ext: ".exe" },
  { pkg: "node18-macos-arm64", tauri: "aarch64-apple-darwin",      ext: "" },
  { pkg: "node18-macos-x64",   tauri: "x86_64-apple-darwin",       ext: "" },
  { pkg: "node18-linux-x64",   tauri: "x86_64-unknown-linux-gnu",  ext: "" },
];

const run = (cmd) => execSync(cmd, { cwd: root, stdio: "inherit" });

for (const t of targets) {
  const out = join(binDir, `crawler-${t.tauri}${t.ext}`);
  console.log(`pkg: building ${t.pkg}…`);
  run(
    `npx pkg src-crawler/dist/crawler-bundle.cjs` +
    ` --target ${t.pkg}` +
    ` --no-bytecode --public-packages "*" --public` +
    ` --output ${out}`
  );
  console.log(`✓ ${out}`);
}

console.log("\n✓ All crawler binaries built.");
console.log("Now run: npm run tauri build");
