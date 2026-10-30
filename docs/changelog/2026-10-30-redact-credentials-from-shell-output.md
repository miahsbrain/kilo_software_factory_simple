# Redact credentials from every shell command's output

**Date:** 2026-10-30
**Board:** BOARD-002
**Branch:** `chore/redact-credentials-from-every-shell-command`

## What happened

The machine's global git config carried two `url.https://<token>@github.com/.insteadOf` rewrites,
written by VS Code's Dev Containers GitHub Authentication integration at container provisioning.
Because `insteadOf` rewrites the URL, `git remote -v` printed the credential in plaintext. A
documentation task ran `git remote -v` on six of the 75 microservice repositories, and the token
landed in an agent transcript and in the session database.

The token was never committed. Every persistent location was checked and is clean: the 75
repositories' tracked files and full git history, the control repo, the host-mounted workspace, the
`kilo-config` docker volume and the `vscode-server` mount. The only copy outside the git config
was the session transcript store, which sits on the container's overlay filesystem and does not
survive the container.

## The two fixes

### 1. The credential left the URL

`url.<base>.insteadOf` is the wrong place for a token. Every command that touches a remote
substitutes it into the URL, so every command that prints a URL discloses the credential.

The rewrite is removed. The token moved to `/home/node/.git-credentials` (mode `600`), and git's
credential helper serves it:

    [credential]
        helper = store --file=/home/node/.git-credentials

`git remote -v` now prints `https://github.com/Inhouz-Cloud-AI/payment_ms.git` and nothing else.
`git ls-remote` still authenticates. The credential is in no URL, so no routine git command can
disclose it.

The VS Code credential helper that was already configured does not answer in this container — the
extension's GitHub session is not available to it — so the helper alone was not enough. That is
why the token is in the store file rather than left to the helper.

### 2. The output stream is scrubbed

The first fix closes the git vector. It does not close the general one: any tool that prints a
credential puts it in the agent's context, whether it is git, curl, a deployment script, or the
agent's own deployment tool.

`.devcontainer/kilo-redact.sh` closes it. It is loaded as the container's `$BASH_ENV` startup file
and redirects the shell's stdout and stderr through a `sed` filter that replaces:

- `ghp_`, `ghs_`, `gho_`, `ghu_`, `ghr_` and `github_pat_` tokens;
- the `x-access-token:<value>` form;
- a URL with an inline `user:password@`;
- a `KEY=`, `TOKEN=`, `SECRET=`, `PASSWORD=`, `PASSWD=` or `CREDENTIAL=` assignment;
- a bearer header value.

with `<REDACTED_TOKEN>`.

## Why `$BASH_ENV` and not `~/.bashrc`

Kilo Code runs shell tools as `/bin/bash -c "<command>"`. Debian's `~/.bashrc` opens with:

    case $- in
        *i*) ;;
          *) return;;
    esac

so it returns immediately for a non-interactive shell. A function defined there is never defined
for the agent. This was measured, not assumed: a probe variable appended to `~/.bashrc` was
invisible to every `bash -c`, `bash -lc` and `bash -ic` invocation.

`$BASH_ENV` is the one startup file bash always reads for a non-interactive shell. A dedicated file
pointed at by `devcontainer.json` → `remoteEnv.BASH_ENV` was measured to load correctly.

## What it preserves

The filter runs on the byte stream, so it cannot change what the agent reads unless a credential
is present:

| Property | Result |
|---|---|
| Output with no credential | byte-identical, including binary output (md5 checked) |
| Exit code | preserved |
| stdout and stderr | kept on separate streams |
| Output order | preserved |
| Overhead | about 2 ms per command |

`LC_ALL=C` keeps `sed` byte-oriented, which is what makes the binary passthrough exact.

## The limits

- The filter covers shell output. It does not cover a credential the harness reports outside the
  shell, or one pasted into a prompt.
- It is a backstop. The credential belongs in the credential store, not in a URL, not in a command
  line and not in a document.
- It runs on every `bash`, including build scripts. A script that depends on a byte-exact binary
  stream or on stdout being a terminal would notice the difference.

## What the user still has to do

**Rotate the token.** It was printed in plaintext once. A classic `ghp_` personal access token
never expires on its own, so rotation is the only way to retire the copy that reached the
transcript.

## Files

| File | Change |
|---|---|
| `.devcontainer/kilo-redact.sh` | new — the redaction startup file |
| `.devcontainer/test-kilo-redact.sh` | new — 14 checks |
| `.devcontainer/devcontainer.json` | `remoteEnv.BASH_ENV`, and the install step in `postCreateCommand` |
| `docs/ENVIRONMENT.md` | `BASH_ENV`, the credential store path, the git config keys |
| `docs/STACK.md` | the redaction section |
| `docs/RISKS.md` | the token risk updated to the fixed state, plus the filter's residual risk |
| `docs/DECISIONS.md` | ADR-049, ADR-050 |
| `AGENTS.md` | §B11 — the rule that keeps a credential out of a URL, so it never reaches a transcript |
