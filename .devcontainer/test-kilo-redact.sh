#!/usr/bin/env bash
# Proves the redaction in .devcontainer/kilo-redact.sh works, and that it changes
# nothing else. Run it the way the agent's shell runs, with the file as $BASH_ENV:
#
#   BASH_ENV=.devcontainer/kilo-redact.sh bash .devcontainer/test-kilo-redact.sh
#
set -uo pipefail

cd "$(dirname "$0")"
REDACT="./kilo-redact.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Built at run time so that no token-shaped literal is stored in the repository.
FAKE_CLASSIC="ghp_$(printf 'A%.0s' $(seq 1 36))"
FAKE_FINE="github_pat_$(printf 'B%.0s' $(seq 1 82))"

pass=0
fail=0
check() {
    local name="$1" expected="$2" actual="$3"
    if [ "$expected" = "$actual" ]; then
        printf '  ok   %s\n' "$name"
        pass=$((pass + 1))
    else
        printf '  FAIL %s\n       expected: %s\n       actual:   %s\n' "$name" "$expected" "$actual"
        fail=$((fail + 1))
    fi
}

# Runs a command in a shell that has the filter loaded, the way the agent's shell has it.
run() { BASH_ENV="$REDACT" bash -c "$1" 2>"$TMP/err"; }

echo "the filter is loaded by every non-interactive shell"

out=$(BASH_ENV="$REDACT" bash -c "echo \"token $FAKE_CLASSIC end\"")
check "a classic token is removed from stdout" "0" "$(printf '%s' "$out" | grep -c 'ghp_')"
check "the redaction marker is present" "1" "$(printf '%s' "$out" | grep -c '<REDACTED_TOKEN>')"

out=$(run "echo \"token $FAKE_CLASSIC end\" >&2"; cat "$TMP/err")
check "a classic token is removed from stderr" "0" "$(printf '%s' "$out" | grep -c 'ghp_')"

echo "the other credential shapes"

out=$(BASH_ENV="$REDACT" bash -c "echo \"t $FAKE_FINE end\"")
check "a fine-grained token is removed" "0" "$(printf '%s' "$out" | grep -c 'github_pat_')"

out=$(BASH_ENV="$REDACT" bash -c "echo \"t https://x-access-token:$FAKE_CLASSIC@github.com/x end\"")
check "the x-access-token form is removed" "0" "$(printf '%s' "$out" | grep -c 'ghp_')"

out=$(BASH_ENV="$REDACT" bash -c 'echo "t mongodb://admin:sup3rs3cret@cluster0.example.net/db end"')
check "an inline url password is removed" "0" "$(printf '%s' "$out" | grep -c 'sup3rs3cret')"

out=$(BASH_ENV="$REDACT" bash -c 'echo "t OPENROUTER_API_KEY=sk-or-v1-abc123 end"')
check "a key-shaped assignment is removed" "0" "$(printf '%s' "$out" | grep -c 'sk-or-v1')"

out=$(BASH_ENV="$REDACT" bash -c 'echo "t Authorization: Bearer abcdefghijklmnop end"')
check "a bearer header is removed" "0" "$(printf '%s' "$out" | grep -c 'abcdefghijklmnop')"

echo "output without a credential is untouched"

out=$(BASH_ENV="$REDACT" bash -c 'echo "https://github.com/Inhouz-Cloud-AI/payment_ms.git"')
check "a plain url is unchanged" "https://github.com/Inhouz-Cloud-AI/payment_ms.git" "$out"

out=$(BASH_ENV="$REDACT" bash -c 'echo "APP_URL=https://inhouz.io PORT=15180"')
check "a token-free assignment is unchanged" "APP_URL=https://inhouz.io PORT=15180" "$out"

head -c 4096 /dev/urandom > "$TMP/bin.dat"
before=$(md5sum < "$TMP/bin.dat")
after=$(BASH_ENV="$REDACT" bash -c "cat '$TMP/bin.dat'" | md5sum)
check "binary output is byte-identical" "$before" "$after"

echo "the shell still behaves"

st=0; BASH_ENV="$REDACT" bash -c 'exit 7' || st=$?
check "the exit code is preserved" "7" "$st"

out=$(BASH_ENV="$REDACT" bash -c 'for i in 1 2 3; do echo "line $i"; done')
check "output keeps its order" "line 1
line 2
line 3" "$out"

out=$(BASH_ENV="$REDACT" bash -c 'echo "S-OUT"; echo "S-ERR" >&2' 2>"$TMP/err")
check "stdout stays on stdout" "S-OUT" "$out"
check "stderr stays on stderr" "S-ERR" "$(cat "$TMP/err")"

echo "the protected-file guard"

guard_rc() { BASH_ENV="$REDACT" bash -c "$1" >/dev/null 2>"$TMP/err"; echo $?; }

check "a .env read is blocked" "1" "$(guard_rc 'cat .env')"
check "a nested .env read is blocked" "1" "$(guard_rc 'cat config/.env.local')"
check "a git config read is blocked" "1" "$(guard_rc 'cat .git/config')"
check "a credential store read is blocked" "1" "$(guard_rc 'cat /home/node/.git-credentials')"
check "a global git config read is blocked" "1" "$(guard_rc 'cat ~/.gitconfig')"
check "an npmrc read is blocked" "1" "$(guard_rc 'cat .npmrc')"
check "a private key read is blocked" "1" "$(guard_rc 'openssl pkey -in server.key')"
check ".env.example stays readable" "0" "$(guard_rc 'echo .env.example')"
check "a process.env argument is not blocked" "0" "$(guard_rc 'echo process.env')"
check "a plain command is not blocked" "0" "$(guard_rc 'echo safe')"

echo "the repository holds no token-shaped literal"

stored=$(grep -roE 'gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{16,}' "$REDACT" ./test-kilo-redact.sh 2>/dev/null | wc -l)
check "no token-shaped string is stored" "0" "$stored"

echo
printf 'passed %d, failed %d\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
