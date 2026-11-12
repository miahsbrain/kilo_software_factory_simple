import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, writeFile, copyFile, symlink, readFile } from 'node:fs/promises'
import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { guard, guardArguments, setup } from './index.js'

const source = fileURLToPath(new URL('../../../', import.meta.url))
const scripts = '.opencode/skills/git-worktree/scripts'
const git = (cwd, ...args) => execFileSync('git', args, { cwd, stdio: 'pipe' })

async function fixture() {
  const root = await mkdtemp(path.join(source, 'factory-guard-test-'))
  await mkdir(path.join(root, scripts), { recursive: true })
  await mkdir(path.join(root, '.opencode/policies'), { recursive: true })
  for (const name of ['guard.py', 'worktree.py', 'scope.py'])
    await copyFile(path.join(source, scripts, name), path.join(root, scripts, name))
  await copyFile(path.join(source, '.opencode/policies/git-policy.json'), path.join(root, '.opencode/policies/git-policy.json'))
  const runtime = '.opencode/skills/runtime-state/scripts/state.py'
  await mkdir(path.dirname(path.join(root, runtime)), { recursive: true })
  await copyFile(path.join(source, runtime), path.join(root, runtime))
  git(root, 'init', '-b', 'main')
  await writeFile(path.join(root, 'sample.txt'), 'dummy\n')
  git(root, 'add', 'sample.txt')
  git(root, '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-m', 'fixture')
  const linked = path.join(root, '.opencode/worktrees/test')
  git(root, 'worktree', 'add', '-b', 'feat/test', linked)
  await mkdir(path.join(linked, 'src'))
  await writeFile(path.join(linked, 'src/sample.txt'), 'dummy\n')
  return { root, linked }
}

test('canonical boundaries on real temporary linked worktrees', async () => {
  const { root, linked } = await fixture()
  assert.equal(await guard('edit', 'src/sample.txt', root, root), 'deny')
  assert.equal(await guard('edit', 'src/sample.txt', linked, root), 'allow')
  assert.equal(await guard('edit', 'new/deep/file.txt', linked, root), 'allow')
  assert.equal(await guard('edit', '.env.example', linked, root), 'allow')
  assert.equal(await guard('edit', '.env', linked, root), 'deny')
  assert.equal(await guard('edit', 'docs/BOARD.md', linked, root), 'deny')
  assert.equal(await guard('edit', 'AGENTS.md', linked, root), 'ask')
  assert.equal(await guard('edit', path.join(root, 'sample.txt'), linked, root), 'deny')
  await symlink(root, path.join(linked, 'escape'))
  assert.equal(await guard('edit', 'escape/sample.txt', linked, root), 'deny')
  assert.equal(await guard('read', 'escape/sample.txt', linked, root), 'deny')
  assert.equal(await guard('search', 'escape', linked, root), 'deny')
  assert.equal(await guard('search', 'src', linked, root), 'allow')
  await writeFile(path.join(linked, 'src/.env'), 'DUMMY_ONLY=placeholder\n')
  assert.equal(await guard('search', 'src', linked, root), 'deny')
  assert.equal(await guard('read', 'src/.env', linked, root), 'deny')
  await writeFile(path.join(linked, '.env.example'), 'DUMMY_ONLY=\n')
  assert.equal(await guard('read', '.env.example', linked, root), 'allow')
  assert.equal(await guard('check-git', 'git commit -m fixture', root, root), 'deny')
  assert.equal(await guard('check-git', 'git commit -m fixture', linked, root), 'allow')
  assert.equal(await guard('check-git', `git -C '${root}' commit -m fixture`, linked, root), 'deny')
  assert.equal(await guard('check-git', 'git push origin main', linked, root), 'deny')
  git(linked, 'branch', 'opencode', 'HEAD')
  git(linked, 'symbolic-ref', 'HEAD', 'refs/heads/opencode')
  assert.equal(await guard('check-git', 'git commit -m fixture', linked, root), 'deny')
  assert.equal(await guard('read', 'sample.txt', root, path.join(root, 'missing')), 'deny')
  assert.deepEqual(guardArguments('read', '--hostile'), ['check-file', '--kind', 'read', '--', '--hostile'])
})

test('runtime wrappers reject protected search before native execution; hooks retain gates', async () => {
  const root = await mkdtemp(path.join(source, 'factory-hook-test-'))
  await writeFile(path.join(root, '.env'), 'DUMMY_ONLY=placeholder\n')
  const wrappers = new Map()
  const hooks = new Map()
  let nativeCalls = 0
  const ctx = {
    session: { get: async () => ({ location: { directory: root } }) },
    permission: {
      assert: async () => {},
      hook: async (name, fn) => hooks.set(`permission:${name}`, fn),
    },
    shell: { hook: async (name, fn) => hooks.set(`shell:${name}`, fn) },
    tool: { transform: async (fn) => fn({
      remove: (id) => wrappers.set(id, null),
      update: (id, update) => {
        const tool = { execute: async () => { nativeCalls++; return { content: 'dummy' } } }
        update(tool)
        wrappers.set(id, tool.execute)
      },
    }) },
  }
  await setup(ctx)
  for (const id of ['grep', 'glob'])
    await assert.rejects(wrappers.get(id)({ pattern: '*', path: root }, { sessionID: 'fixture', agent: 'backend-dev' }))
  assert.equal(nativeCalls, 0)
  assert.equal(wrappers.get('opencode_worktree_create'), null)
  assert.equal(wrappers.get('opencode_worktree_remove'), null)
  const event = { action: 'factory_guard_approval', effect: 'allow', resources: ['AGENTS.md'] }
  await hooks.get('permission:evaluate')(event)
  assert.equal(event.effect, 'ask')
})

test('generated native policy and portable runtime merge preserve settings', async () => {
  const code = `import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('guard',sys.argv[1]); g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
p=g.load_policy(sys.argv[2]); c,_=g.load_config(sys.argv[3]); assert c['permissions']==g.generated_permission(p)
m=g.merge_runtime(c,{'model':'fixture/model','mcp':{'servers':{'custom':{'type':'local','command':['dummy']}}}})
assert m['default_agent']=='architect' and m['model']=='fixture/model'
assert 'playwright' in m['mcp']['servers'] and 'custom' in m['mcp']['servers']
assert 'plugins' in g.SYNC_SLICE
print('policy and runtime merge passed')`
  const output = execFileSync('python3', ['-c', code, path.join(source, scripts, 'guard.py'), path.join(source, '.opencode/policies/git-policy.json'), path.join(source, 'opencode.jsonc')], { cwd: source, encoding: 'utf8' })
  assert.match(output, /passed/)
  const policy = JSON.parse(await readFile(path.join(source, '.opencode/policies/git-policy.json'), 'utf8'))
  assert.ok(policy.blocked_tools.includes('opencode_worktree_create'))
})

test('shared QA exception stays canonical and rejects protected or foreign targets', async () => {
  const { root, linked } = await fixture()
  const task = path.join(root, 'artifacts/factory/qa/2026-11-12/BOARD-151')
  for (const cwd of [root, linked]) {
    for (const scope of ['web', 'api', 'mobile', 'factory'])
      assert.equal(await guard('edit', path.join(root, `artifacts/${scope}/qa/2026-11-12/BOARD-151/qa.md`), cwd, root), 'allow')
    for (const output of ['ui.md', 'builder/notes.md', 'route/390x844/light/screenshot.png'])
      assert.equal(await guard('edit', path.join(task, output), cwd, root), 'allow')
    for (const target of [
      path.join(root, 'sample.txt'), path.join(root, '.factory-state/reviews/BOARD-151-ledger.md'),
      path.join(task, '.env'), path.join(task, '.private/notes.md'),
      path.join(root, 'artifacts/unknown/qa/2026-11-12/BOARD-151/qa.md'),
      path.join(root, 'artifacts/factory/qa/not-a-date/BOARD-151/qa.md'),
      task, `${task}/../BOARD-151/qa.md`,
    ]) assert.equal(await guard('edit', target, cwd, root), 'deny', target)
  }
  const other = await fixture()
  assert.equal(await guard('edit', path.join(other.root, 'artifacts/factory/qa/2026-11-12/BOARD-151/qa.md'), linked, root), 'deny')
  await mkdir(task, { recursive: true })
  await symlink(other.root, path.join(task, 'escape'))
  await symlink(task, path.join(root, 'alias'))
  await symlink(path.join(task, 'qa.md'), path.join(task, 'ui.md'))
  for (const cwd of [root, linked]) {
    for (const target of [path.join(task, 'escape/qa.md'), path.join(root, 'alias/qa.md'), path.join(task, 'ui.md')])
      assert.equal(await guard('edit', target, cwd, root), 'deny')
  }
  const nested = path.join(task, 'nested')
  await mkdir(nested)
  git(nested, 'init', '-b', 'main')
  assert.equal(await guard('edit', path.join(nested, 'qa.md'), linked, root), 'deny')
})

test('real adapter preserves configured role decisions for shared QA artifacts', async () => {
  const { root, linked } = await fixture()
  const plugin = path.join(root, '.opencode/plugins/factory-guard/index.mjs')
  await mkdir(path.dirname(plugin), { recursive: true })
  await copyFile(path.join(source, '.opencode/plugins/factory-guard/index.js'), plugin)
  const adapter = await import(pathToFileURL(plugin).href)
  const configCode = `import importlib.util,json,sys
spec=importlib.util.spec_from_file_location('guard',sys.argv[1]);g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
c,_=g.load_config(sys.argv[2]);print(json.dumps(c))`
  const config = JSON.parse(execFileSync('python3', ['-c', configCode, path.join(source, scripts, 'guard.py'), path.join(source, 'opencode.jsonc')], { cwd: source, encoding: 'utf8' }))
  // Seed the hook with ordered native-rule decisions; the adapter must never promote them.
  const nativeEffect = (agent, resource) => {
    let effect = 'ask'
    for (const rule of [...config.permissions, ...config.agents[agent].permissions]) {
      const pattern = rule.resource.split('*').map(s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('.*')
      if (rule.action === 'edit' && new RegExp(`^${pattern}$`).test(resource)) effect = rule.effect
    }
    return effect
  }
  for (const cwd of [root, linked]) {
    const hooks = new Map()
    const wrappers = new Map()
    let calls = 0
    await adapter.setup({
      session: { get: async () => ({ location: { directory: cwd } }) },
      permission: { assert: async () => assert.fail('unexpected approval'), hook: async (name, fn) => hooks.set(name, fn) },
      shell: { hook: async () => {} },
      tool: { transform: async fn => fn({ remove: () => {}, update: (id, update) => {
        const tool = { execute: async () => { calls++; return 'native' } }
        update(tool); wrappers.set(id, tool.execute)
      } }) },
    })
    const task = path.join(root, 'artifacts/factory/qa/2026-11-12/BOARD-151')
    for (const agent of ['qa-reviewer', 'ui-critic', 'frontend-dev', 'backend-dev', 'mobile-dev', 'general']) {
      for (const output of ['qa.md', 'ui.md', 'builder/notes.md', 'route/screenshot.png']) {
        const resource = path.join(task, output)
        const expected = agent === 'qa-reviewer' ? !['ui.md', 'builder/notes.md'].includes(output)
          : agent === 'ui-critic' ? output === 'ui.md' : output === 'builder/notes.md'
        const event = { action: 'edit', resources: [resource], sessionID: 'fixture', agent, effect: nativeEffect(agent, resource) }
        assert.equal(event.effect, expected ? 'allow' : 'deny', `${agent}: ${output}`)
        await hooks.get('evaluate')(event)
        assert.equal(event.effect, expected ? 'allow' : 'deny')
      }
    }
    for (const effect of ['deny', 'ask']) {
      const event = { action: 'edit', resources: [path.join(task, 'qa.md')], sessionID: 'fixture', effect }
      await hooks.get('evaluate')(event)
      assert.equal(event.effect, effect)
    }
    for (const id of ['edit', 'write', 'patch']) {
      const target = path.join(task, 'builder/notes.md')
      const input = id === 'patch' ? { patchText: `*** Begin Patch\n*** Add File: ${target}\n+fixture\n*** End Patch` } : { path: target }
      assert.equal(await wrappers.get(id)(input, { sessionID: 'fixture', agent: 'backend-dev' }), 'native')
    }
    assert.equal(calls, 3)
  }
})
