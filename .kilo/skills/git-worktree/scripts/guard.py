#!/usr/bin/env python3
"""Guard for destructive shell commands and for git commands in this factory.

Kilo has no hook runner, so this is invoked explicitly before a destructive
command runs:

    guard.py check-delete -- "rm -rf /tmp/scratch"
    guard.py check-worktree -- "git worktree add .kilo/worktrees/x -b feat/x main"
    guard.py check-git -- "git push origin main"
    guard.py check-policy [--write]
    guard.py sync --repo <id> [--apply]
    guard.py check-repos
    guard.py policy

check-delete allows deletion only inside a linked worktree (the one under
.kilo/worktrees/<slug>/) or inside a temp root (/tmp, /private/tmp,
/var/folders, $TMPDIR) but never a temp root itself. Anything inside the main
checkout that is not a linked worktree, the repository root, the filesystem
root and $HOME are denied.

check-worktree requires every `git worktree add|move` target to resolve inside
<repo-root>/.kilo/worktrees/.

check-git reads the canonical policy from .kilo/policies/git-policy.json and
evaluates the git command against it: the context checks first (protected
branch, branch switch inside a worktree, raw worktree remove), then the bash
rules with LAST MATCH WINS, exactly like Kilo's own permission evaluation.

check-policy proves that the permission map in kilo.jsonc still matches the
policy file. --write regenerates it; policy prints it for a human to paste.

sync copies the .kilo slice, the scope rules and the permission map from the
control repo into another repo named in .kilo/repos.json. It is a dry run
unless --apply is given. check-repos proves that the map and the apps/ layout
agree.

Exit codes: 0 allowed, 1 denied, 2 usage error, 3 needs the user's approval.
A failure inside the guard never blocks work: it exits 0 with a note.
"""

import argparse
import fnmatch
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

RM_CMDS = {"rm", "rmdir", "unlink", "trash"}
TEMP_ROOTS = ["/tmp", "/private/tmp", "/var/folders", "/private/var/folders"]
GIT_VALUE_OPTS = {
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--exec-path",
    "--config-env",
}
ADD_VALUE_OPTS = {"-b", "-B", "--reason"}
LINKED_MARKER = os.sep + ".kilo" + os.sep + "worktrees" + os.sep
SYNC_SLICE = ["agent", "command", "skills", "policies", "scopes"]
SCHEMA_URL = "https://app.kilo.ai/config.json"

OK = 0
DENIED = 1
USAGE = 2


def segments(command):
    """Split a shell command into simple-command token lists. Quotes are honoured; nothing runs."""
    out, tokens, cur, has, quote = [], [], "", False, None
    i = 0

    def push_token():
        nonlocal cur, has
        if has:
            tokens.append(cur)
        cur, has = "", False

    while i < len(command):
        c = command[i]
        if quote:
            if c == quote:
                quote = None
            elif c == "\\" and quote == '"' and i + 1 < len(command):
                i += 1
                cur += command[i]
            else:
                if c == "$" and quote == "'":
                    cur += "\0"
                else:
                    cur += c
        elif c in "'\"":
            quote, has = c, True
        elif c == "\\" and i + 1 < len(command):
            i += 1
            cur += command[i]
            has = True
        elif c in " \t":
            push_token()
        elif c in ";\n|&()":
            push_token()
            if tokens:
                out.append(tokens)
            tokens = []
        else:
            cur += c
            has = True
        i += 1
    push_token()
    if tokens:
        out.append(tokens)
    return out


def expand(word, env, local):
    """Expand ~ and $VAR like the shell. None when the value cannot be known before it runs."""
    if "$(" in word or "`" in word:
        return None
    s = re.sub(r"^~(?=/|$)", lambda m: env.get("HOME", "~"), word)
    unknowable = []

    def var(m):
        name = m.group(1) or m.group(2)
        if name in local:
            unknowable.append(name)
        return env.get(name, "")

    s = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}|\$([A-Za-z_][A-Za-z0-9_]*)", var, s)
    if unknowable:
        return None
    return s.replace("\0", "$")


def under(path, root):
    return path == root or path.startswith(root.rstrip(os.sep) + os.sep)


def real(path):
    return os.path.realpath(path) if os.path.exists(path) else path


def git_out(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(
            ["git", "-C", cwd] + list(args),
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout.strip() if r.returncode == 0 else None


def git_rc(cwd, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    try:
        r = subprocess.run(
            ["git", "-C", cwd] + list(args),
            capture_output=True,
            text=True,
            env=env,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1
    return r.returncode


def list_worktrees(cwd):
    out = git_out(cwd, "worktree", "list", "--porcelain") or ""
    wts = []
    for block in out.split("\n\n"):
        wt = {"path": "", "head": "", "branch": None, "bare": False}
        for line in block.splitlines():
            key, _, val = line.partition(" ")
            if key == "worktree":
                wt["path"] = val
            elif key == "HEAD":
                wt["head"] = val
            elif key == "branch":
                wt["branch"] = val[len("refs/heads/") :] if val.startswith("refs/heads/") else val
            elif key == "bare":
                wt["bare"] = True
        if wt["path"]:
            wts.append(wt)
    return wts


def repo_context(cwd):
    """Where the repository is, and whether this shell sits in a linked worktree."""
    top = git_out(cwd, "rev-parse", "--show-toplevel")
    if not top:
        return None
    common = git_out(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir") or git_out(
        cwd, "rev-parse", "--git-common-dir"
    )
    wts = list_worktrees(cwd)
    main = wts[0]["path"] if wts else top
    repo_root = real(main)
    top_real = real(top)
    return {
        "top": top_real,
        "repo_root": repo_root,
        "worktrees_root": os.path.join(repo_root, ".kilo", "worktrees"),
        "common": os.path.abspath(common) if common else None,
        "linked": LINKED_MARKER in top_real + os.sep,
    }


def verdict(path, ctx, env):
    """None when the deletion target is fine, else why it is not."""
    forms = {
        os.path.normpath(path),
        os.path.join(os.path.realpath(os.path.dirname(path)), os.path.basename(path)),
    }
    home = os.path.normpath(env["HOME"]) if env.get("HOME") else None
    for p in forms:
        if p == os.sep:
            return "is the filesystem root"
        if home and p == home:
            return "is your home directory"

    if ctx["linked"]:
        for p in forms:
            if under(p, ctx["top"]):
                return None

    temps = list(TEMP_ROOTS)
    if env.get("TMPDIR"):
        temps.append(os.path.normpath(env["TMPDIR"]))
    for p in forms:
        for t in temps:
            if under(p, t) and os.path.normpath(p) != os.path.normpath(t):
                return None

    for p in forms:
        if p == ctx["repo_root"]:
            return "is the repository root (%s)" % ctx["repo_root"]
        if under(p, ctx["worktrees_root"]):
            return (
                "is another linked worktree, not the current one; remove it with "
                "worktree.py cleanup, not with rm"
            )
        if under(p, ctx["repo_root"]):
            return "is inside the main checkout (%s), which is never deleted" % ctx["repo_root"]
    return "is outside the current worktree and the allowed temp roots"


def denial(cmd, raw, resolved, why, ctx):
    if ctx["linked"]:
        where = "the current linked worktree (%s)" % ctx["top"]
        rule = "Deletion is allowed only inside %s" % where
        hint = "Delete inside the worktree, use a temp dir, or ask the user to run it themselves."
    else:
        where = "the main checkout (%s), where no repository path is deletable" % ctx["repo_root"]
        rule = (
            "Deletion is allowed only inside a linked worktree, and this command runs in %s" % where
        )
        hint = (
            "Do not delete anything in the main checkout. Do the work in a linked worktree, "
            "use a temp dir, or ask the user to run it themselves."
        )
    return (
        'Blocked: %s target "%s" resolves to %s, which %s.\n'
        "%s, or inside a temp dir under /tmp or $TMPDIR (never the temp root itself).\n%s"
        % (cmd, raw, resolved, why, rule, hint)
    )


def collect_delete_targets(command, cwd, env, ctx):
    """[(command_name, raw_word, resolved_or_None)] for every deletion target."""
    found, d, local = [], cwd, set()
    for tokens in segments(command):
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            local.add(tokens[0].split("=", 1)[0])
            tokens = tokens[1:]
        while tokens and tokens[0] in ("sudo", "command", "nice", "time", "xargs"):
            tokens = tokens[1:]
        if tokens and tokens[0] in ("export", "local", "read", "for"):
            local.update(re.sub(r"=.*", "", t) for t in tokens[1:] if re.match(r"^[A-Za-z_]", t))
            continue
        if not tokens:
            continue
        cmd, args = os.path.basename(tokens[0]), tokens[1:]
        if cmd == "cd":
            target = expand(args[0], env, local) if args else env.get("HOME")
            d = os.path.normpath(os.path.join(d, target)) if target else d
            continue

        def resolve(word, base=None):
            ex = expand(word, env, local)
            if ex is None or ex == "":
                return None
            return os.path.normpath(os.path.join(base or d, ex))

        if cmd in RM_CMDS:
            words, end = [], False
            for a in args:
                if not end and a == "--":
                    end = True
                elif end or not a.startswith("-") or a == "-":
                    words.append(a)
            for w in words:
                found.append((cmd, w, resolve(w)))
        elif cmd == "find":
            if "-delete" in args or any(
                a == "-exec" and i + 1 < len(args) and os.path.basename(args[i + 1]) in RM_CMDS
                for i, a in enumerate(args)
            ):
                for w in args:
                    if w.startswith("-") or w in ("!", "(", ")"):
                        break
                    found.append(("find", w, resolve(w)))
        elif cmd == "git":
            git_dir, i = d, 0
            while i < len(args) and args[i].startswith("-"):
                if args[i] == "-C" and i + 1 < len(args):
                    git_dir = resolve(args[i + 1]) or git_dir
                    i += 2
                elif args[i] in GIT_VALUE_OPTS:
                    i += 2
                else:
                    i += 1
            rest = args[i:]
            if not rest:
                continue
            sub = rest[0]
            if sub == "clean":
                found.append(("git clean", git_dir, git_dir))
            elif sub == "worktree" and len(rest) > 1 and rest[1] == "remove":
                for w in rest[2:]:
                    if not w.startswith("-"):
                        found.append(("git worktree remove", w, resolve(w)))
            elif sub == "checkout" and "--" in rest:
                for w in rest[rest.index("--") + 1 :]:
                    found.append(("git checkout --", w, resolve(w)))
    return found


def check_delete(command, cwd, ctx, env):
    """None when allowed, else the deny reason."""
    for cmd, raw, resolved in collect_delete_targets(command, cwd, env, ctx):
        if resolved is None:
            continue
        why = verdict(resolved, ctx, env)
        if why:
            return denial(cmd, raw, resolved, why, ctx)
    for tokens in segments(command):
        if not tokens or os.path.basename(tokens[0]) != "git":
            continue
        args = tokens[1:]
        i = 0
        while i < len(args) and args[i].startswith("-"):
            i += 1
        rest = args[i:]
        if not rest:
            continue
        if rest[0] == "branch" and "-D" in rest:
            names = [rest[j + 1] for j, a in enumerate(rest) if a == "-D" and j + 1 < len(rest)]
            for name in names:
                if git_rc(cwd, "merge-base", "--is-ancestor", name, "HEAD") != 0:
                    return (
                        "Blocked: git branch -D %s would delete commits that are not merged into HEAD.\n"
                        "Delete a branch only after its work is merged; use `git branch -d` for a safe delete."
                        % name
                    )
        if rest[0] == "reset" and "--hard" in rest:
            if not ctx["linked"]:
                return (
                    "Blocked: git reset --hard would touch the main checkout (%s).\n"
                    "Do not run destructive git commands in the main checkout; run them inside "
                    "a linked worktree." % ctx["repo_root"]
                )
            status = git_out(cwd, "status", "--porcelain")
            if status:
                return (
                    "Blocked: git reset --hard would discard uncommitted changes in %s.\n"
                    "Commit or stash the work first, then reset." % cwd
                )
    return None


def worktree_targets(command, cwd, env, ctx):
    """[(raw, resolved_or_None)] for every worktree add/move target."""
    found, d = [], cwd
    for tokens in segments(command):
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        cmd, args = tokens[0], tokens[1:]
        if cmd == "cd":
            target = expand(args[0], env, set()) if args else env.get("HOME")
            if target:
                d = os.path.normpath(os.path.join(d, target))
            continue
        if os.path.basename(cmd) != "git":
            continue
        git_dir, i = d, 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C":
                target = expand(args[i + 1] if i + 1 < len(args) else "", env, set())
                if target:
                    git_dir = os.path.normpath(os.path.join(git_dir, target))
                i += 2
            elif args[i] in GIT_VALUE_OPTS:
                i += 2
            else:
                i += 1
        if i >= len(args) or args[i] != "worktree" or i + 1 >= len(args):
            continue
        sub = args[i + 1]
        if sub not in ("add", "move"):
            continue
        positional, j = [], i + 2
        while j < len(args):
            a = args[j]
            if a == "--":
                positional += args[j + 1 :]
                break
            if a in ADD_VALUE_OPTS:
                j += 1
            elif not a.startswith("-") and not re.match(r"^\d*[<>]", a):
                positional.append(a)
            j += 1
        idx = 0 if sub == "add" else 1
        if len(positional) <= idx:
            continue
        raw = positional[idx]
        ex = expand(raw, env, set())
        if ex is None:
            found.append((raw, None))
            continue
        base = ex if os.path.isabs(ex) else os.path.join(ctx["repo_root"], ex)
        found.append((raw, os.path.normpath(base)))
    return found


def check_worktree(command, cwd, ctx, env):
    """None when allowed, else the deny reason."""
    allowed = ctx["worktrees_root"]
    for raw, resolved in worktree_targets(command, cwd, env, ctx):
        if (
            resolved
            and under(resolved, allowed)
            and os.path.normpath(resolved) != os.path.normpath(allowed)
        ):
            continue
        where = ("resolves to " + resolved) if resolved else "cannot be resolved before it runs"
        return (
            'Blocked: worktree path "%s" %s, outside %s.\n'
            "Worktrees live only under %s so cleanup and sweeps can find them.\n"
            "Use: git worktree add .kilo/worktrees/<slug> -b <type>/<slug> <base> (from the repo root)."
            % (raw, where, allowed, allowed)
        )
    return None


PROTECTED_BRANCHES = ("main", "master", "base")
POLICY_REL = os.path.join(".kilo", "policies", "git-policy.json")
REPOS_REL = os.path.join(".kilo", "repos.json")
FALLBACK_KEY = "*"
ASK = 3


def script_project_root():
    """The root of the tree that holds this script, whatever the cwd is."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", "..", "..", ".."))


def find_policy(ctx):
    """(root, policy_path) for the tree that holds the policy file, else (None, None).

    The tree the shell is in wins, so an agent in a worktree guards and
    regenerates the files of that worktree, not the main checkout.
    """
    roots = []
    if ctx:
        roots.append(ctx.get("top"))
        roots.append(ctx.get("repo_root"))
    roots.append(script_project_root())
    for root in roots:
        if not root:
            continue
        path = os.path.join(root, POLICY_REL)
        if os.path.exists(path):
            return root, path
    return None, None


def load_policy(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def pattern_matches(command, pattern):
    """True when the command equals the pattern or starts with the part before its first '*'."""
    if "*" not in pattern:
        return command == pattern
    return command.startswith(pattern.split("*", 1)[0])


def git_commands(command):
    """[(reconstructed, subcommand, args)] for every git command in the shell command."""
    found = []
    for tokens in segments(command):
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        while tokens and tokens[0] in ("sudo", "command", "nice", "time", "xargs"):
            tokens = tokens[1:]
        if not tokens or os.path.basename(tokens[0]) != "git":
            continue
        args = tokens[1:]
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C" or args[i] in GIT_VALUE_OPTS:
                i += 2
            else:
                i += 1
        if i >= len(args):
            continue
        sub = args[i]
        rest = args[i + 1 :]
        found.append(("git %s%s" % (sub, (" " + " ".join(rest)) if rest else ""), sub, rest))
    return found


def context_verdict(policy, command, cwd, ctx):
    """The context rule that fires for this command, or None."""
    for rule in policy.get("context", []):
        if not any(pattern_matches(command, p) for p in rule.get("applies_to", [])):
            continue
        check = rule.get("check")
        if check == "always":
            fired = True
        elif check == "protected_branch":
            branch = git_out(cwd, "rev-parse", "--abbrev-ref", "HEAD")
            fired = branch in PROTECTED_BRANCHES
        elif check == "branch_switch_in_worktree":
            parts = command.split()
            sub = parts[1] if len(parts) > 1 else ""
            rest = parts[2:]
            switches = sub in ("checkout", "switch") and not (
                sub == "checkout" and rest[:1] == ["--"]
            )
            fired = bool(ctx and ctx.get("linked")) and switches
        else:
            fired = False
        if fired:
            return rule
    return None


def bash_verdict(policy, command):
    """(action, reason) from the bash rules, LAST MATCH WINS like Kilo's permission map."""
    action, reason = None, None
    for rule in policy.get("bash", []):
        if pattern_matches(command, rule["pattern"]):
            action = rule["action"]
            reason = rule.get("reason")
    if action is None:
        fallback = policy.get("fallback", {})
        action = fallback.get("action", "allow")
        reason = fallback.get("reason")
    return action, reason


def cmd_check_git(command, cwd, ctx):
    root, path = find_policy(ctx)
    if not path:
        print(
            "policy file not found: %s\n"
            "The canonical guard-rail policy is missing; run guard.py check-policy --write "
            "after creating .kilo/policies/git-policy.json." % POLICY_REL,
            file=sys.stderr,
        )
        return USAGE
    policy = load_policy(path)

    commands = git_commands(command)
    if not commands:
        print("no git command")
        return OK

    for reconstructed, _sub, _rest in commands:
        rule = context_verdict(policy, reconstructed, cwd, ctx)
        if rule:
            action = rule.get("action", "deny")
            reason = rule.get("reason", "")
            if action == "ask":
                print(
                    "needs approval: %s\nreason: %s\nnext: the user must approve it before "
                    "it runs." % (reconstructed, reason)
                )
                return ASK
            print(
                "blocked: %s\nreason: %s\nnext: do not run this command." % (reconstructed, reason)
            )
            return DENIED

        action, reason = bash_verdict(policy, reconstructed)
        if action == "deny":
            print(
                "blocked: %s\nreason: %s\nnext: do not run this command." % (reconstructed, reason)
            )
            return DENIED
        if action == "ask":
            print(
                "needs approval: %s\nreason: %s\nnext: the user must approve it before "
                "it runs." % (reconstructed, reason)
            )
            return ASK

    print("allowed: %s" % command)
    return OK


def strip_jsonc(text):
    """Remove // and /* */ comments that are not inside a string."""
    out, i, n = [], 0, len(text)
    in_string, quote, escaped = False, "", False
    while i < n:
        c = text[i]
        if in_string:
            out.append(c)
            if escaped:
                escaped = False
            elif c == "\\":
                escaped = True
            elif c == quote:
                in_string = False
            i += 1
            continue
        if c in "\"'":
            in_string, quote = True, c
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def load_config(path):
    """(config, error_line). The error line is None when the file parses."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None, None
    try:
        return json.loads(strip_jsonc(text)), None
    except json.JSONDecodeError as exc:
        return None, exc.lineno


FILE_TOOLS = ("read", "grep", "glob", "list")


def generated_permission(policy):
    """The permission block generated from the policy: fallback first, then rules in file order.

    `hidden_paths` is expanded into one deny rule per path for every file-reading tool, so a git
    config or credential file is never readable by `read`, `grep`, `glob` or `list`.
    """
    fallback = policy.get("fallback", {}).get("action", "allow")
    block = {}
    for kind in ("bash", "edit"):
        mapping = {FALLBACK_KEY: fallback}
        for rule in policy.get(kind, []):
            mapping[rule["pattern"]] = rule["action"]
        block[kind] = mapping
    hidden = policy.get("hidden_paths") or {}
    tools = hidden.get("tools") or FILE_TOOLS
    for tool in tools:
        mapping = {FALLBACK_KEY: fallback}
        for path in hidden.get("paths", []):
            mapping[path] = "deny"
        for path in hidden.get("allow", []):
            mapping[path] = "allow"
        block[tool] = mapping
    return block


def permission_block_text(policy):
    return json.dumps({"permission": generated_permission(policy)}, indent=2)


def write_permission_map(config_path, policy, create_missing=False):
    """(expected, message). Writes the generated permission block into config_path."""
    expected = generated_permission(policy)
    existed = os.path.exists(config_path)
    config, bad_line = load_config(config_path)
    if config is None:
        if not create_missing:
            return None, (
                "cannot parse %s%s" % (config_path, (" at line %d" % bad_line) if bad_line else "")
            )
        config = {"$schema": SCHEMA_URL}
    updated = {k: v for k, v in config.items() if k != "permission"}
    updated["permission"] = expected
    with open(config_path, "w", encoding="utf-8") as fh:
        json.dump(updated, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return expected, ("updated" if existed else "created")


def cmd_check_policy(write, cwd, ctx):
    root, path = find_policy(ctx)
    if not path:
        print("policy file not found: %s" % POLICY_REL, file=sys.stderr)
        return USAGE
    policy = load_policy(path)
    expected = generated_permission(policy)

    config_path = os.path.join(root, "kilo.jsonc")
    config, bad_line = load_config(config_path)
    if config is None:
        print(
            "cannot parse %s%s" % (config_path, (" at line %d" % bad_line) if bad_line else ""),
            file=sys.stderr,
        )
        return USAGE

    current = config.get("permission") or {}
    same = set(current) == set(expected) and all(
        list((current.get(kind) or {}).items()) == list(mapping.items())
        for kind, mapping in expected.items()
    )

    if same and not write:
        print("policy in sync")
        return OK

    if write:
        write_permission_map(config_path, policy)
        print("permission map written to %s" % config_path)
        return OK

    print("policy out of sync: %s does not match %s" % (config_path, path))
    print(permission_block_text(policy))
    return DENIED


def cmd_policy(cwd, ctx):
    root, path = find_policy(ctx)
    if not path:
        print("policy file not found: %s" % POLICY_REL, file=sys.stderr)
        return USAGE
    print(permission_block_text(load_policy(path)))
    return OK


def load_worktree_module():
    """The sibling worktree.py, loaded by path so it works from anywhere."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "worktree.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location("worktree", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shell_tree(ctx):
    """The tree the shell is in: the source of the .kilo slice and the scope rules."""
    if ctx:
        top = ctx.get("top")
        if top:
            return top
    return script_project_root()


def control_root(ctx):
    """The control repo's main checkout: the place the target repositories live.

    A nested app repository at apps/<name>/ is not tracked by the control repo,
    so it exists only in the main checkout, never in a worktree of it.
    """
    if ctx:
        root = ctx.get("repo_root")
        if root:
            return root
    return script_project_root()


def repo_targets(source_tree, control, repo_id):
    """(target root, repos map, error). The map in .kilo/repos.json is the only way in.

    The map is read from the tree the shell is in. The target is resolved in
    the control repo's main checkout, except for 'control' itself, which is
    the tree the shell is in.
    """
    wt = load_worktree_module()
    if wt is None:
        return None, None, "worktree.py not found next to guard.py"
    repos, err = wt.load_repos(source_tree)
    if repos is None:
        return None, None, err
    if repo_id == "control":
        return source_tree, repos, None
    target, err = wt.resolve_repo(control, repos, repo_id)
    if err:
        return None, repos, err
    return target, repos, None


def scope_files(source_tree, target, repo_id):
    """[(source, destination)] for the scope rules of this target."""
    pairs = []
    scopes_dir = os.path.join(source_tree, ".kilo", "scopes")
    if repo_id == "control":
        for name in sorted(os.listdir(scopes_dir)) if os.path.isdir(scopes_dir) else []:
            if not name.endswith(".md"):
                continue
            scope_id = name[:-3]
            pairs.append(
                (
                    os.path.join(scopes_dir, name),
                    os.path.join(source_tree, "apps", scope_id, "AGENTS.md"),
                )
            )
        return pairs
    source = os.path.join(scopes_dir, repo_id + ".md")
    if os.path.exists(source):
        pairs.append((source, os.path.join(target, "AGENTS.md")))
    return pairs


def file_state(source, destination):
    """'new', 'changed' or 'identical' for one planned file."""
    if not os.path.exists(destination):
        return "new"
    try:
        with open(source, "rb") as fh:
            a = fh.read()
        with open(destination, "rb") as fh:
            b = fh.read()
    except OSError:
        return "changed"
    return "identical" if a == b else "changed"


def cmd_sync(repo_id, apply, cwd, ctx):
    source_tree = shell_tree(ctx)
    control = control_root(ctx)
    target, repos, err = repo_targets(source_tree, control, repo_id)
    if err:
        print(err, file=sys.stderr)
        return DENIED
    wt = load_worktree_module()
    is_repo = bool(wt) and wt.is_git_repo(target)
    if not is_repo and apply:
        print(
            "target %s is not a git repository; refusing to write into it" % target,
            file=sys.stderr,
        )
        return DENIED
    plan = []
    for folder in SYNC_SLICE:
        source_dir = os.path.join(source_tree, ".kilo", folder)
        if not os.path.isdir(source_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(source_dir):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            rel = os.path.relpath(dirpath, source_dir)
            for name in sorted(filenames):
                if name.endswith(".pyc"):
                    continue
                source = os.path.join(dirpath, name)
                rel_file = name if rel == "." else os.path.join(rel, name)
                plan.append((source, os.path.join(target, ".kilo", folder, rel_file)))
    plan.extend(scope_files(source_tree, target, repo_id))
    config_path = os.path.join(target, "kilo.jsonc")

    print("control repo: %s" % control)
    print(
        "target repo:  %s (%s)%s"
        % (target, repo_id, "" if is_repo else " - not a git repository yet")
    )
    print("plan:")
    written = identical = 0
    for source, destination in plan:
        state = file_state(source, destination)
        if state == "identical":
            identical += 1
        else:
            written += 1
        print("  %-9s %s" % (state, os.path.relpath(destination, target)))
    print("  %-9s %s" % ("regen", os.path.relpath(config_path, target)))
    if not is_repo:
        print("note: the target is not a git repository; --apply would be refused.")

    if not apply:
        print("dry run; re-run with --apply to act")
        return OK

    for source, destination in plan:
        if os.path.realpath(source) == os.path.realpath(destination):
            continue
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copyfile(source, destination)
    policy = load_policy(os.path.join(source_tree, POLICY_REL))
    written_config, message = write_permission_map(config_path, policy, create_missing=True)
    print("permission map %s (%s)" % (os.path.relpath(config_path, target), message))
    print("files written: %d, identical: %d, skipped: 0" % (written, identical))
    return OK


def cmd_check_repos(cwd, ctx):
    source_tree = shell_tree(ctx)
    control = control_root(ctx)
    target, repos, err = repo_targets(source_tree, control, "control")
    if err:
        print(err, file=sys.stderr)
        return DENIED
    problems = []
    registered = set()
    for repo_id in sorted(repos):
        resolved, err = resolve_repo_path(control, repos, repo_id)
        if err:
            problems.append(err)
            continue
        if not os.path.isdir(resolved):
            problems.append("repo %r: %s does not exist" % (repo_id, resolved))
            continue
        registered.add(os.path.realpath(resolved))
        wt = load_worktree_module()
        if not wt or not wt.is_git_repo(resolved):
            print("repo %r: %s - registered, not a git repository yet" % (repo_id, resolved))
            continue
        print("repo %r: %s - git repository" % (repo_id, resolved))
    control_real = os.path.realpath(control)
    if "control" not in repos:
        problems.append("the control repo %s is not registered as 'control'" % control)
    elif control_real not in registered:
        problems.append("the 'control' entry does not point at the control repo %s" % control)
    apps = os.path.join(control, "apps")
    if os.path.isdir(apps):
        for name in sorted(os.listdir(apps)):
            folder = os.path.join(apps, name)
            if os.path.isdir(folder) and os.path.exists(os.path.join(folder, ".git")):
                if os.path.realpath(folder) not in registered:
                    problems.append(
                        "apps/%s is a git repository but is not registered in %s"
                        % (name, REPOS_REL)
                    )
    if problems:
        for problem in problems:
            print("problem: %s" % problem, file=sys.stderr)
        print("the repo map and the layout disagree", file=sys.stderr)
        return DENIED
    print("repos in sync")
    return OK


def resolve_repo_path(control, repos, repo_id):
    """The absolute path of a repo id, or an error message."""
    wt = load_worktree_module()
    if wt is None:
        return None, "worktree.py not found next to guard.py"
    return wt.resolve_repo(control, repos, repo_id)


def main(argv):
    parser = argparse.ArgumentParser(
        prog="guard.py", description="Guard destructive shell commands in this factory."
    )
    sub = parser.add_subparsers(dest="command")

    p_del = sub.add_parser("check-delete", help="allow or deny a destructive shell command")
    p_del.add_argument("shell_command", nargs="?", help="the shell command to inspect")
    p_del.add_argument("rest", nargs=argparse.REMAINDER)

    p_wt = sub.add_parser("check-worktree", help="allow or deny a git worktree add/move path")
    p_wt.add_argument("shell_command", nargs="?", help="the shell command to inspect")
    p_wt.add_argument("rest", nargs=argparse.REMAINDER)

    p_git = sub.add_parser("check-git", help="allow, ask or deny a git command from the policy")
    p_git.add_argument("shell_command", nargs="?", help="the shell command to inspect")
    p_git.add_argument("rest", nargs=argparse.REMAINDER)

    p_pol = sub.add_parser("check-policy", help="prove kilo.jsonc matches the policy file")
    p_pol.add_argument("--write", action="store_true", help="regenerate the permission map")

    p_sync = sub.add_parser("sync", help="copy the guard rails into another repo")
    p_sync.add_argument("--repo", required=True, help="repo id from .kilo/repos.json")
    p_sync.add_argument("--apply", action="store_true", help="act; without it this is a dry run")

    sub.add_parser("check-repos", help="prove the repo map and the apps/ layout agree")

    sub.add_parser("policy", help="print the generated permission block")

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return USAGE

    if args.command in ("check-policy", "policy"):
        cwd = os.getcwd()
        ctx = repo_context(cwd)
        if args.command == "policy":
            return cmd_policy(cwd, ctx)
        return cmd_check_policy(args.write, cwd, ctx)

    if args.command in ("sync", "check-repos"):
        cwd = os.getcwd()
        ctx = repo_context(cwd)
        if args.command == "check-repos":
            return cmd_check_repos(cwd, ctx)
        return cmd_sync(args.repo, args.apply, cwd, ctx)

    parts = [args.shell_command] if args.shell_command else []
    parts.extend(args.rest or [])
    command = " ".join(p for p in parts if p).strip()
    if not command:
        print("no shell command given", file=sys.stderr)
        return USAGE

    cwd = os.getcwd()
    ctx = repo_context(cwd)
    if ctx is None:
        print("not inside a git repository; nothing to guard against")
        return OK

    env = dict(os.environ)
    if args.command == "check-delete":
        reason = check_delete(command, cwd, ctx, env)
    elif args.command == "check-git":
        return cmd_check_git(command, cwd, ctx)
    else:
        reason = check_worktree(command, cwd, ctx, env)

    if reason:
        print(reason, file=sys.stderr)
        return DENIED
    print("allowed: %s" % command)
    return OK


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception as exc:  # a broken guard must never block unrelated work
        print("guard.py internal error, not blocking: %s" % exc, file=sys.stderr)
        sys.exit(OK)
