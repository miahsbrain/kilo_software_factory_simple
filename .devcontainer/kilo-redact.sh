#!/usr/bin/env bash
# Credential redaction for every shell command the agent runs.
#
# Kilo Code executes shell tools as `/bin/bash -c "<command>"`. Debian's ~/.bashrc
# returns immediately for a non-interactive shell, so a function defined there is never
# defined for the agent. $BASH_ENV is the one startup file bash always reads for a
# non-interactive shell, so this file is installed there and pointed at by
# devcontainer.json -> remoteEnv.BASH_ENV.
#
# The shell's own stdout and stderr are redirected through the filter, so every byte the
# agent reads has been scrubbed, whatever command produced it.

# ---- protected-file guard -------------------------------------------------------------
# Kilo's permission map blocks the read/grep/glob/list tools by path. A shell command has no
# path awareness, so this guard refuses a `bash -c` command whose text names a protected file
# (.env, git config, git credentials, .npmrc, private keys). It runs for every shell Kilo
# starts, in every subfolder and every repository, so the root policy needs no copies.
#
# .env.example carries no secret and stays readable.
_kilo_protected_re='(^|[^A-Za-z0-9_-])\.env([^A-Za-z0-9_-]|$)|\.git/config|\.git-credentials|(^|[^A-Za-z0-9_-])\.gitconfig|\.config/git/(config|credentials)|(^|[^A-Za-z0-9_-])\.npmrc|(^|[^A-Za-z0-9_-])id_rsa|\.(pem|key|p12)([^A-Za-z0-9]|$)'

_kilo_guard_paths() {
    local cmd="${BASH_EXECUTION_STRING:-}"
    [ -n "$cmd" ] || return 0
    local probe="${cmd//.env.example/__KILO_ENV_EXAMPLE__}"
    if [[ $probe =~ $_kilo_protected_re ]]; then
        printf '%s\n' '[GUARD] Blocked: this command references a protected file (.env, git config, git credentials, .npmrc or a private key). Ask the user if you need it.' >&2
        exit 1
    fi
}
_kilo_guard_paths

# ---- credential redaction -------------------------------------------------------------

_kilo_redact() {
    LC_ALL=C sed -E \
        -e 's/(gh[pousr]_[A-Za-z0-9]{16,})/<REDACTED_TOKEN>/g' \
        -e 's/(github_pat_[A-Za-z0-9_]{16,})/<REDACTED_TOKEN>/g' \
        -e 's#(x-access-token:)[^@[:space:]]+#\1<REDACTED_TOKEN>#g' \
        -e 's#(://[^:/[:space:]]+):[^@[:space:]]+@#\1:<REDACTED>@#g' \
        -e 's/([A-Za-z0-9_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Za-z0-9_]*)=[^[:space:]]+/\1=<REDACTED>/g' \
        -e 's/([Aa]uthorization:[[:space:]]*[Bb]earer[[:space:]]+)[A-Za-z0-9._~+/-]{10,}/\1<REDACTED_TOKEN>/g'
}

# LC_ALL=C keeps sed byte-oriented, so output that holds no credential is unchanged.
# A missing sed must not take the whole shell down with it.
if command -v sed >/dev/null 2>&1; then
    exec > >(_kilo_redact)
    exec 2> >( _kilo_redact >&2 )
fi

# To scrub one stream by hand, pipe it through the function:
#
#   some-command | _kilo_redact
#
# To cover a tool that writes to a file rather than to stdout, scrub the file itself:
#
#   _kilo_redact < some-file > some-file.clean
