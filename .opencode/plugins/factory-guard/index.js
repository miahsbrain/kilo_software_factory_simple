import { access, readFile } from 'node:fs/promises'
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

const execute = promisify(execFile)
const root = fileURLToPath(new URL('../../../', import.meta.url))

export function guardArguments(kind, resource) {
  if (['read', 'edit', 'search'].includes(kind))
    return ['check-file', '--kind', kind, '--', resource]
  return [kind, '--', resource]
}

export async function guard(kind, resource, directory, harness = root) {
  const policy = path.join(harness, '.opencode/policies/git-policy.json')
  const script = path.join(harness, '.opencode/skills/git-worktree/scripts/guard.py')
  try {
    await access(policy)
    await access(script)
    const env = Object.fromEntries(Object.entries(process.env).filter(([k]) => !k.startsWith('GIT_')))
    await execute('python3', [script, ...guardArguments(kind, resource)], {
      cwd: directory, env, timeout: 30000, maxBuffer: 65536,
    })
    return 'allow'
  } catch (error) {
    return error.code === 3 ? 'ask' : 'deny'
  }
}

export async function setup(ctx) {
  let policy
  try {
    policy = JSON.parse(await readFile(path.join(root, '.opencode/policies/git-policy.json'), 'utf8'))
    if (!Array.isArray(policy.blocked_tools)) policy = undefined
  } catch { policy = undefined }
  const directory = async (sessionID) => {
    const session = await ctx.session.get({ sessionID })
    if (!session.location?.directory) throw new Error('Factory guard: session Location unavailable')
    return session.location.directory
  }
  const enforce = async (kind, resource, context) => {
    const effect = await guard(kind, resource, await directory(context.sessionID))
    if (effect === 'deny') throw new Error('Factory guard refused operation; narrow the path or use the board workflow')
    if (effect === 'ask') await ctx.permission.assert({
      sessionID: context.sessionID, agent: context.agent,
      action: 'factory_guard_approval', resources: [resource], save: [],
    })
  }
  await ctx.tool.transform((editor) => {
    if (!policy) {
      for (const tool of editor.list()) editor.remove(tool.id)
      return
    }
    for (const id of policy.blocked_tools) editor.remove(id)
    for (const id of ['read', 'grep', 'glob', 'edit', 'write', 'patch']) {
      editor.update(id, (tool) => {
        const original = tool.execute
        tool.execute = async (input, context) => {
          if (id === 'glob' && (path.isAbsolute(input.pattern) || /\.\.|[\\~$]/.test(input.pattern)))
            throw new Error('Factory guard: glob pattern must stay inside the search path')
          if (id === 'patch') {
            const paths = [...input.patchText.matchAll(/^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$/gm)].map((m) => m[1])
            if (!paths.length) throw new Error('Factory guard: no patch targets')
            for (const target of paths) await enforce('edit', target, context)
          } else {
            const kind = ['grep', 'glob'].includes(id) ? 'search' : id === 'read' ? 'read' : 'edit'
            await enforce(kind, input.path ?? '.', context)
          }
          return original(input, context)
        }
      })
    }
  })
  await ctx.permission.hook('evaluate', async (event) => {
    if (!policy) { event.effect = 'deny'; return }
    if (event.action === 'factory_guard_approval') {
      event.effect = 'ask'
      return
    }
    if (!['read', 'edit', 'shell'].includes(event.action)) return
    const cwd = await directory(event.sessionID)
    for (const resource of event.resources) {
      const checks = event.action === 'shell' ? ['check-git', 'check-delete', 'check-worktree'] : [event.action]
      for (const kind of checks) {
        const effect = await guard(kind, resource, cwd)
        if (effect === 'deny') { event.effect = 'deny'; return }
        if (effect === 'ask') event.effect = 'ask'
      }
    }
  })
  await ctx.shell.hook('create.before', async (event) => {
    for (const kind of ['check-git', 'check-delete', 'check-worktree']) {
      if (await guard(kind, event.command, event.cwd) === 'deny')
        throw new Error('Factory guard refused shell operation')
    }
  })
}

export default { id: 'factory.guard', setup }
