import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, writeFile, copyFile, symlink, readFile } from 'node:fs/promises'
import { execFileSync } from 'node:child_process'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { guard, guardArguments, setup } from './index.js'

const source = fileURLToPath(new URL('../../../', import.meta.url))
const scripts = '.opencode/skills/git-worktree/scripts'
const git = (cwd, ...args) => execFileSync('git', args, { cwd, stdio: 'pipe' })

async function fixture() {
  const root = await mkdtemp('/tmp/opencode/factory-guard-')
  await mkdir(path.join(root, scripts), { recursive: true })
  await mkdir(path.join(root, '.opencode/policies'), { recursive: true })
  for (const name of ['guard.py', 'worktree.py', 'scope.py'])
    await copyFile(path.join(source, scripts, name), path.join(root, scripts, name))
  await copyFile(path.join(source, '.opencode/policies/git-policy.json'), path.join(root, '.opencode/policies/git-policy.json'))
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
  const root = await mkdtemp('/tmp/opencode/factory-hook-')
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
  const output = execFileSync('python3', ['-c', code, path.join(source, scripts, 'guard.py'), path.join(source, '.opencode/policies/git-policy.json'), path.join(source, 'opencode.jsonc')], { encoding: 'utf8' })
  assert.match(output, /passed/)
  const policy = JSON.parse(await readFile(path.join(source, '.opencode/policies/git-policy.json'), 'utf8'))
  assert.ok(policy.blocked_tools.includes('opencode_worktree_create'))
})
