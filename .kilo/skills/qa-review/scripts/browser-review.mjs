#!/usr/bin/env node
/**
 * browser-review.mjs — capture browser evidence for a QA review.
 *
 * Uses Playwright: the project's own copy when it has one, otherwise the global
 * install. When no downloaded browser exists, the system chromium binary is used.
 *
 * Usage:
 *   node browser-review.mjs --base-url <url> --route <path> [--route <path> ...]
 *                            [--scope <name>] [--task-id <id>] [--date <YYYY-MM-DD>]
 *                            [--artifact-dir <dir>]
 *                            [--project <dir with package.json>]
 *                            [--viewports "390x844,834x1112,1440x900,1920x1080,320x800"]
 *                            [--label <slug>] [--scheme light|dark|both]
 *                            [--component <css-selector>] [--compare <dir>]
 *
 * Without --artifact-dir the capture lands in the canonical artifacts folder of
 * the main checkout: <repo-root>/artifacts/<scope>/qa/<date>/<task-id>/.
 *
 * For every route x viewport x scheme it writes a screenshot plus console,
 * page-error and network-failure logs, then a summary.json and a notes.md for
 * the reviewer.
 * Exit codes: 0 capture completed, 2 fatal error.
 */
import {createRequire} from 'node:module';
import {resolve, join, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFile, mkdir, readdir, readFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';

const DEFAULT_VIEWPORTS = '390x844,834x1112,1440x900,1920x1080,320x800';
const SCHEMES = ['light', 'dark'];
const COMMON_GLOBAL_ROOT = '/usr/local/share/npm-global/lib/node_modules';
const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));

function usage() {
  return [
    'Usage: node browser-review.mjs --base-url <url> --route <path> [--route <path> ...]',
    '                                [--scope <name>] [--task-id <id>] [--date <YYYY-MM-DD>]',
    '                                [--artifact-dir <dir>]',
    '                                [--project <dir with package.json>]',
    '                                [--viewports "' + DEFAULT_VIEWPORTS + '"]',
    '                                [--label <slug>]',
    '                                [--scheme light|dark|both]',
    '                                [--component <css-selector>] [--component <css-selector> ...]',
    '                                [--compare <dir>]',
    '',
    'Options:',
    '  --base-url     Base URL of the running app (required).',
    '  --route        Route path to visit, repeatable (required).',
    '  --scope        Scope folder under artifacts/. Default: factory.',
    '  --task-id      Task folder under qa/<date>/. Default: adhoc.',
    '  --date         Capture date folder YYYY-MM-DD. Default: today.',
    '  --artifact-dir Optional override for the task directory.',
    '  --project      Directory whose package.json provides Playwright. Default: cwd.',
    '  --viewports    Comma-separated WIDTHxHEIGHT list. Default: ' + DEFAULT_VIEWPORTS,
    '  --label        Optional slug mixed into the artifact directory name.',
    '  --scheme       Colour scheme to capture: light, dark, or both. Default: light.',
    '  --component    CSS selector whose matched elements are captured as crops. Repeatable.',
    '  --compare      Directory holding a previous capture; writes a before | after sheet.',
    '  --help         Show this message and exit.',
  ].join('\n');
}

function fail(message) {
  process.stderr.write('browser-review: ' + message + '\n');
  process.exit(2);
}

function today() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return now.getFullYear() + '-' + month + '-' + day;
}

function mainCheckoutRoot() {
  try {
    const output = execFileSync('git', ['worktree', 'list', '--porcelain'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    for (const line of output.split('\n')) {
      if (line.startsWith('worktree ')) return line.slice('worktree '.length).trim();
    }
  } catch {
    /* git is not available here */
  }
  let current = SCRIPT_DIR;
  while (true) {
    if (existsSync(join(current, '.git'))) return current;
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return SCRIPT_DIR;
}

function taskDirectory(options) {
  if (options.artifactDir) return resolve(options.artifactDir);
  return join(mainCheckoutRoot(), 'artifacts', options.scope, 'qa', options.date, options.taskId);
}

function parseArgs(argv) {
  const options = {
    routes: [],
    viewports: DEFAULT_VIEWPORTS,
    project: process.cwd(),
    scheme: 'light',
    components: [],
    scope: 'factory',
    taskId: 'adhoc',
    date: today(),
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      const value = argv[i + 1];
      if (value === undefined) fail('missing value for ' + arg);
      i += 1;
      return value;
    };
    switch (arg) {
      case '--help':
      case '-h':
        process.stdout.write(usage() + '\n');
        process.exit(0);
        break;
      case '--base-url':
        options.baseUrl = next();
        break;
      case '--route':
        options.routes.push(next());
        break;
      case '--artifact-dir':
        options.artifactDir = next();
        break;
      case '--scope':
        options.scope = next();
        break;
      case '--task-id':
        options.taskId = next();
        break;
      case '--date':
        options.date = next();
        break;
      case '--project':
        options.project = next();
        break;
      case '--viewports':
        options.viewports = next();
        break;
      case '--label':
        options.label = next();
        break;
      case '--scheme':
        options.scheme = next();
        break;
      case '--component':
        options.components.push(next());
        break;
      case '--compare':
        options.compare = next();
        break;
      default:
        fail('unknown argument: ' + arg);
    }
  }
  if (!options.baseUrl) fail('--base-url is required');
  if (!options.routes.length) fail('at least one --route is required');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(options.date)) fail('--date must be YYYY-MM-DD');
  if (!options.scope) fail('--scope is required');
  if (!options.taskId) fail('--task-id is required');
  if (!['light', 'dark', 'both'].includes(options.scheme)) {
    fail('--scheme must be light, dark, or both');
  }
  try {
    new URL(options.baseUrl);
  } catch {
    fail('--base-url is not a valid URL: ' + options.baseUrl);
  }
  const viewports = options.viewports.split(',').map(part => part.trim()).filter(Boolean).map(part => {
    const match = /^(\d+)x(\d+)$/.exec(part);
    if (!match) fail('invalid viewport: ' + part + ' (expected WIDTHxHEIGHT)');
    return {width: Number(match[1]), height: Number(match[2]), name: part};
  });
  if (!viewports.length) fail('--viewports produced no usable entries');
  options.viewports = viewports;
  return options;
}

function routeSlug(route) {
  const slug = route.replace(/^\/+/, '').replace(/\/+$/, '').replace(/[^A-Za-z0-9._-]+/g, '-');
  return slug || 'root';
}

function joinUrl(baseUrl, route) {
  const base = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const path = route.startsWith('/') ? route : '/' + route;
  return base + path;
}

function schemeList(scheme) {
  return scheme === 'both' ? SCHEMES : [scheme];
}

function screenshotName(scheme, viewport, all) {
  if (all) return viewport.name + '-' + scheme + '.png';
  return scheme === 'dark' ? 'full-dark.png' : 'full.png';
}

/* ---------- Playwright resolution ---------- */

let cachedGlobalRoots = null;

function npmGlobalRoot() {
  if (cachedGlobalRoots) return cachedGlobalRoots;
  const roots = [];
  for (const entry of (process.env.NODE_PATH || '').split(process.platform === 'win32' ? ';' : ':')) {
    const trimmed = entry.trim();
    if (trimmed) roots.push(trimmed);
  }
  try {
    const output = execFileSync('npm', ['root', '-g'], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']});
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
    dirs.push(join(root, 'playwright'));
    dirs.push(join(root, 'playwright-core'));
    dirs.push(join(root, '@playwright', 'mcp', 'node_modules', 'playwright'));
    dirs.push(join(root, '@playwright', 'mcp', 'node_modules', 'playwright-core'));
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
      const found = localRequire.resolve(name, {paths: [moduleDir, dirname(moduleDir)]});
      return localRequire(found);
    } catch {
      /* try the next candidate */
    }
  }
  return null;
}

async function loadPlaywright(projectDir) {
  const project = resolve(projectDir);
  try {
    const require = createRequire(resolve(project, 'package.json'));
    return require('playwright');
  } catch {
    /* the project has no Playwright of its own */
  }
  for (const moduleDir of globalModuleDirs()) {
    const found = requireFrom(moduleDir, ['playwright', 'playwright-core']);
    if (found) return found;
  }
  return null;
}

/* ---------- browser binary ---------- */

function whichChromium() {
  try {
    const output = execFileSync('which', ['chromium'], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']});
    const trimmed = String(output).trim().split('\n')[0];
    return trimmed || null;
  } catch {
    return null;
  }
}

function systemChromiumPath() {
  const candidates = [];
  if (process.env.PLAYWRIGHT_CHROMIUM_PATH) candidates.push(process.env.PLAYWRIGHT_CHROMIUM_PATH);
  candidates.push('/usr/bin/chromium', '/usr/bin/chromium-browser');
  const which = whichChromium();
  if (which) candidates.push(which);
  for (const candidate of candidates) {
    if (candidate && existsSync(candidate)) return candidate;
  }
  return null;
}

function downloadedChromiumPath(playwright) {
  try {
    const path = playwright.chromium.executablePath();
    return path && existsSync(path) ? path : null;
  } catch {
    return null;
  }
}

const OVERFLOW_EXPRESSION = '(() => {const r = document.documentElement; return r.scrollWidth > r.clientWidth + 1;})()';

function boxesExpression(selectors) {
  return '(() => {' +
    'const out = [];' +
    'for (const selector of ' + JSON.stringify(selectors) + ') {' +
    '  let nodes = [];' +
    '  try { nodes = Array.from(document.querySelectorAll(selector)); } catch (e) { continue; }' +
    '  for (const node of nodes) {' +
    '    const box = node.getBoundingClientRect();' +
    '    if (box.width < 1 || box.height < 1) continue;' +
    '    out.push({x: box.left + window.scrollX, y: box.top + window.scrollY, width: box.width, height: box.height});' +
    '  }' +
    '}' +
    'return out;' +
    '})()';
}

class PlaywrightPage {
  constructor(context, page) {
    this.context = context;
    this.page = page;
    this.consoleErrors = [];
    this.pageErrors = [];
    this.networkFailures = [];
    page.on('console', message => {
      if (message.type() === 'error') this.consoleErrors.push(message.text());
    });
    page.on('pageerror', error => this.pageErrors.push(String(error.stack || error)));
    page.on('response', response => {
      if (response.status() >= 400) {
        this.networkFailures.push({
          url: response.url(),
          status: response.status(),
          method: response.request().method(),
        });
      }
    });
    page.on('requestfailed', request => {
      this.networkFailures.push({
        url: request.url(),
        status: null,
        method: request.method(),
        error: request.failure() ? request.failure().errorText : 'request failed',
      });
    });
  }

  async setup() {
    return undefined;
  }

  async goto(url) {
    try {
      await this.page.goto(url, {waitUntil: 'networkidle', timeout: 30000});
      return {ok: true, waitUntil: 'networkidle'};
    } catch (error) {
      try {
        await this.page.goto(url, {waitUntil: 'load', timeout: 30000});
        return {ok: true, waitUntil: 'load', note: 'networkidle timed out, fell back to load'};
      } catch (fallbackError) {
        return {ok: false, waitUntil: 'load', error: String(fallbackError.message || fallbackError)};
      }
    }
  }

  async evaluate(expression) {
    return this.page.evaluate(expression).catch(() => null);
  }

  async screenshotFull() {
    return this.page.screenshot({fullPage: true});
  }

  async screenshotClip(box) {
    try {
      return await this.page.screenshot({
        fullPage: true,
        clip: {x: box.x, y: box.y, width: box.width, height: box.height},
      });
    } catch {
      return this.page.screenshot({
        clip: {x: box.x, y: box.y, width: box.width, height: box.height},
      });
    }
  }

  logs() {
    return {consoleErrors: this.consoleErrors, pageErrors: this.pageErrors, networkFailures: this.networkFailures};
  }

  async close() {
    await this.context.close();
  }
}

/* ---------- before/after sheets ---------- */

function beforeNames(scheme, viewport) {
  if (scheme === 'dark') return [viewport.name + '-dark.png', 'full-dark.png'];
  return [viewport.name + '-light.png', 'full.png', 'full-light.png'];
}

async function findBeforeImage(compareDir, label, slug, viewport, scheme) {
  const names = beforeNames(scheme, viewport);
  const roots = [
    compareDir,
    label ? join(compareDir, label) : null,
  ].filter(Boolean);

  for (const root of roots) {
    for (const name of names) {
      const candidate = join(root, slug, viewport.name, scheme, name);
      if (existsSync(candidate)) return candidate;
    }
  }

  let children = [];
  try {
    children = await readdir(compareDir, {withFileTypes: true});
  } catch {
    return null;
  }
  for (const child of children) {
    if (!child.isDirectory()) continue;
    for (const name of names) {
      const candidate = join(compareDir, child.name, slug, viewport.name, scheme, name);
      if (existsSync(candidate)) return candidate;
    }
  }
  return null;
}

function sheetHtml(beforeUri, afterUri, beforeLabel, afterLabel) {
  return '<!doctype html><meta charset="utf-8"><style>' +
    'body{margin:0;background:#6b6f73;font:600 14px system-ui;display:flex;gap:12px;padding:12px;align-items:flex-start}' +
    'figure{margin:0;background:#fff;color:#111;flex:1 1 0;min-width:0}' +
    'figcaption{padding:6px 8px;font-size:13px}' +
    'img{display:block;width:100%;height:auto}' +
    '</style>' +
    '<figure><figcaption>BEFORE · ' + beforeLabel + '</figcaption><img src="' + beforeUri + '"></figure>' +
    '<figure><figcaption>AFTER · ' + afterLabel + '</figcaption><img src="' + afterUri + '"></figure>';
}

async function writeCompareSheet(browser, beforeBuffer, afterBuffer, sheetPath, beforeLabel, afterLabel) {
  const uri = buffer => 'data:image/png;base64,' + buffer.toString('base64');
  const html = sheetHtml(uri(beforeBuffer), uri(afterBuffer), beforeLabel, afterLabel);
  const context = await browser.handle.newContext({viewport: {width: 1600, height: 900}});
  const page = await context.newPage();
  await page.setContent(html, {waitUntil: 'load'});
  await page.evaluate(async () => {
    await Promise.all(Array.from(document.images).map(image =>
      image.complete ? null : new Promise(resolve => { image.onload = resolve; })));
  });
  await page.screenshot({path: sheetPath, fullPage: true});
  await context.close();
}

/* ---------- capture ---------- */

function renderNotes(options, summary) {
  const lines = [];
  lines.push('# QA capture — ' + options.taskId);
  lines.push('');
  lines.push('- Command: `' + process.argv.join(' ') + '`');
  lines.push('- Scope: ' + options.scope);
  lines.push('- Task: ' + options.taskId);
  lines.push('- Date: ' + options.date);
  lines.push('- Routes: ' + options.routes.join(', '));
  lines.push('- Viewports: ' + options.viewports.map(viewport => viewport.name).join(', '));
  lines.push('- Schemes: ' + schemeList(options.scheme).join(', '));
  lines.push('');
  lines.push('| Scheme | Console errors | Page errors | Network failures |');
  lines.push('|---|---|---|---|');
  for (const scheme of schemeList(options.scheme)) {
    const rows = summary.results.filter(entry => entry.scheme === scheme);
    const sum = field => rows.reduce((total, entry) => total + (entry[field] || 0), 0);
    lines.push('| ' + scheme + ' | ' + sum('console_error_count') + ' | ' +
      sum('page_error_count') + ' | ' + sum('network_failure_count') + ' |');
  }
  lines.push('');
  lines.push('What was checked and the expected vs actual result are written by the reviewer.');
  return lines.join('\n') + '\n';
}

async function captureEntry(session, options, route, viewport, scheme, allSchemes) {
  const url = joinUrl(options.baseUrl, route);
  const dir = join(options.artifactRoot, routeSlug(route), viewport.name, scheme);
  await mkdir(dir, {recursive: true});

  const name = screenshotName(scheme, viewport, allSchemes);
  const screenshot = join(dir, name);
  const entry = {
    route,
    viewport: viewport.name,
    scheme,
    width: viewport.width,
    height: viewport.height,
    url,
    screenshot,
    components: [],
    compare: null,
    console_errors: [],
    page_errors: [],
    network_failures: [],
    console_error_count: 0,
    page_error_count: 0,
    network_failure_count: 0,
    horizontal_overflow: null,
    horizontal_overflow_check_passed: null,
    navigation: null,
    error: null,
  };

  try {
    await session.setup(viewport, scheme);
    const navigation = await session.goto(url);
    entry.navigation = navigation;
    await new Promise(resolveWait => setTimeout(resolveWait, 750));

    const overflow = await session.evaluate(OVERFLOW_EXPRESSION);
    entry.horizontal_overflow = typeof overflow === 'boolean' ? overflow : null;
    entry.horizontal_overflow_check_passed = entry.horizontal_overflow === null ? null : !entry.horizontal_overflow;

    const image = await session.screenshotFull();
    await writeFile(screenshot, image);

    if (options.components.length) {
      const boxes = await session.evaluate(boxesExpression(options.components));
      if (Array.isArray(boxes)) {
        for (let index = 0; index < boxes.length; index += 1) {
          const componentName = allSchemes
            ? 'component-' + (index + 1) + '-' + scheme + '.png'
            : 'component-' + (index + 1) + '.png';
          const componentPath = join(dir, componentName);
          try {
            await writeFile(componentPath, await session.screenshotClip(boxes[index]));
            entry.components.push(componentPath);
          } catch {
            entry.components.push(null);
          }
        }
      }
    }

    const logs = session.logs();
    entry.console_errors = logs.consoleErrors;
    entry.page_errors = logs.pageErrors;
    entry.network_failures = logs.networkFailures;
    entry.console_error_count = logs.consoleErrors.length;
    entry.page_error_count = logs.pageErrors.length;
    entry.network_failure_count = logs.networkFailures.length;

    await writeFile(join(dir, 'console.log'), logs.consoleErrors.join('\n') + (logs.consoleErrors.length ? '\n' : ''));
    await writeFile(join(dir, 'page-errors.log'), logs.pageErrors.join('\n') + (logs.pageErrors.length ? '\n' : ''));
    await writeFile(join(dir, 'network.json'), JSON.stringify(logs.networkFailures, null, 2));
  } catch (error) {
    entry.error = String(error.message || error);
    await writeFile(join(dir, 'console.log'), '').catch(() => {});
    await writeFile(join(dir, 'page-errors.log'), '').catch(() => {});
    await writeFile(join(dir, 'network.json'), '[]').catch(() => {});
  }
  return entry;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const playwright = await loadPlaywright(options.project);
  const allSchemes = options.scheme === 'both';
  const schemes = schemeList(options.scheme);

  if (!playwright) {
    fail('Playwright was not found in the project "' + resolve(options.project) +
      '" or in the global npm install. Searched the project directory and the global npm root' +
      ' (npm root -g, NODE_PATH, ' + COMMON_GLOBAL_ROOT + ').');
  }

  options.taskDir = taskDirectory(options);
  options.artifactRoot = options.label
    ? join(options.taskDir, options.label)
    : options.taskDir;

  const launchOptions = {headless: true, args: ['--no-sandbox']};
  const executablePath = downloadedChromiumPath(playwright) || systemChromiumPath();
  if (executablePath) launchOptions.executablePath = executablePath;

  const summary = {
    base_url: options.baseUrl,
    project: resolve(options.project),
    artifact_dir: options.artifactRoot,
    task_dir: options.taskDir,
    scope: options.scope,
    task_id: options.taskId,
    date: options.date,
    scheme: options.scheme,
    viewports: options.viewports.map(viewport => viewport.name),
    routes: options.routes,
    components: options.components,
    compare: options.compare || null,
    driver: 'playwright',
    browser_executable: executablePath || null,
    results: [],
  };

  let browser = null;
  try {
    browser = {kind: 'playwright', handle: await playwright.chromium.launch(launchOptions)};
  } catch (error) {
    fail('could not launch chromium: ' + (error.message || error));
  }

  try {
    for (const route of options.routes) {
      for (const viewport of options.viewports) {
        for (const scheme of schemes) {
          const context = await browser.handle.newContext({
            viewport: {width: viewport.width, height: viewport.height},
            locale: 'en-US',
            timezoneId: 'UTC',
            colorScheme: scheme,
          });
          const page = await context.newPage();
          page.setDefaultTimeout(15000);
          const session = new PlaywrightPage(context, page);

          const entry = await captureEntry(session, options, route, viewport, scheme, allSchemes);
          summary.results.push(entry);

          if (options.compare && !entry.error) {
            const before = await findBeforeImage(resolve(options.compare), options.label, routeSlug(route), viewport, scheme);
            if (before) {
              const sheetPath = join(options.artifactRoot, routeSlug(route), viewport.name, scheme, 'compare.png');
              try {
                await writeCompareSheet(
                  browser,
                  await readFile(before),
                  await readFile(entry.screenshot),
                  sheetPath,
                  resolve(options.compare).split('/').pop() || 'before',
                  options.label || 'after',
                );
                entry.compare = sheetPath;
              } catch (error) {
                entry.compare_error = String(error.message || error);
              }
            }
          }

          await session.close();
        }
      }
    }
  } finally {
    await browser.handle.close().catch(() => {});
  }

  await mkdir(options.taskDir, {recursive: true});
  await writeFile(join(options.taskDir, 'summary.json'), JSON.stringify(summary, null, 2));
  await writeFile(join(options.taskDir, 'notes.md'), renderNotes(options, summary));
  process.stdout.write(JSON.stringify(summary) + '\n');
}

main().catch(error => {
  fail(String(error && error.stack ? error.stack : error));
});
