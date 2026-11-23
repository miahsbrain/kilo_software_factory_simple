import {test} from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp, writeFile, mkdir, symlink, readFile, stat, rm, readdir, copyFile} from 'node:fs/promises';
import {tmpdir as osTmpdir} from 'node:os';
import {join, resolve} from 'node:path';
import {execFileSync, execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {createServer} from 'node:http';
import {fileURLToPath} from 'node:url';
import {parseArgs, safeUrl, validateNavigation, localJson, runSteps, stateSecrets, redact,
  PlaywrightPage, captureEntry, callerRoot, taskDirectory, prepareArtifacts, artifactPath,
  browserTemp} from './browser-review.mjs';

const fixtures = join(callerRoot(), 'artifacts', 'tmp', 'tests');
await artifactPath(fixtures);
await mkdir(fixtures, {recursive: true});
const tmpdir = () => fixtures;

const base = 'http://localhost:4173';
const manualCapture = '--human-requested-manual-capture';
const state = {cookies: [{value: 'test-session-placeholder'}], origins: [
  {origin: base, localStorage: [{name: 'session', value: 'test-local-placeholder'}]},
]};

test('CLI accepts state/navigation paths and explicit destructive authorization', () => {
  const options = parseArgs(['--base-url', base, '--route', '/app', '--storage-state', '.kilo/qa-local/state.json',
    '--navigation', '.kilo/qa-local/navigation.json', '--allow-destructive']);
  assert.equal(options.storageState, '.kilo/qa-local/state.json');
  assert.equal(options.navigation, '.kilo/qa-local/navigation.json');
  assert.equal(options.allowDestructive, true);
  assert.equal(options.viewports.length, 5);
});

test('automatic CLI requires valid enabled QA before artifact inspection or browser launch', async t => {
  const fixture = await mkdtemp(join(fixtures, 'capture-policy-'));
  t.after(() => rm(fixture, {recursive: true, force: true}));
  const cwd = join(fixture, 'assigned-app');
  const scripts = join(fixture, '.kilo/skills');
  const captureDir = join(scripts, 'qa-review/scripts');
  const policyDir = join(scripts, 'git-worktree/scripts');
  await mkdir(cwd);
  execFileSync('git', ['init', '-q'], {cwd});
  await mkdir(captureDir, {recursive: true});
  await mkdir(policyDir, {recursive: true});
  const script = join(captureDir, 'browser-review.mjs');
  await copyFile(new URL('./browser-review.mjs', import.meta.url), script);
  const policy = join(policyDir, 'worktree.py');
  const refusal = (reason, ...flags) => assert.throws(() => execFileSync(process.execPath,
    [script, '--base-url', base, '--route', '/', ...flags], {cwd, stdio: 'pipe'}),
    error => error.status === 2 && reason.test(error.stderr));
  const invalid = /cannot verify review policy/;
  const pathCheck = /inside caller worktree artifacts/;
  refusal(invalid); // Missing policy CLI.
  refusal(pathCheck, manualCapture, '--artifact-dir', fixture); // Manual capture still enforces confinement.
  for (const [result, expected] of [
    ['raise SystemExit(1)', invalid], ["print('invalid')", invalid],
    ["print('{\"qa\":true}')", invalid], ["print('{\"qa\":\"false\",\"ui\":true}')", invalid],
    ["print('{\"qa\":false,\"ui\":true}')", /automatic QA capture is off/],
    ["print('{\"qa\":true,\"ui\":false}')", pathCheck],
  ]) {
    await writeFile(policy, 'import os, sys\nassert sys.argv[1:] == ["reviews", "status"]\n' +
      'assert os.getcwd() == ' + JSON.stringify(cwd) + '\n' + result);
    if (expected === pathCheck) refusal(expected, '--artifact-dir', fixture);
    else refusal(expected); // Valid capture request must stop without creating even browser temp files.
    assert.deepEqual(await readdir(cwd), ['.git']);
  }
});

test('unsafe scope/task/label/date are refused, including with explicit artifact override', () => {
  for (const flag of ['--scope', '--task-id', '--label', '--date']) {
    for (const segment of ['..', '.', '../escape', '/absolute', 'a/b', 'a\\b', '']) {
      assert.throws(() => parseArgs(['--base-url', base, '--route', '/', '--artifact-dir', fixtures, flag, segment]));
    }
  }
  const options = parseArgs(['--base-url', base, '--route', '/', '--task-id', 'BOARD134']);
  assert.equal(taskDirectory(options), join(callerRoot(), 'artifacts', 'factory', 'qa', options.date, 'BOARD134'));
});

test('outside overrides and symlink ancestors/files are refused before any writes or browser access', async t => {
  const root = await mkdtemp(join(fixtures, 'qa-path-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const outside = join(callerRoot(), 'BOARD134-must-not-exist');
  const options = dir => parseArgs(['--base-url', base, '--route', '/', '--artifact-dir', dir]);
  await assert.rejects(prepareArtifacts(options(outside)), /inside caller worktree artifacts/);
  await assert.rejects(prepareArtifacts(options(join(callerRoot(), 'artifacts', '..', 'escape'))));
  await assert.rejects(stat(outside), {code: 'ENOENT'});
  await mkdir(join(root, 'target'));
  await symlink(join(root, 'target'), join(root, 'link'));
  await assert.rejects(prepareArtifacts(options(join(root, 'link', 'absent', 'child'))), /symlink/);
  await mkdir(join(root, 'capture'));
  await symlink(join(root, 'target', 'summary.json'), join(root, 'capture', 'summary.json'));
  await assert.rejects(prepareArtifacts(options(join(root, 'capture'))), /symlink/);
  assert.deepEqual(await readdir(join(root, 'target')), []);
  // The artifacts root itself must not be a symlink, even to another in-workspace path.
  const fixture = join(root, 'non-git');
  await mkdir(fixture);
  execFileSync('git', ['init', '-q'], {cwd: fixture});
  await symlink(join(root, 'target'), join(fixture, 'artifacts'));
  const script = fileURLToPath(new URL('./browser-review.mjs', import.meta.url));
  assert.throws(() => execFileSync(process.execPath, [script, manualCapture, '--base-url', base, '--route', '/'],
    {cwd: fixture, stdio: 'pipe'}), error => error.status === 2 && /symlink/.test(error.stderr));
  assert.deepEqual(await readdir(join(root, 'target')), []);
});

test('browser temp and Playwright output directories are artifact-local and env restores on failure', async t => {
  const root = await mkdtemp(join(fixtures, 'qa-temp-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const saved = Object.fromEntries(['TMPDIR', 'TMP', 'TEMP'].map(key => [key, process.env[key]]));
  const temp = await browserTemp();
  t.after(() => rm(temp.path, {recursive: true, force: true}));
  try {
    assert.equal(resolve(osTmpdir()), temp.path);
    for (const key of Object.keys(saved)) assert.equal(resolve(process.env[key]), temp.path);
    assert.ok(temp.path.startsWith(join(callerRoot(), 'artifacts', 'tmp') + '/'));
    assert.equal(await artifactPath(join(temp.path, 'downloads')), join(temp.path, 'downloads'));
  } finally { temp.restore(); }
  for (const [key, value] of Object.entries(saved)) assert.equal(process.env[key], value);
});

test('dot route slugs, components and error logs stay under artifacts', async t => {
  const root = await mkdtemp(join(fixtures, 'qa-dot-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  for (const route of ['/.', '/..']) {
    const page = fakePage();
    page.evaluate = async expression => typeof expression === 'string' && expression.includes('getBoundingClientRect')
      ? [{x: 0, y: 0, width: 20, height: 20}] : [];
    const session = new PlaywrightPage({storageState: async () => state}, page);
    const result = await captureEntry(session, {baseUrl: base, artifactRoot: root, loginEnv: {}, components: ['main'],
      navigationConfig: {}}, route, {name: '320x800', width: 320, height: 800}, 'light', false);
    assert.ok(result.screenshot.startsWith(join(root, 'root') + '/'));
    assert.equal(await readFile(join(root, 'root', '320x800', 'light', 'network.json'), 'utf8'), '[]');
    page.goto = async () => { throw new Error('fixture failure'); };
    const failed = await captureEntry(session, {baseUrl: base, artifactRoot: root, loginEnv: {}, components: [],
      navigationConfig: {}}, route, {name: '320x800', width: 320, height: 800}, 'light', false);
    assert.ok(failed.error);
    assert.equal(await readFile(join(root, 'root', '320x800', 'light', 'network.json'), 'utf8'), '[]');
  }
});

test('secret CLI arguments and URL credentials/query/fragment fail without echoing values', () => {
  for (const url of ['http://name:test-placeholder@localhost:4173', base + '/?token=test-placeholder',
    base + '/#test-placeholder', 'javascript:test-placeholder']) {
    assert.throws(() => safeUrl(url), error => !error.message.includes('test-placeholder'));
  }
  assert.throws(() => parseArgs(['--password=test-placeholder']), error => !error.message.includes('test-placeholder'));
  assert.throws(() => safeUrl('https://other.example/app', base), /same-origin/);
  assert.equal(safeUrl('/app', base), base + '/app');
});

test('configuration requires explicit approval, known actions, env-only fills and authenticated route', () => {
  const fill = {action: 'fill', selector: '#password', env: 'QA_TEST_PASSWORD'};
  const valid = {approved: true, login: [fill], authenticatedPath: '/app', authenticatedSelector: '#signed-in', steps: []};
  assert.equal(validateNavigation(valid, base), valid);
  for (const config of [{steps: []}, {...valid, approved: false}, {...valid, authenticatedPath: undefined},
    {...valid, login: [{...fill, value: 'test-placeholder'}]}, {...valid, login: [{...fill, env: 'literal value'}]},
    {approved: true, steps: [{action: 'evaluate', code: 'anything'}]}, {approved: true, steps: {}},
    {approved: true, steps: [{action: 'goto', path: '/?token=test-placeholder'}]}]) {
    assert.throws(() => validateNavigation(config, base));
  }
});

test('login and state require a nonempty app-specific signed-in marker with actionable failure', () => {
  for (const marker of [undefined, '', ' ', 12]) {
    const config = {approved: true, authenticatedSelector: marker};
    assert.throws(() => validateNavigation(config, base, false, true), /authenticatedSelector.*Ask the user.*MFA\/SSO/);
    assert.throws(() => validateNavigation({...config, login: [{action: 'goto', path: '/login'}],
      authenticatedPath: '/app'}, base), /authenticatedSelector.*Ask the user/);
  }
  validateNavigation({approved: true, authenticatedSelector: '#signed-in'}, base, false, true);
  validateNavigation({approved: true}, base);
});

test('clicks require reviewed intent and destructive clicks require explicit authorization', () => {
  const config = intent => ({approved: true, steps: [{action: 'click', selector: '#action', intent}]});
  validateNavigation(config('navigation'), base);
  for (const intent of [undefined, 'login', 'unknown', 'destructive']) {
    assert.throws(() => validateNavigation(config(intent), base));
  }
  validateNavigation(config('destructive'), base, true);
});

function fakePage() {
  const calls = [];
  let url = base + '/login';
  const page = {
    calls, url: () => url, authenticated: true, password: false,
    goto: async (target, options) => { calls.push(['goto', target, options]); url = target; return {status: () => 200}; },
    waitForURL: async (target, options) => { calls.push(['waitForURL', target, options]); url = target; },
    locator: selector => ({
      fill: async value => calls.push(['fill', selector, value]),
      click: async () => calls.push(['click', selector]),
      waitFor: async options => {
        calls.push(['waitForSelector', selector, options]);
        if (selector === '#signed-in' && !page.authenticated) throw new Error('signed-in marker absent');
      },
      count: async () => selector.includes('password') && page.password ? 1 : 0,
    }),
    getByText: (value, options) => ({value, options}),
    on: (event, callback) => { page[event] = callback; },
    screenshot: async options => { calls.push(['screenshot', options]); return Buffer.from('image'); },
    evaluate: async expression => typeof expression === 'string' ? false : [],
    waitForLoadState: async state => calls.push(['load', state]),
    setViewportSize: async viewport => calls.push(['viewport', viewport]),
    emulateMedia: async scheme => calls.push(['scheme', scheme]),
    close: async () => calls.push(['close']),
  };
  return page;
}

test('navigation primitives execute deterministically and resolve fill values only from env', async () => {
  const page = fakePage();
  const steps = [
    {action: 'goto', path: '/login'}, {action: 'fill', selector: '#password', env: 'QA_TEST_PASSWORD'},
    {action: 'click', selector: '#submit', intent: 'login'}, {action: 'waitForURL', path: '/app'},
    {action: 'waitForSelector', selector: '#ready'},
  ];
  await runSteps(page, steps, base, {QA_TEST_PASSWORD: 'test-password-placeholder'});
  assert.deepEqual(page.calls.map(call => call[0]), ['goto', 'fill', 'click', 'waitForURL', 'waitForSelector']);
  assert.equal(page.calls[1][2], 'test-password-placeholder');
  assert.equal(page.url(), base + '/app');
});

test('missing access and unsafe redirects stop before further interaction; raw browser errors are withheld', async () => {
  const page = fakePage();
  const fill = [{action: 'fill', selector: '#password', env: 'QA_TEST_PASSWORD'}];
  await assert.rejects(runSteps(page, fill, base, {}), /Ask the user.*MFA\/SSO/);
  page.locator = () => ({fill: async () => { throw new Error('test-password-placeholder Authorization: private'); }});
  await assert.rejects(runSteps(page, fill, base, {QA_TEST_PASSWORD: 'test-password-placeholder'}),
    error => !error.message.includes('test-password-placeholder') && !error.message.includes('Authorization'));
  await page.goto('https://other.example/login');
  const count = page.calls.length;
  await assert.rejects(runSteps(page, fill, base, {QA_TEST_PASSWORD: 'test-password-placeholder'}));
  assert.equal(page.calls.length, count);
});

test('state handling requires ignored, untracked, in-repository regular files and never saves state', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-state-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const git = args => execFileSync('git', args, {cwd: root, stdio: 'ignore'});
  git(['init', '-q']);
  await mkdir(join(root, 'local'));
  await writeFile(join(root, '.gitignore'), 'local/\n');
  const path = join(root, 'local', 'state.json');
  await writeFile(path, JSON.stringify(state), {mode: 0o600});
  const before = await stat(path);
  assert.deepEqual(await localJson(path, root, true), state);
  assert.equal((await stat(path)).mtimeMs, before.mtimeMs);
  assert.equal((await stat(path)).mode & 0o777, 0o600);
  assert.equal(await readFile(path, 'utf8'), JSON.stringify(state));
  await symlink(path, join(root, 'local', 'link.json'));
  await assert.rejects(localJson('local/link.json', root, true), /ignored, untracked regular file/);
  await writeFile(join(root, 'public.json'), JSON.stringify(state));
  await assert.rejects(localJson('public.json', root, true));
  await assert.rejects(localJson('local/missing.json', root, true), /Ask the user/);
  await writeFile(join(root, 'local', 'bad.json'), '{"password":"test-placeholder"');
  await assert.rejects(localJson('local/bad.json', root, true), error => !error.message.includes('test-placeholder'));
  await writeFile(join(root, 'local', 'invalid.json'), '{}');
  await assert.rejects(localJson('local/invalid.json', root, true));
  git(['add', '-f', 'local/state.json']);
  await assert.rejects(localJson(path, root, true), /ignored, untracked regular file/);
  await assert.rejects(localJson(join(root, '..'), root, true));
});

test('redaction removes known/encoded secrets, authorization and full URL paths/query/credentials', () => {
  const secrets = stateSecrets(state);
  assert.deepEqual(secrets, ['test-session-placeholder', 'test-local-placeholder']);
  const output = redact('https://name:private@example.com/private-path?token=private\n' +
    secrets.join(' ') + '\nAuthorization: Bearer private\n' + encodeURIComponent('test password'), [...secrets, 'test password']);
  for (const value of ['private', ...secrets, 'test%20password']) assert.ok(!output.includes(value));
});

test('artifact collectors withhold raw console/errors/payloads and screenshots mask credentials', async () => {
  const page = fakePage();
  const session = new PlaywrightPage({}, page, ['test-password-placeholder']);
  page.console({type: () => 'error', text: () => { throw new Error('must not read console payload'); }});
  page.pageerror(new Error('test-password-placeholder'));
  page.response({status: () => 403, url: () => base + '/private?token=test-password-placeholder',
    request: () => ({method: () => 'GET'})});
  page.requestfailed({url: () => base + '/private?token=test-password-placeholder',
    method: () => 'POST', failure: () => { throw new Error('must not read request payload'); }});
  const logs = JSON.stringify(session.logs());
  assert.ok(!logs.includes('test-password-placeholder'));
  assert.ok(!logs.includes('/private'));
  assert.equal(session.logs().networkFailures.length, 2);
  assert.equal(session.accessDenied, true);
  await session.screenshotFull();
  await session.screenshotClip({x: 0, y: 0, width: 20, height: 20});
  for (const call of page.calls.filter(call => call[0] === 'screenshot')) assert.equal(call[1].mask.length, 2);
  await session.setup();
  assert.equal(session.accessDenied, false);
  assert.deepEqual(session.logs(), {consoleErrors: [], pageErrors: [], networkFailures: []});
  await session.close();
  assert.equal(page.calls.at(-1)[0], 'close');
});

test('screenshot masking includes process-environment credentials without mutating the page', async () => {
  const page = fakePage();
  const session = new PlaywrightPage({}, page, ['environment-secret-placeholder']);
  const before = page.calls.length;
  await session.screenshotFull();
  assert.equal(page.calls.length, before + 1);
  assert.equal(page.calls.at(-1)[0], 'screenshot');
  assert.equal(page.calls.at(-1)[1].mask.length, 2);
  assert.equal(page.calls.at(-1)[1].mask[1].value, 'environment-secret-placeholder');
});

test('401/403 target navigation does not count as successful access', async () => {
  for (const status of [401, 403]) {
    const page = fakePage();
    page.goto = async () => ({status: () => status});
    assert.equal((await new PlaywrightPage({}, page).goto(base + '/app')).ok, false);
  }
});

test('fallback navigation and screenshot retain sanitized errors and masking', async () => {
  const page = fakePage();
  page.goto = async () => { throw new Error('test-password-placeholder'); };
  const session = new PlaywrightPage({}, page, ['test-password-placeholder']);
  assert.equal((await session.goto(base)).ok, false);
  assert.ok(!JSON.stringify(await session.goto(base)).includes('test-password-placeholder'));
  let calls = 0;
  page.screenshot = async options => {
    calls += 1;
    assert.equal(options.mask.length, 2);
    if (calls === 1) throw new Error('clip fallback');
    return Buffer.from('image');
  };
  await session.screenshotClip({x: 0, y: 0, width: 20, height: 20});
  assert.equal(calls, 2);
});

test('redirected protected target yields actionable access request without taking screenshot', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-capture-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  const session = new PlaywrightPage({}, page);
  session.setup = async () => {};
  session.goto = async () => ({ok: true});
  const result = await captureEntry(session, {baseUrl: base, artifactRoot: root, navigationConfig: {}, loginEnv: {}},
    '/app', {name: '320x800', width: 320, height: 800}, 'light', false);
  assert.match(result.error, /Ask the user.*MFA\/SSO/);
  assert.ok(!page.calls.some(call => call[0] === 'screenshot'));
  assert.equal(await readFile(join(root, 'app', '320x800', 'light', 'network.json'), 'utf8'), '[]');
});

test('successful protected capture replays explicit nested navigation across viewports in the same session', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-success-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  page.password = true;
  const context = {storageState: async () => state};
  const session = new PlaywrightPage(context, page);
  const options = {baseUrl: base, artifactRoot: root, loginEnv: {}, components: [], navigationConfig: {
    authenticatedSelector: '#signed-in', steps: [
      {action: 'click', selector: '#settings', intent: 'navigation'},
      {action: 'waitForURL', path: '/settings'}, {action: 'waitForSelector', selector: 'main'},
    ],
  }};
  for (const viewport of [{name: '320x800', width: 320, height: 800}, {name: '834x1112', width: 834, height: 1112}]) {
    await page.setViewportSize(viewport);
    await page.emulateMedia({colorScheme: 'light'});
    const result = await captureEntry(session, options, '/app', viewport, 'light', false);
    assert.equal(result.error, null);
    assert.equal(result.horizontal_overflow_check_passed, true);
    assert.equal(await readFile(result.screenshot, 'utf8'), 'image');
    assert.deepEqual(JSON.parse(await readFile(join(root, 'app', viewport.name, 'light', 'network.json'), 'utf8')), []);
  }
  assert.equal(page.calls.filter(call => call[0] === 'click').length, 2);
  assert.equal(page.calls.filter(call => call[0] === 'goto').length, 2);
  assert.equal(page.calls.filter(call => call[0] === 'waitForSelector' && call[1] === '#signed-in').length, 4);
  const firstMarker = page.calls.findIndex(call => call[0] === 'waitForSelector' && call[1] === '#signed-in');
  assert.ok(firstMarker < page.calls.findIndex(call => call[0] === 'click'));
  assert.ok(!page.calls.some(call => call[0] === 'close'));
});

test('same-URL HTTP-200 sign-in challenge blocks protected interactions without relying on password inputs', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-false-auth-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  page.authenticated = false;
  const session = new PlaywrightPage({}, page);
  const result = await captureEntry(session, {baseUrl: base, artifactRoot: root, loginEnv: {}, components: [],
    navigationConfig: {authenticatedSelector: '#signed-in', steps: [
      {action: 'click', selector: '#protected', intent: 'navigation'},
    ]}}, '/app', {name: '320x800', width: 320, height: 800}, 'light', false);
  assert.equal(page.url(), base + '/app');
  assert.match(result.error, /signed-in marker.*Ask the user.*MFA\/SSO/);
  assert.ok(!page.calls.some(call => ['click', 'screenshot'].includes(call[0])));
});

test('marker is checked again after navigation settles and before a screenshot', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-lost-auth-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  page.waitForURL = async () => { page.authenticated = false; };
  const result = await captureEntry(new PlaywrightPage({}, page), {baseUrl: base, artifactRoot: root, loginEnv: {},
    components: [], navigationConfig: {authenticatedSelector: '#signed-in', steps: [{action: 'waitForURL', path: '/app'}]}},
  '/app', {name: '320x800', width: 320, height: 800}, 'light', false);
  assert.match(result.error, /signed-in marker/);
  assert.ok(!page.calls.some(call => call[0] === 'screenshot'));
});

test('page-changing steps without explicit waitForURL cannot produce a successful capture', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-final-url-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  const result = await captureEntry(new PlaywrightPage({}, page), {baseUrl: base, artifactRoot: root,
    loginEnv: {}, components: [], navigationConfig: {steps: [{action: 'goto', path: '/settings'}]}},
  '/app', {name: '320x800', width: 320, height: 800}, 'light', false);
  assert.match(result.error, /declare page changes with waitForURL/);
  assert.ok(!page.calls.some(call => call[0] === 'screenshot'));
});

test('public capture remains available without login/state or an authenticated marker', async t => {
  const root = await mkdtemp(join(tmpdir(), 'qa-public-test-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const page = fakePage();
  const session = new PlaywrightPage({storageState: async () => ({cookies: [], origins: []})}, page);
  const result = await captureEntry(session, {baseUrl: base, artifactRoot: root, loginEnv: {}, components: [],
    navigationConfig: {}}, '/', {name: '320x800', width: 320, height: 800}, 'light', false);
  assert.equal(result.error, null);
  assert.ok(!page.calls.some(call => call[0] === 'waitForSelector' && call[1] === '#signed-in'));
});

test('canonical browser script logs in and captures protected password settings using its existing browser resolver',
  {timeout: 120000}, async t => {
    const fixture = await mkdtemp(join(tmpdir(), 'qa-real-browser-test-'));
    t.after(() => rm(fixture, {recursive: true, force: true}));
    const primary = join(fixture, 'primary');
    const root = join(fixture, 'linked');
    await mkdir(primary);
    execFileSync('git', ['init', '-q'], {cwd: primary, stdio: 'ignore'});
    await writeFile(join(primary, '.gitignore'), 'artifacts/\nlocal/\n');
    execFileSync('git', ['add', '.gitignore'], {cwd: primary, stdio: 'ignore'});
    execFileSync('git', ['-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
      '-c', 'commit.gpgsign=false', 'commit', '-qm', 'fixture'], {cwd: primary, stdio: 'ignore'});
    execFileSync('git', ['worktree', 'add', '-qb', 'review', root], {cwd: primary, stdio: 'ignore'});
    assert.equal(callerRoot(root), root);
    await mkdir(join(root, 'local'));
    await writeFile(join(root, '.gitignore'), 'local/\n');
    let logins = 0;
    let appVisits = 0;
    let settingsVisits = 0;
     const observedTempPaths = new Set();
     let foreignRequests = 0;
     const foreign = createServer((_req, res) => { foreignRequests++; res.end(); });
     await new Promise(resolve => foreign.listen(0, '127.0.0.1', resolve));
     t.after(() => new Promise(resolve => { foreign.close(resolve); foreign.closeAllConnections(); }));
    const server = createServer(async (request, response) => {
      response.setHeader('Content-Type', 'text/html');
      response.setHeader('Cache-Control', 'no-store');
      if (request.url === '/favicon.ico') { response.writeHead(204).end(); return; }
      if (request.url === '/redirect-image') {
        response.writeHead(302, {Location: 'http://127.0.0.1:' + foreign.address().port + '/pixel'}).end(); return;
      }
      if (request.url === '/login' && request.method === 'GET') {
        for (const name of await readdir(join(root, 'artifacts', 'tmp'))) {
          const temp = join(root, 'artifacts', 'tmp', name);
          for (const child of await readdir(temp)) observedTempPaths.add(join(temp, child));
        }
        response.end('<!doctype html><form method="post" action="/login"><input name="email" id="email">' +
          '<input name="password" id="password" type="password"><button type="submit">Sign in</button></form>');
        return;
      }
      if (request.url === '/login' && request.method === 'POST') {
        let body = '';
        for await (const chunk of request) body += chunk;
        const values = new URLSearchParams(body);
        if (values.get('email') !== 'fixture-user-placeholder' || values.get('password') !== 'fixture-password-placeholder') {
          response.writeHead(401).end('Fixture login rejected'); return;
        }
        logins += 1;
        response.setHeader('Set-Cookie', 'fixture_session=fixture-session-placeholder; HttpOnly; SameSite=Strict; Path=/');
        response.end('<!doctype html><script>sessionStorage.setItem("fixture", "fixture-session-placeholder");' +
          'location.href="/app";</script>');
        return;
      }
      if (!request.headers.cookie?.includes('fixture_session=fixture-session-placeholder')) {
        response.end('<!doctype html><main>Complete manual sign-in to continue</main>'); return;
      }
      if (request.url === '/app') appVisits += 1;
      if (request.url === '/settings') settingsVisits += 1;
      response.end('<!doctype html><main><a href="/settings">Settings</a>' +
        '<label>New password<input type="password" value="fixture-password-placeholder"></label></main>' +
        '<script>if(localStorage.fixture) { new Image().src="/redirect-image"; }' +
        'if((sessionStorage.fixture || localStorage.fixture) === "fixture-session-placeholder") {' +
        'const marker=document.createElement("nav"); marker.id="signed-in"; marker.textContent="Signed in";' +
        'document.body.append(marker);}</script>');
    });
    t.after(() => new Promise(resolve => { server.close(resolve); server.closeAllConnections(); }));
    await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
    const url = 'http://127.0.0.1:' + server.address().port;
    const config = {approved: true, authenticatedPath: '/app', authenticatedSelector: '#signed-in', login: [
      {action: 'goto', path: '/login'},
      {action: 'fill', selector: '#email', env: 'QA_FIXTURE_EMAIL'},
      {action: 'fill', selector: '#password', env: 'QA_FIXTURE_PASSWORD'},
      {action: 'click', selector: 'button[type=submit]', intent: 'login'},
      {action: 'waitForURL', path: '/app'},
    ], steps: [
      {action: 'click', selector: 'a[href="/settings"]', intent: 'navigation'},
      {action: 'waitForURL', path: '/settings'}, {action: 'waitForSelector', selector: 'main'},
    ]};
    await writeFile(join(root, 'local', 'navigation.json'), JSON.stringify(config), {mode: 0o600});
    const artifactDir = join(root, 'artifacts', 'factory', 'qa', '2026-11-18', 'BOARD134');
    const script = fileURLToPath(new URL('./browser-review.mjs', import.meta.url));
    const args = [script, manualCapture, '--base-url', url, '--route', '/app', '--project', root,
      '--navigation', 'local/navigation.json', '--date', '2026-11-18', '--task-id', 'BOARD134',
      '--component', 'main', '--viewports', '320x800,834x1112'];
    let output;
    try {
      output = await promisify(execFile)(process.execPath, args, {cwd: root, timeout: 90000,
        env: {...process.env, QA_FIXTURE_EMAIL: 'fixture-user-placeholder', QA_FIXTURE_PASSWORD: 'fixture-password-placeholder'}});
    } catch (error) {
      if (/Playwright was not found|no chromium browser was found/.test(error.stderr || '')) {
        t.skip('Existing Playwright/browser unavailable; no installation attempted'); return;
      }
      assert.fail('Canonical command: ' + [process.execPath, ...args].join(' ') + '\nExit: ' + error.code +
        '\n' + (error.stderr || error.message));
    }
    const summary = JSON.parse(await readFile(join(artifactDir, 'summary.json'), 'utf8'));
    assert.equal(summary.driver, 'playwright');
    assert.equal(summary.results.length, 2);
    assert.equal(logins, 1);
    assert.ok(appVisits >= 2);
    assert.equal(settingsVisits, 2);
    await assert.rejects(stat(join(primary, 'artifacts')), {code: 'ENOENT'});
    const tempChildren = await readdir(join(root, 'artifacts', 'tmp'));
    assert.ok(tempChildren.some(name => name.startsWith('browser-')));
    assert.ok([...observedTempPaths].some(path => path.includes('/playwright-artifacts-')));
    assert.ok([...observedTempPaths].some(path => path.includes('/playwright_chromiumdev_profile-')));
    for (const path of observedTempPaths) assert.ok(path.startsWith(join(root, 'artifacts', 'tmp') + '/'));
    for (const result of summary.results) {
      assert.equal(result.error, null);
      assert.equal(result.components.length, 1);
      assert.ok(result.components[0].startsWith(artifactDir + '/'));
      assert.equal((await readFile(result.screenshot)).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
      for (const name of ['console.log', 'page-errors.log', 'network.json']) {
        const artifact = await readFile(join(artifactDir, 'app', result.viewport, 'light', name), 'utf8');
        for (const value of ['fixture-password-placeholder', 'fixture-session-placeholder']) assert.ok(!artifact.includes(value));
      }
    }
    for (const value of ['fixture-password-placeholder', 'fixture-session-placeholder']) {
      assert.ok(!output.stdout.includes(value));
      assert.ok(!output.stderr.includes(value));
    }
    // Reuse the canonical command for comparison sheets, without another driver.
    await promisify(execFile)(process.execPath, [...args, '--label', 'after', '--compare', artifactDir],
      {cwd: root, timeout: 90000, env: {...process.env, QA_FIXTURE_EMAIL: 'fixture-user-placeholder',
        QA_FIXTURE_PASSWORD: 'fixture-password-placeholder'}});
    const compared = JSON.parse(await readFile(join(artifactDir, 'summary.json'), 'utf8'));
    for (const result of compared.results) {
      assert.equal(result.compare_error, undefined);
      assert.ok(result.compare.startsWith(join(artifactDir, 'after') + '/'));
      assert.equal((await readFile(result.compare)).subarray(0, 8).toString('hex'), '89504e470d0a1a0a');
    }
    const local = join(root, '.kilo/local');
    await mkdir(local, {recursive: true});
    await writeFile(join(root, '.gitignore'), 'local/\n.kilo/local/\n');
    const auth = {approved: true, origin: url, storageState: 'qa-storage-state.json', authenticatedSelector: '#signed-in'};
    await writeFile(join(local, 'qa-auth.json'), JSON.stringify(auth));
    const prepared = {cookies: [{name: 'fixture_session', value: 'fixture-session-placeholder', domain: '127.0.0.1',
      path: '/', expires: -1, httpOnly: true, secure: false, sameSite: 'Strict'}], origins: [{origin: url,
      localStorage: [{name: 'fixture', value: 'fixture-session-placeholder'}]}]};
    await writeFile(join(local, auth.storageState), JSON.stringify(prepared));
    const before = logins;
    const capture = await promisify(execFile)(process.execPath, [script, manualCapture, '--base-url', url, '--route', '/app',
      '--viewports', '320x800'], {cwd: root});
    const entry = JSON.parse(capture.stdout).results[0];
    assert.equal(entry.error, null);
    assert.ok(entry.network_failure_count > 0);
    assert.equal(foreignRequests, 0, 'redirect to the same hostname on another port must not reach the server');
    assert.equal(logins, before);
    assert.ok(!capture.stdout.includes('fixture-session-placeholder'));
  });

test('discovery fails closed before launch on unsafe config, foreign origin/state, or conflicting inputs', async t => {
  const root = await mkdtemp(join(fixtures, 'auth-config-'));
  t.after(() => rm(root, {recursive: true, force: true}));
  const git = (...args) => execFileSync('git', args, {cwd: root, stdio: 'ignore'});
  git('init', '-q');
  const local = join(root, '.kilo/local');
  await mkdir(local, {recursive: true});
  await writeFile(join(root, '.gitignore'), '.kilo/local/\n');
  const config = {approved: true, origin: base, authenticatedSelector: '#signed-in', storageState: 'qa-storage-state.json'};
  const file = join(local, 'qa-auth.json');
  const script = fileURLToPath(new URL('./browser-review.mjs', import.meta.url));
  const refusal = (...extra) => assert.throws(() => execFileSync(process.execPath,
    [script, manualCapture, '--base-url', base, '--route', '/', ...extra], {cwd: root, stdio: 'pipe'}),
    error => error.status === 2 && !error.stderr.includes('SECRET-MARKER'));
  for (const changed of [{approved: false}, {origin: 'https://localhost:4173'}, {origin: 'http://localhost:4174'},
    {storageState: '../SECRET-MARKER'}, {password: 'SECRET-MARKER'}]) {
    await writeFile(file, JSON.stringify({...config, ...changed})); refusal();
  }
  await writeFile(file, JSON.stringify(config));
  refusal('--storage-state', 'somewhere'); refusal('--project', fixtures); refusal();
  const stateFile = join(local, config.storageState);
  const insecureOrigin = 'http://fixture.invalid';
  await writeFile(file, JSON.stringify({...config, origin: insecureOrigin}));
  await writeFile(stateFile, JSON.stringify({cookies: [], origins: []}));
  refusal('--base-url', insecureOrigin);
  await writeFile(file, JSON.stringify(config));
  for (const bad of [{cookies: [], origins: [{origin: 'https://foreign.invalid'}]},
    {cookies: [{domain: '.localhost', value: 'SECRET-MARKER'}], origins: []}]) {
    await writeFile(stateFile, JSON.stringify(bad)); refusal();
  }
  git('add', '-f', '.kilo/local/qa-auth.json'); refusal();
  await rm(file); await symlink(join(root, 'missing'), file); refusal();
  await assert.rejects(stat(join(root, 'artifacts')), {code: 'ENOENT'});
});
