import { createRequire } from "node:module";
import { existsSync, mkdirSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { execFileSync } from "node:child_process";

const usage = "usage: node snapshot.mjs <url or local file> <out.html> [pass label] [--dark | --light] [--width 1440] [--height 810] [--chromium <path>]";
const args = process.argv.slice(2);
const positionals = [];
let width = 1440;
let height = 810;
let chromiumFlag = null;
const size = (name, value) => {
  const n = Number(value);
  if (!Number.isInteger(n) || n <= 0) {
    console.error(`--${name} must be a whole number above 0, got "${value}"`);
    process.exit(1);
  }
  return n;
};
for (let i = 0; i < args.length; i++) {
  const arg = args[i];
  const match = /^--(width|height|chromium)(?:=(.*))?$/.exec(arg);
  if (match) {
    const value = match[2] ?? args[++i];
    if (value === undefined || value.startsWith("--")) {
      console.error(`--${match[1]} needs a value, like --${match[1]} 1440`);
      process.exit(1);
    }
    if (match[1] === "width") width = size("width", value);
    else if (match[1] === "height") height = size("height", value);
    else chromiumFlag = value;
  } else if (!arg.startsWith("--")) {
    positionals.push(arg);
  }
}
const [url, out, label] = positionals;
const scheme = args.includes("--dark") ? "dark" : args.includes("--light") ? "light" : "no-preference";
if (!url || !out) {
  console.error(usage);
  process.exit(1);
}
// A path on disk is a page too: a bare file path is not a URL, and
// Playwright rejects it with a protocol error, so turn it into one.
const target = statSync(url, { throwIfNoEntry: false })?.isFile() ? pathToFileURL(resolve(url)).href : url;

/* ---------- Playwright resolution: the project's own copy, then the global install ---------- */

const COMMON_GLOBAL_ROOT = "/usr/local/share/npm-global/lib/node_modules";
let cachedGlobalRoots = null;

function npmGlobalRoot() {
  if (cachedGlobalRoots) return cachedGlobalRoots;
  const roots = [];
  for (const entry of (process.env.NODE_PATH || "").split(process.platform === "win32" ? ";" : ":")) {
    const trimmed = entry.trim();
    if (trimmed) roots.push(trimmed);
  }
  try {
    const output = execFileSync("npm", ["root", "-g"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    const trimmed = String(output).trim();
    if (trimmed) roots.push(trimmed);
  } catch {
    /* npm is not available here */
  }
  roots.push(COMMON_GLOBAL_ROOT);
  cachedGlobalRoots = roots;
  return roots;
}

function globalModuleDirs() {
  const dirs = [];
  for (const root of npmGlobalRoot()) {
    dirs.push(join(root, "playwright"));
    dirs.push(join(root, "playwright-core"));
    dirs.push(join(root, "@playwright", "mcp", "node_modules", "playwright"));
    dirs.push(join(root, "@playwright", "mcp", "node_modules", "playwright-core"));
  }
  return dirs;
}

function requireFrom(moduleDir, names) {
  const localRequire = createRequire(import.meta.url);
  for (const name of names) {
    try {
      const direct = localRequire.resolve(join(moduleDir, name));
      return localRequire(direct);
    } catch {
      /* try the next candidate */
    }
    try {
      const found = localRequire.resolve(name, { paths: [moduleDir, dirname(moduleDir)] });
      return localRequire(found);
    } catch {
      /* try the next candidate */
    }
  }
  return null;
}

function loadPlaywright() {
  const project = process.cwd();
  try {
    return createRequire(resolve(project, "package.json"))("playwright");
  } catch {
    /* the project has no Playwright of its own */
  }
  for (const moduleDir of globalModuleDirs()) {
    const found = requireFrom(moduleDir, ["playwright", "playwright-core"]);
    if (found) return found;
  }
  return null;
}

/* ---------- browser binary ---------- */

const SYSTEM_CHROMIUM_CANDIDATES = ["/usr/bin/chromium", "/usr/bin/chromium-browser"];

function whichChromium() {
  try {
    const output = execFileSync("which", ["chromium"], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
    const trimmed = String(output).trim().split("\n")[0];
    return trimmed || null;
  } catch {
    return null;
  }
}

function existingPath(candidate) {
  return candidate && existsSync(candidate) ? candidate : null;
}

function systemChromiumPath() {
  for (const candidate of SYSTEM_CHROMIUM_CANDIDATES) {
    const found = existingPath(candidate);
    if (found) return found;
  }
  return existingPath(whichChromium());
}

function downloadedChromiumPath(playwright) {
  try {
    const path = playwright.chromium.executablePath();
    return path && existsSync(path) ? path : null;
  } catch {
    return null;
  }
}

function resolveChromium(playwright) {
  const resolution = {
    project: process.cwd(),
    flag: chromiumFlag || null,
    env: process.env.PLAYWRIGHT_CHROMIUM_PATH || null,
    path: null,
  };
  if (resolution.flag) {
    resolution.path = existingPath(resolution.flag);
    return resolution;
  }
  if (resolution.env) {
    resolution.path = existingPath(resolution.env);
    return resolution;
  }
  resolution.path = downloadedChromiumPath(playwright);
  if (resolution.path) return resolution;
  resolution.path = systemChromiumPath();
  return resolution;
}

function noChromiumMessage(resolution) {
  const flagLine = resolution.flag ? "--chromium " + resolution.flag : "--chromium <path>";
  const envLine = resolution.env ? "$PLAYWRIGHT_CHROMIUM_PATH=" + resolution.env : "$PLAYWRIGHT_CHROMIUM_PATH";
  return [
    "snapshot: no chromium browser was found.",
    "",
    "Searched:",
    "  - the browser Playwright downloaded for " + resolution.project,
    "  - " + envLine,
    "  - " + flagLine,
    "  - /usr/bin/chromium",
    "  - /usr/bin/chromium-browser",
    "  - `which chromium`",
    "",
    "This script does not install a browser and does not fall back to another driver.",
    "Ask the user to install one or to point at an existing binary, then re-run:",
    "",
    "  npx playwright install chromium",
    "  PLAYWRIGHT_CHROMIUM_PATH=/path/to/chromium node .opencode/skills/unslop/scripts/snapshot.mjs ...",
    "  node .opencode/skills/unslop/scripts/snapshot.mjs --chromium /path/to/chromium ...",
  ].join("\n");
}

const playwright = loadPlaywright();
if (!playwright) {
  console.error([
    "snapshot: Playwright was not found in the project \"" + process.cwd() + "\" or in the global npm install.",
    "Searched the project directory and the global npm root (npm root -g, NODE_PATH, " + COMMON_GLOBAL_ROOT + ").",
  ].join("\n"));
  process.exit(2);
}

const resolution = resolveChromium(playwright);
if (!resolution.path) {
  console.error(noChromiumMessage(resolution));
  process.exit(2);
}

const { chromium } = playwright;
let browser;
try {
  browser = await chromium.launch({ headless: true, args: ["--no-sandbox"], executablePath: resolution.path });
} catch (error) {
  console.error([
    "snapshot: the chromium binary was found but failed to start.",
    "",
    "Browser: " + resolution.path,
    "Error: " + String(error && error.message ? error.message : error),
    "",
    "This script does not install a browser and does not fall back to another driver.",
  ].join("\n"));
  process.exit(2);
}
try {
  const page = await browser.newPage({ viewport: { width: Number(width), height: Number(height) }, colorScheme: scheme });
  await page.goto(target, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(600);
  await page.evaluate(async () => {
    const pause = (ms) => new Promise((done) => setTimeout(done, ms));
    const root = document.scrollingElement || document.documentElement;
    let last = root.scrollHeight;
    for (let step = 0; step < 30 && root.scrollTop < 20_000; step++) {
      window.scrollBy(0, window.innerHeight);
      await pause(150);
      const grown = root.scrollHeight;
      if (grown <= last && root.scrollTop + window.innerHeight >= grown) break;
      last = grown;
    }
    window.scrollTo(0, 0);
    const loaded = (image) =>
      new Promise((done) => {
        image.addEventListener("load", done, { once: true });
        image.addEventListener("error", done, { once: true });
      });
    const pending = [...document.images].filter((image) => !image.complete);
    await Promise.race([Promise.all(pending.map(loaded)), pause(5000)]);
  });
  const html = await page.evaluate(async ([label, scheme]) => {
    const LIMIT = 3_000_000;
    const absolute = (value, base = location.href) => {
      try {
        return new URL(value, base).href;
      } catch {
        return value;
      }
    };
    const inlined = new Map();
    const inline = async (href) => {
      if (!href || href.startsWith("data:")) return href;
      if (!inlined.has(href)) {
        inlined.set(
          href,
          fetch(href)
            .then((response) => (response.ok ? response.blob() : null))
            .then((blob) =>
              blob && blob.size < LIMIT
                ? new Promise((done) => {
                    const reader = new FileReader();
                    reader.onload = () => done(reader.result);
                    reader.readAsDataURL(blob);
                  })
                : href,
            )
            .catch(() => href),
        );
      }
      return inlined.get(href);
    };
    const urls = async (css, base) => {
      const found = [...css.matchAll(/url\((['"]?)(?!data:)([^)'"]+)\1\)/g)];
      let result = css;
      for (const [whole, , value] of found) {
        if (/^(#|%23)/.test(value.trim())) continue;
        const data = await inline(absolute(value.trim(), base));
        result = result.split(whole).join(`url("${data}")`);
      }
      return result;
    };

    const css = [];
    for (const sheet of document.styleSheets) {
      const owner = sheet.ownerNode;
      let text = "";
      let base = location.href;
      if (sheet.href) {
        base = sheet.href;
        text = await fetch(sheet.href).then((response) => (response.ok ? response.text() : "")).catch(() => "");
      } else if (owner && owner.textContent.trim()) {
        text = owner.textContent;
      }
      if (!text) {
        try {
          text = [...sheet.cssRules].map((rule) => rule.cssText).join("\n");
        } catch {}
      }
      const media = sheet.media && sheet.media.mediaText;
      css.push(media && media !== "all" ? `@media ${media} {\n${text}\n}` : text);
      css[css.length - 1] = await urls(css[css.length - 1], base);
    }

    const copy = document.documentElement.cloneNode(true);
    // Freeze the browser's selected image before removing responsive markup.
    const images = document.querySelectorAll("img");
    copy.querySelectorAll("img").forEach((node, index) => {
      const selected = images[index].currentSrc;
      if (selected) node.setAttribute("src", selected);
    });
    copy.querySelectorAll("script, noscript, link[rel='stylesheet'], link[rel='preload'], link[rel='modulepreload'], style").forEach((node) => node.remove());
    copy.querySelectorAll("[srcset]").forEach((node) => node.removeAttribute("srcset"));
    copy.querySelectorAll("source").forEach((node) => node.remove());
    copy.querySelectorAll("[loading]").forEach((node) => node.removeAttribute("loading"));
    for (const node of copy.querySelectorAll("img[src], video[poster], image")) {
      const attr = node.tagName === "VIDEO" ? "poster" : node.tagName.toLowerCase() === "image" ? "href" : "src";
      const value = node.getAttribute(attr);
      if (value) node.setAttribute(attr, await inline(absolute(value)));
    }
    copy.querySelectorAll("a[href]").forEach((node) => node.setAttribute("href", absolute(node.getAttribute("href"))));
    for (const node of copy.querySelectorAll("[style*='url(']")) {
      node.setAttribute("style", await urls(node.getAttribute("style"), location.href));
    }
    const style = document.createElement("style");
    let text = css.join("\n");
    if (scheme === "dark" || scheme === "light") {
      const other = scheme === "dark" ? "light" : "dark";
      text = text
        .replace(new RegExp(`prefers-color-scheme\\s*:\\s*${scheme}`, "g"), "min-width: 0px")
        .replace(new RegExp(`prefers-color-scheme\\s*:\\s*${other}`, "g"), "max-width: 0px");
      const meta = document.createElement("meta");
      meta.name = "color-scheme";
      meta.content = scheme;
      copy.querySelector("head").prepend(meta);
    }
    style.textContent = text;
    copy.querySelector("head").appendChild(style);
    if (label) {
      const meta = document.createElement("meta");
      meta.name = "unslop-pass";
      meta.content = label;
      copy.querySelector("head").prepend(meta);
    }
    return "<!doctype html>\n" + copy.outerHTML;
  }, [label ?? "", scheme]);
  mkdirSync(dirname(resolve(out)), { recursive: true });
  writeFileSync(resolve(out), html);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: resolve(out).replace(/\.html?$/, "") + ".live.png" });
  console.log(`saved ${resolve(out)}${label ? ` as ${label}` : ""}`);
} finally {
  await browser.close();
}
