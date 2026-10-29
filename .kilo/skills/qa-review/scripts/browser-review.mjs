#!/usr/bin/env node
/**
 * browser-review.mjs — capture browser evidence for a QA review.
 *
 * Uses the project's own Playwright (resolved from the target project's
 * package.json), so this script installs nothing of its own.
 *
 * Usage:
 *   node browser-review.mjs --base-url <url> --route <path> [--route <path> ...]
 *                            --artifact-dir <dir>
 *                            [--project <dir with package.json>]
 *                            [--viewports "390x844,834x1112,1440x900,1920x1080,320x800"]
 *                            [--label <slug>]
 *
 * For every route x viewport it writes a full-page screenshot plus console,
 * page-error and network-failure logs, then a summary.json for the reviewer.
 * Exit codes: 0 capture completed, 2 fatal error.
 */
import {createRequire} from 'node:module';
import {resolve, join} from 'node:path';
import {writeFile, mkdir} from 'node:fs/promises';

const DEFAULT_VIEWPORTS = '390x844,834x1112,1440x900,1920x1080,320x800';

function usage() {
  return [
    'Usage: node browser-review.mjs --base-url <url> --route <path> [--route <path> ...]',
    '                                --artifact-dir <dir>',
    '                                [--project <dir with package.json>]',
    '                                [--viewports "' + DEFAULT_VIEWPORTS + '"]',
    '                                [--label <slug>]',
    '',
    'Options:',
    '  --base-url     Base URL of the running app (required).',
    '  --route        Route path to visit, repeatable (required).',
    '  --artifact-dir Directory that receives screenshots and logs (required).',
    '  --project      Directory whose package.json provides Playwright. Default: cwd.',
    '  --viewports    Comma-separated WIDTHxHEIGHT list. Default: ' + DEFAULT_VIEWPORTS,
    '  --label        Optional slug mixed into the artifact directory name.',
    '  --help         Show this message and exit.',
  ].join('\n');
}

function fail(message) {
  process.stderr.write('browser-review: ' + message + '\n');
  process.exit(2);
}

function parseArgs(argv) {
  const options = {routes: [], viewports: DEFAULT_VIEWPORTS, project: process.cwd()};
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
      case '--project':
        options.project = next();
        break;
      case '--viewports':
        options.viewports = next();
        break;
      case '--label':
        options.label = next();
        break;
      default:
        fail('unknown argument: ' + arg);
    }
  }
  if (!options.baseUrl) fail('--base-url is required');
  if (!options.routes.length) fail('at least one --route is required');
  if (!options.artifactDir) fail('--artifact-dir is required');
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

async function loadPlaywright(projectDir) {
  const project = resolve(projectDir);
  try {
    const require = createRequire(resolve(project, 'package.json'));
    return require('playwright');
  } catch (error) {
    fail('Playwright is not installed in project "' + project + '". Install it there, or pass --project <dir>. (' + error.message + ')');
  }
}

async function captureRoute(page, url) {
  const consoleErrors = [];
  const pageErrors = [];
  const networkFailures = [];

  const onConsole = msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  };
  const onPageError = error => pageErrors.push(String(error && error.stack ? error.stack : error));
  const onResponse = response => {
    if (response.status() >= 400) {
      networkFailures.push({url: response.url(), status: response.status(), method: response.request().method()});
    }
  };
  const onRequestFailed = request => {
    networkFailures.push({
      url: request.url(),
      status: null,
      method: request.method(),
      error: request.failure() ? request.failure().errorText : 'request failed',
    });
  };

  page.on('console', onConsole);
  page.on('pageerror', onPageError);
  page.on('response', onResponse);
  page.on('requestfailed', onRequestFailed);

  let navigation = {ok: true, waitUntil: 'networkidle'};
  try {
    await page.goto(url, {waitUntil: 'networkidle', timeout: 30000});
  } catch (error) {
    try {
      await page.goto(url, {waitUntil: 'load', timeout: 30000});
      navigation = {ok: true, waitUntil: 'load', note: 'networkidle timed out, fell back to load'};
    } catch (fallbackError) {
      navigation = {ok: false, waitUntil: 'load', error: String(fallbackError.message || fallbackError)};
    }
  }
  await page.waitForTimeout(750);

  const overflow = await page.evaluate(() => {
    const root = document.documentElement;
    return root.scrollWidth > root.clientWidth + 1;
  }).catch(() => null);

  page.off('console', onConsole);
  page.off('pageerror', onPageError);
  page.off('response', onResponse);
  page.off('requestfailed', onRequestFailed);

  return {consoleErrors, pageErrors, networkFailures, navigation, overflow};
}

async function main() {
  const options = parseArgs(process.argv.slice(2));
  const {chromium} = await loadPlaywright(options.project);

  const artifactRoot = options.label
    ? join(resolve(options.artifactDir), options.label)
    : resolve(options.artifactDir);

  const summary = {
    base_url: options.baseUrl,
    project: resolve(options.project),
    artifact_dir: artifactRoot,
    viewports: options.viewports.map(v => v.name),
    routes: options.routes,
    results: [],
  };

  let browser;
  try {
    browser = await chromium.launch({headless: true});
  } catch (error) {
    fail('could not launch chromium: ' + (error.message || error));
  }

  try {
    for (const route of options.routes) {
      const slug = routeSlug(route);
      const url = joinUrl(options.baseUrl, route);
      for (const viewport of options.viewports) {
        const dir = join(artifactRoot, slug, viewport.name);
        await mkdir(dir, {recursive: true});
        const entry = {
          route,
          viewport: viewport.name,
          width: viewport.width,
          height: viewport.height,
          url,
          screenshot: join(dir, 'full.png'),
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
          const context = await browser.newContext({
            viewport: {width: viewport.width, height: viewport.height},
            locale: 'en-US',
            timezoneId: 'UTC',
          });
          const page = await context.newPage();
          page.setDefaultTimeout(15000);
          const captured = await captureRoute(page, url);
          entry.navigation = captured.navigation;
          entry.console_errors = captured.consoleErrors;
          entry.page_errors = captured.pageErrors;
          entry.network_failures = captured.networkFailures;
          entry.console_error_count = captured.consoleErrors.length;
          entry.page_error_count = captured.pageErrors.length;
          entry.network_failure_count = captured.networkFailures.length;
          entry.horizontal_overflow = captured.overflow;
          entry.horizontal_overflow_check_passed = captured.overflow === null ? null : !captured.overflow;
          await page.screenshot({path: entry.screenshot, fullPage: true});
          await writeFile(join(dir, 'console.log'), captured.consoleErrors.join('\n') + (captured.consoleErrors.length ? '\n' : ''));
          await writeFile(join(dir, 'page-errors.log'), captured.pageErrors.join('\n') + (captured.pageErrors.length ? '\n' : ''));
          await writeFile(join(dir, 'network.json'), JSON.stringify(captured.networkFailures, null, 2));
          await context.close();
        } catch (error) {
          entry.error = String(error.message || error);
          await writeFile(join(dir, 'console.log'), '').catch(() => {});
          await writeFile(join(dir, 'page-errors.log'), '').catch(() => {});
          await writeFile(join(dir, 'network.json'), '[]').catch(() => {});
        }
        summary.results.push(entry);
      }
    }
  } finally {
    await browser.close().catch(() => {});
  }

  await mkdir(artifactRoot, {recursive: true});
  await writeFile(join(artifactRoot, 'summary.json'), JSON.stringify(summary, null, 2));
  process.stdout.write(JSON.stringify(summary) + '\n');
}

main().catch(error => {
  fail(String(error && error.stack ? error.stack : error));
});
