#!/usr/bin/env node
/**
 * browser-review.mjs — capture browser evidence for a QA review.
 *
 * Uses Playwright: the project's own copy when it has one, otherwise the global
 * install. The browser binary is the first of: --chromium <path>,
 * $PLAYWRIGHT_CHROMIUM_PATH, the browser Playwright downloaded, the system chromium.
 * The script never installs a browser and never falls back to another driver.
 *
 * Usage:
 *   node browser-review.mjs --base-url <url> --route <path> [--route <path> ...]
 *                            [--scope <name>] [--task-id <id>] [--date <YYYY-MM-DD>]
 *                            [--artifact-dir <dir>]
 *                            [--project <dir with package.json>]
 *                            [--viewports "390x844,834x1112,1440x900,1920x1080,320x800"]
 *                            [--label <slug>] [--scheme light|dark|both]
 *                            [--component <css-selector>] [--compare <dir>]
 *                            [--chromium <path>]
 *
 * All output stays in the caller's Git worktree artifacts folder (cwd for
 * non-Git fixtures): <worktree>/artifacts/<scope>/qa/<date>/<task-id>/.
 *
 * For every route x viewport x scheme it writes a screenshot plus console,
 * page-error and network-failure logs, then a summary.json and a notes.md for
 * the reviewer.
 * Exit codes: 0 capture completed, 2 fatal error.
 */
import {createRequire} from 'node:module';
import {resolve, join, dirname, relative, isAbsolute} from 'node:path';
import {fileURLToPath} from 'node:url';
import {writeFile, mkdir, mkdtemp, readdir, readFile, realpath, lstat} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {execFileSync} from 'node:child_process';

const DEFAULT_VIEWPORTS = '390x844,834x1112,1440x900,1920x1080,320x800';
const SCHEMES = ['light', 'dark'];
const COMMON_GLOBAL_ROOT = '/usr/local/share/npm-global/lib/node_modules';

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
    '                                [--chromium <path>]',
    '',
    'Options:',
    '  --base-url     Base URL of the running app (required).',
    '  --route        Route path to visit, repeatable (required).',
    '  --scope        Scope folder under artifacts/. Default: factory.',
    '  --task-id      Task folder under qa/<date>/. Default: adhoc.',
    '  --date         Capture date folder YYYY-MM-DD. Default: today.',
    '  --artifact-dir Override within caller worktree artifacts/ only (no symlinks).',
    '  --project      Directory whose package.json provides Playwright. Default: cwd.',
    '  --viewports    Comma-separated WIDTHxHEIGHT list. Default: ' + DEFAULT_VIEWPORTS,
    '  --label        Optional slug mixed into the artifact directory name.',
    '  --scheme       Colour scheme to capture: light, dark, or both. Default: light.',
    '  --component    CSS selector whose matched elements are captured as crops. Repeatable.',
    '  --compare      Directory holding a previous capture; writes a before | after sheet.',
    '  --chromium     Path to a chromium binary. Overrides $PLAYWRIGHT_CHROMIUM_PATH.',
    '  --storage-state Ignored local Playwright state JSON (read only; never saved).',
    '  --navigation   Ignored local JSON: approved:true, login:[], steps:[].',
    '                 Actions: goto/path, fill/selector/env, click/selector/intent,',
    '                 waitForURL/path, waitForSelector/selector. No literal fill values.',
    '                 Login requires authenticatedPath. State/login require authenticatedSelector.',
    '                 Steps run after each target goto; page changes require waitForURL.',
    '  --allow-destructive Explicit authorization for steps with intent:destructive.',
    '  --help         Show this message and exit.',
  ].join('\n');
}

function abort(message) {
  process.stderr.write(message + '\n');
  process.exit(2);
}

class ReviewError extends Error {}

function fail(message) {
  throw new ReviewError('browser-review: ' + message);
}

function today() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const day = String(now.getDate()).padStart(2, '0');
  return now.getFullYear() + '-' + month + '-' + day;
}

export function callerRoot(cwd = process.cwd()) {
  try {
    return execFileSync('git', ['rev-parse', '--show-toplevel'], {
      cwd,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'ignore'],
      env: Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith('GIT_'))),
    }).trim();
  } catch {
    return resolve(cwd); // Non-Git fixtures remain confined to their own cwd.
  }
}

function safeSegment(value, name) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9_-][A-Za-z0-9._-]*$/.test(value)) {
    fail(name + ' must be a safe path segment');
  }
}

export async function artifactPath(path) {
  const root = resolve(callerRoot(), 'artifacts');
  const target = resolve(path);
  const rel = relative(root, target);
  if (rel === '..' || rel.startsWith('../') || isAbsolute(rel)) fail('output must stay inside caller worktree artifacts/');
  // Check existing ancestors even when the leaf does not exist. No symlinks in
  // the output tree, including in-root links and links at the artifacts root.
  if (await realpath(dirname(root)) !== dirname(root)) fail('artifact root has a symlink ancestor');
  let current = root;
  for (const segment of ['', ...rel.split('/').filter(Boolean)]) {
    if (segment) current = join(current, segment);
    try {
      if ((await lstat(current)).isSymbolicLink() || await realpath(current) !== current) {
        fail('artifact output has a symlink ancestor or destination');
      }
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
  }
  return target;
}

async function outputFile(path, data) {
  return writeFile(await artifactPath(path), data);
}

export function taskDirectory(options) {
  for (const key of ['scope', 'taskId', 'date']) safeSegment(options[key], key);
  if (options.label !== undefined) safeSegment(options.label, 'label');
  if (options.artifactDir !== undefined) return resolve(options.artifactDir);
  return join(callerRoot(), 'artifacts', options.scope, 'qa', options.date, options.taskId);
}

export async function prepareArtifacts(options) {
  options.taskDir = await artifactPath(taskDirectory(options));
  options.artifactRoot = await artifactPath(options.label ? join(options.taskDir, options.label) : options.taskDir);
  // Refuse pre-existing output links before launching or contacting the app.
  async function inspect(path) {
    await artifactPath(path);
    let children;
    try { children = await readdir(path, {withFileTypes: true}); }
    catch (error) { if (error.code === 'ENOENT' || error.code === 'ENOTDIR') return; throw error; }
    for (const child of children) {
      const target = join(path, child.name);
      await artifactPath(target);
      if (child.isDirectory()) await inspect(target);
    }
  }
  await inspect(options.taskDir);
}

export async function browserTemp() {
  const parent = await artifactPath(join(callerRoot(), 'artifacts', 'tmp'));
  await mkdir(parent, {recursive: true});
  const temp = await mkdtemp(join(parent, 'browser-'));
  const saved = Object.fromEntries(['TMPDIR', 'TMP', 'TEMP'].map(key => [key, process.env[key]]));
  // Chromium's singleton Unix socket has a small pathname limit. A relative
  // TMPDIR keeps that socket short without writing outside this worktree.
  const envPath = relative(process.cwd(), temp);
  await artifactPath(resolve(envPath));
  for (const key of Object.keys(saved)) process.env[key] = envPath;
  return {path: temp, restore() {
    for (const [key, value] of Object.entries(saved)) {
      if (value === undefined) delete process.env[key]; else process.env[key] = value;
    }
  }};
}

export function parseArgs(argv) {
  const options = {
    routes: [],
    viewports: DEFAULT_VIEWPORTS,
    project: process.cwd(),
    scheme: 'light',
    components: [],
    scope: 'factory',
    taskId: 'adhoc',
    date: today(),
    chromium: null,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    const next = () => {
      const value = argv[i + 1];
      if (value === undefined) fail('missing option value');
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
      case '--chromium':
        options.chromium = next();
        break;
      case '--storage-state':
        options.storageState = next();
        break;
      case '--navigation':
        options.navigation = next();
        break;
      case '--allow-destructive':
        options.allowDestructive = true;
        break;
      default:
        fail('unknown argument (literal credentials are not accepted)');
    }
  }
  if (!options.baseUrl) fail('--base-url is required');
  if (!options.routes.length) fail('at least one --route is required');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(options.date)) fail('--date must be YYYY-MM-DD');
  if (!options.scope) fail('--scope is required');
  if (!options.taskId) fail('--task-id is required');
  taskDirectory(options);
  if (!['light', 'dark', 'both'].includes(options.scheme)) {
    fail('--scheme must be light, dark, or both');
  }
  safeUrl(options.baseUrl);
  for (const route of options.routes) safeUrl(joinUrl(options.baseUrl, route));
  const viewports = options.viewports.split(',').map(part => part.trim()).filter(Boolean).map(part => {
    const match = /^(\d+)x(\d+)$/.exec(part);
    if (!match) fail('invalid viewport (expected WIDTHxHEIGHT)');
    return {width: Number(match[1]), height: Number(match[2]), name: part};
  });
  if (!viewports.length) fail('--viewports produced no usable entries');
  options.viewports = viewports;
  return options;
}

function routeSlug(route) {
  const slug = route.replace(/^\/+/, '').replace(/\/+$/, '').replace(/[^A-Za-z0-9._-]+/g, '-');
  return !slug || slug === '.' || slug === '..' ? 'root' : slug;
}

function joinUrl(baseUrl, route) {
  const base = baseUrl.endsWith('/') ? baseUrl.slice(0, -1) : baseUrl;
  const path = route.startsWith('/') ? route : '/' + route;
  return base + path;
}

const ACCESS_REQUEST = 'Ask the user for authorized test access via named environment variables or an ignored local Playwright storage-state file. For MFA/SSO, ask the user to log in manually and supply that state; never bypass authentication.';

export function safeUrl(value, baseUrl) {
  let url;
  try { url = new URL(value, baseUrl); } catch { fail('invalid navigation URL'); }
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash ||
      (baseUrl && url.origin !== new URL(baseUrl).origin)) {
    fail('navigation URLs must be HTTP(S), same-origin, and contain no credentials, query or fragment');
  }
  return url.href;
}

export function validateNavigation(config, baseUrl, allowDestructive = false, usesStorageState = false) {
  if (!config || typeof config !== 'object' || Array.isArray(config) || config.approved !== true ||
      Object.keys(config).some(key => !['approved', 'login', 'steps', 'authenticatedPath', 'authenticatedSelector'].includes(key))) {
    fail('navigation JSON requires approved:true and only login, steps, authenticatedPath, authenticatedSelector');
  }
  for (const [phase, steps] of [['login', config.login || []], ['steps', config.steps || []]]) {
    if (!Array.isArray(steps) || steps.length > 50) fail('navigation steps must be an array of at most 50 actions');
    for (const step of steps) {
      const fields = {
        goto: ['action', 'path'], fill: ['action', 'selector', 'env'],
        click: ['action', 'selector', 'intent'], waitForURL: ['action', 'path'],
        waitForSelector: ['action', 'selector'],
      };
      const allowed = step && fields[step.action];
      if (!allowed || Object.keys(step).some(key => !allowed.includes(key)) ||
          allowed.some(key => typeof step[key] !== 'string' || !step[key])) {
        fail('invalid navigation action; literal values and executable code are forbidden');
      }
      if (step.path) safeUrl(step.path, baseUrl);
      if (step.env && !/^[A-Za-z_][A-Za-z0-9_]*$/.test(step.env)) fail('fill requires an environment variable name');
      if (step.intent && (!['navigation', 'login', 'destructive'].includes(step.intent) ||
          (step.intent === 'login' && phase !== 'login') ||
          (step.intent === 'destructive' && !allowDestructive))) {
        fail('click requires reviewed navigation/login intent or explicit --allow-destructive authorization');
      }
    }
  }
  if (config.login?.length && !config.authenticatedPath) fail('login requires authenticatedPath');
  if ((usesStorageState || config.login?.length || config.authenticatedSelector !== undefined) &&
      (typeof config.authenticatedSelector !== 'string' || !config.authenticatedSelector.trim())) {
    fail('authenticated review requires an app-specific authenticatedSelector in --navigation. ' + ACCESS_REQUEST);
  }
  if (config.authenticatedPath) safeUrl(config.authenticatedPath, baseUrl);
  return config;
}

export async function localJson(path, projectDir, state = false) {
  try {
    const root = execFileSync('git', ['rev-parse', '--show-toplevel'], {
      cwd: projectDir, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'],
    }).trim();
    const absolute = resolve(projectDir, path);
    const canonical = await realpath(absolute);
    const rel = relative(root, canonical);
    if (rel.startsWith('..') || isAbsolute(rel) || canonical !== absolute || !(await lstat(absolute)).isFile()) {
      fail('local authentication files must be regular, non-symlink files inside the project repository');
    }
    const tracked = execFileSync('git', ['ls-files', '--', rel], {
      cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore'],
    });
    if (tracked.trim()) fail('local authentication files must not be tracked');
    execFileSync('git', ['check-ignore', '-q', '--', rel], {cwd: root, stdio: 'ignore'});
    const data = JSON.parse(await readFile(absolute, 'utf8'));
    if (state && (!data || !Array.isArray(data.cookies) || !Array.isArray(data.origins))) {
      fail('invalid Playwright storage state');
    }
    return data;
  } catch {
    fail('cannot use local authentication JSON: require an existing, ignored, untracked regular file inside --project. ' + ACCESS_REQUEST);
  }
}

export async function runSteps(page, steps, baseUrl, env) {
  for (let index = 0; index < steps.length; index += 1) {
    const step = steps[index];
    try {
      if (step.action !== 'goto') safeUrl(page.url(), baseUrl);
      if (step.action === 'goto') await page.goto(safeUrl(step.path, baseUrl), {waitUntil: 'load'});
      if (step.action === 'fill') {
        const value = env[step.env];
        if (!value) fail('missing login environment variable. ' + ACCESS_REQUEST);
        await page.locator(step.selector).fill(value);
      }
      if (step.action === 'click') await page.locator(step.selector).click();
      if (step.action === 'waitForURL') await page.waitForURL(safeUrl(step.path, baseUrl), {waitUntil: 'load'});
      if (step.action === 'waitForSelector') await page.locator(step.selector).waitFor({state: 'visible'});
      safeUrl(page.url(), baseUrl);
    } catch {
      fail('approved navigation step ' + (index + 1) + ' failed (details withheld). ' + ACCESS_REQUEST);
    }
  }
}

async function proveAuthentication(page, config) {
  if (!config.authenticatedSelector) return;
  try {
    await page.waitForLoadState('load');
    await page.locator(config.authenticatedSelector).waitFor({state: 'visible', timeout: 15000});
  } catch {
    fail('signed-in marker was not visible; protected interaction and capture withheld. ' + ACCESS_REQUEST);
  }
}

export function stateSecrets(state) {
  return [...(state.cookies || []).map(cookie => cookie.value),
    ...(state.origins || []).flatMap(origin => (origin.localStorage || []).map(item => item.value))]
    .filter(value => typeof value === 'string' && value.length);
}

export function redact(text, secrets = []) {
  let result = String(text);
  for (const secret of secrets.filter(Boolean).sort((a, b) => b.length - a.length)) {
    result = result.split(secret).join('[REDACTED]').split(encodeURIComponent(secret)).join('[REDACTED]');
  }
  return result.replace(/https?:\/\/[^\s"'<>]+/gi, value => {
    try { return new URL(value).origin; } catch { return '[URL withheld]'; }
  }).replace(/\b(authorization|cookie|set-cookie|password|token|secret)\b[^\n]*/gi, '[sensitive details withheld]');
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

const SYSTEM_CHROMIUM_CANDIDATES = ['/usr/bin/chromium', '/usr/bin/chromium-browser'];

function whichChromium() {
  try {
    const output = execFileSync('which', ['chromium'], {encoding: 'utf8', stdio: ['ignore', 'pipe', 'ignore']});
    const trimmed = String(output).trim().split('\n')[0];
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

function resolveChromium(playwright, options) {
  const resolution = {
    project: resolve(options.project),
    flag: options.chromium || null,
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
  const flagLine = resolution.flag ? '--chromium ' + resolution.flag : '--chromium <path>';
  const envLine = resolution.env
    ? '$PLAYWRIGHT_CHROMIUM_PATH=' + resolution.env
    : '$PLAYWRIGHT_CHROMIUM_PATH';
  return [
    'browser-review: no chromium browser was found.',
    '',
    'Searched:',
    '  - the browser Playwright downloaded for ' + resolution.project,
    '  - ' + envLine,
    '  - ' + flagLine,
    '  - /usr/bin/chromium',
    '  - /usr/bin/chromium-browser',
    '  - `which chromium`',
    '',
    'This script does not install a browser and does not fall back to another driver.',
    'Ask the user to install one or to point at an existing binary, then re-run:',
    '',
    '  npx playwright install chromium',
    '  PLAYWRIGHT_CHROMIUM_PATH=/path/to/chromium node .kilo/skills/qa-review/scripts/browser-review.mjs ...',
    '  node .kilo/skills/qa-review/scripts/browser-review.mjs --chromium /path/to/chromium ...',
  ].join('\n');
}

function launchFailureMessage(resolution, error) {
  return [
    'browser-review: the chromium binary was found but failed to start.',
    '',
    'Browser: ' + resolution.path,
    'Error: browser launch failed (details withheld to protect credentials).',
    '',
    'This script does not install a browser and does not fall back to another driver.',
    'Ask the user to point at a working binary, then re-run:',
    '',
    '  node .kilo/skills/qa-review/scripts/browser-review.mjs --chromium /path/to/chromium ...',
  ].join('\n');
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

export class PlaywrightPage {
  constructor(context, page, secrets = []) {
    this.context = context;
    this.page = page;
    this.secrets = secrets;
    this.consoleErrors = [];
    this.pageErrors = [];
    this.networkFailures = [];
    this.accessDenied = false;
    page.on('console', message => {
      if (message.type() === 'error') this.consoleErrors.push('Console error (text withheld to protect private payloads)');
    });
    page.on('pageerror', () => this.pageErrors.push('Page error (details withheld to protect private payloads)'));
    page.on('response', response => {
      if ([401, 403].includes(response.status())) this.accessDenied = true;
      if (response.status() >= 400) {
        this.networkFailures.push({
          url: redact(response.url(), this.secrets),
          status: response.status(),
          method: response.request().method(),
        });
      }
    });
    page.on('requestfailed', request => {
      this.networkFailures.push({
        url: redact(request.url(), this.secrets),
        status: null,
        method: request.method(),
        error: 'request failed (details withheld)',
      });
    });
  }

  async setup() {
    this.consoleErrors = [];
    this.pageErrors = [];
    this.networkFailures = [];
    this.accessDenied = false;
  }

  async goto(url) {
    try {
      const response = await this.page.goto(url, {waitUntil: 'networkidle', timeout: 30000});
      return {ok: ![401, 403].includes(response?.status()), waitUntil: 'networkidle'};
    } catch (error) {
      try {
        const response = await this.page.goto(url, {waitUntil: 'load', timeout: 30000});
        return {ok: ![401, 403].includes(response?.status()), waitUntil: 'load', note: 'networkidle timed out, fell back to load'};
      } catch (fallbackError) {
        return {ok: false, waitUntil: 'load', error: 'navigation failed (details withheld)'};
      }
    }
  }

  async evaluate(expression) {
    return this.page.evaluate(expression).catch(() => null);
  }

  async screenshotFull() {
    return this.page.screenshot({fullPage: true, mask: this.masks()});
  }

  masks() {
    const masks = [this.page.locator('input, textarea, [contenteditable], [data-qa-sensitive]')];
    for (const secret of this.secrets) masks.push(this.page.getByText(secret, {exact: false}));
    return masks;
  }

  async screenshotClip(box) {
    try {
      return await this.page.screenshot({
        fullPage: true,
        mask: this.masks(),
        clip: {x: box.x, y: box.y, width: box.width, height: box.height},
      });
    } catch {
      return this.page.screenshot({
        mask: this.masks(),
        clip: {x: box.x, y: box.y, width: box.width, height: box.height},
      });
    }
  }

  logs() {
    return {consoleErrors: this.consoleErrors, pageErrors: this.pageErrors, networkFailures: this.networkFailures};
  }

  async close() {
    await this.page.close();
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
  await artifactPath(sheetPath);
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
  lines.push('- Command: `browser-review.mjs` (arguments omitted to protect local access configuration)');
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

export async function captureEntry(session, options, route, viewport, scheme, allSchemes) {
  const url = joinUrl(options.baseUrl, route);
  safeSegment(viewport.name, 'viewport');
  safeSegment(scheme, 'scheme');
  const dir = await artifactPath(join(options.artifactRoot, routeSlug(route), viewport.name, scheme));
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
    if (!navigation.ok) fail('target navigation failed. ' + ACCESS_REQUEST);
    await proveAuthentication(session.page, options.navigationConfig);
    await runSteps(session.page, options.navigationConfig.steps || [], options.baseUrl, options.loginEnv);
    const finalStep = [...(options.navigationConfig.steps || [])].reverse().find(step => step.action === 'waitForURL');
    const expectedUrl = finalStep ? safeUrl(finalStep.path, options.baseUrl) : safeUrl(url);
    await new Promise(resolveWait => setTimeout(resolveWait, 750));
    await proveAuthentication(session.page, options.navigationConfig);
    if (safeUrl(session.page.url(), options.baseUrl) !== expectedUrl) {
      fail('final navigation URL did not match; declare page changes with waitForURL. ' + ACCESS_REQUEST);
    }
    if (session.accessDenied) fail('an authenticated request was denied; capture withheld. ' + ACCESS_REQUEST);
    session.secrets = [...new Set([...session.secrets, ...stateSecrets(await session.context.storageState()),
      ...await session.page.evaluate(() => Object.values(sessionStorage))])];

    const overflow = await session.evaluate(OVERFLOW_EXPRESSION);
    entry.horizontal_overflow = typeof overflow === 'boolean' ? overflow : null;
    entry.horizontal_overflow_check_passed = entry.horizontal_overflow === null ? null : !entry.horizontal_overflow;

    const image = await session.screenshotFull();
    await outputFile(screenshot, image);

    if (options.components.length) {
      const boxes = await session.evaluate(boxesExpression(options.components));
      if (Array.isArray(boxes)) {
        for (let index = 0; index < boxes.length; index += 1) {
          const componentName = allSchemes
            ? 'component-' + (index + 1) + '-' + scheme + '.png'
            : 'component-' + (index + 1) + '.png';
          const componentPath = join(dir, componentName);
          try {
            await outputFile(componentPath, await session.screenshotClip(boxes[index]));
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

    await outputFile(join(dir, 'console.log'), logs.consoleErrors.join('\n') + (logs.consoleErrors.length ? '\n' : ''));
    await outputFile(join(dir, 'page-errors.log'), logs.pageErrors.join('\n') + (logs.pageErrors.length ? '\n' : ''));
    await outputFile(join(dir, 'network.json'), JSON.stringify(logs.networkFailures, null, 2));
  } catch (error) {
    entry.error = error instanceof ReviewError ? error.message + ' ' + ACCESS_REQUEST : 'capture failed (details withheld)';
    await outputFile(join(dir, 'console.log'), '').catch(() => {});
    await outputFile(join(dir, 'page-errors.log'), '').catch(() => {});
    await outputFile(join(dir, 'network.json'), '[]').catch(() => {});
  }
  return entry;
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  await prepareArtifacts(options);
  options.navigationConfig = validateNavigation(options.navigation
    ? await localJson(options.navigation, resolve(options.project)) : {approved: true, steps: [], login: []},
  options.baseUrl, options.allowDestructive, Boolean(options.storageState));
  const storageState = options.storageState ? await localJson(options.storageState, resolve(options.project), true) : undefined;
  options.loginEnv = {};
  for (const step of [...(options.navigationConfig.login || []), ...(options.navigationConfig.steps || [])]) {
    if (step.env) {
      if (!process.env[step.env]) fail('missing environment variable ' + step.env + '. ' + ACCESS_REQUEST);
      options.loginEnv[step.env] = process.env[step.env];
    }
  }
  // Set temp roots before importing Playwright as well as before launch: some
  // installed versions resolve internal artifact prefixes at module load time.
  const temp = await browserTemp();
  try {
    const playwright = await loadPlaywright(options.project);
    const allSchemes = options.scheme === 'both';
    const schemes = schemeList(options.scheme);

    if (!playwright) {
      fail('Playwright was not found in the project "' + resolve(options.project) +
        '" or in the global npm install. Searched the project directory and the global npm root' +
        ' (npm root -g, NODE_PATH, ' + COMMON_GLOBAL_ROOT + ').');
    }

    const launchOptions = {headless: true, args: ['--no-sandbox']};
    const resolution = resolveChromium(playwright, options);
    if (!resolution.path) fail(noChromiumMessage(resolution));
    launchOptions.executablePath = resolution.path;

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
      browser_executable: resolution.path,
      results: [],
    };

    launchOptions.downloadsPath = await artifactPath(join(temp.path, 'downloads'));
    launchOptions.tracesDir = await artifactPath(join(temp.path, 'traces'));
    let browser = null;
    try {
      browser = {kind: 'playwright', handle: await playwright.chromium.launch(launchOptions)};
    } catch (error) {
      fail(launchFailureMessage(resolution, error));
    }

    try {
      const context = await browser.handle.newContext({
        viewport: {width: options.viewports[0].width, height: options.viewports[0].height},
        locale: 'en-US', timezoneId: 'UTC', colorScheme: schemes[0], storageState,
      });
      const page = await context.newPage();
      page.setDefaultTimeout(15000);
      if (options.navigationConfig.login?.length) {
        await runSteps(page, options.navigationConfig.login, options.baseUrl, options.loginEnv);
        try {
          await page.waitForURL(safeUrl(options.navigationConfig.authenticatedPath, options.baseUrl), {timeout: 30000, waitUntil: 'load'});
        } catch {
          fail('authenticated route was not reached. ' + ACCESS_REQUEST);
        }
        await proveAuthentication(page, options.navigationConfig);
      }
      const secrets = [...Object.values(options.loginEnv), ...stateSecrets(await context.storageState())];
      const session = new PlaywrightPage(context, page, secrets);
      for (const route of options.routes) {
        for (const viewport of options.viewports) {
          for (const scheme of schemes) {
            await page.setViewportSize({width: viewport.width, height: viewport.height});
            await page.emulateMedia({colorScheme: scheme});

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
                  entry.compare_error = 'comparison failed (details withheld)';
                }
              }
            }
          }
        }
      }
      await session.close();
      await context.close();
    } finally {
      await browser.handle.close().catch(() => {});
    }

    await mkdir(await artifactPath(options.taskDir), {recursive: true});
    await outputFile(join(options.taskDir, 'summary.json'), JSON.stringify(summary, null, 2));
    await outputFile(join(options.taskDir, 'notes.md'), renderNotes(options, summary));
    process.stdout.write(JSON.stringify(summary) + '\n');
    if (summary.results.some(entry => entry.error)) process.exitCode = 2;
  } finally {
    temp.restore();
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch(error => {
    abort(error instanceof ReviewError ? error.message : 'browser-review: operation failed (details withheld to protect credentials)');
  });
}
