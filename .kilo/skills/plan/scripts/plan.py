#!/usr/bin/env python3
"""Create or update one ignored implementation plan in the primary control."""

import argparse
import json
import os
from pathlib import Path
import re
import secrets
import stat
import subprocess
import sys


PLANS = Path('docs/implementation_plans')
DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


def git(root, *args):
    # An inherited index or work tree must not redirect ownership or ignore checks.
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    return subprocess.run(['git', *args], cwd=root, env=env, stdout=subprocess.PIPE,
                          check=True).stdout


def primary_control():
    caller = Path.cwd()
    if os.fsencode(caller) + b'\n' != git(caller, 'rev-parse', '--show-toplevel'):
        raise ValueError('run from the owning control Git root or its linked worktree root')
    records = git(caller, 'worktree', 'list', '--porcelain', '-z').split(b'\0\0')
    roots = [os.fsdecode(r.split(b'\0', 1)[0][9:]) for r in records if r.startswith(b'worktree ')]
    if str(caller) not in roots:
        raise ValueError('caller is not a registered checkout')
    root = Path(roots[0])
    if (root.resolve(strict=True) != root or
            os.fsencode(root) + b'\n' != git(root, 'rev-parse', '--show-toplevel') or
            git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir') !=
            git(caller, 'rev-parse', '--path-format=absolute', '--git-common-dir')):
        raise ValueError('invalid primary checkout')
    board, mapping = root / 'docs/BOARD.md', root / '.kilo/repos.json'
    for marker in (board, mapping):
        if marker.resolve(strict=True) != marker or not marker.is_file():
            raise ValueError(f'expected regular control marker: {marker}')
    repos = json.loads(mapping.read_text(encoding='utf-8'))
    if not isinstance(repos, dict) or repos.get('control') != '.':
        raise ValueError('repo map must identify control as "."')
    return root


def publish(directory, filename, body, action):
    if action == 'update' and not stat.S_ISREG(os.stat(
            filename, dir_fd=directory, follow_symlinks=False).st_mode):
        raise ValueError('update requires an existing regular plan')
    temp = '.plan-' + secrets.token_hex(16)
    fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(body)
        if action == 'create':
            os.link(temp, filename, src_dir_fd=directory, dst_dir_fd=directory)
        else:
            os.replace(temp, filename, src_dir_fd=directory, dst_dir_fd=directory)
    finally:
        try:
            os.unlink(temp, dir_fd=directory)
        except FileNotFoundError:
            pass


def write_plan(action, key, body):
    if not re.fullmatch(r'[A-Za-z0-9]+(?:[-_][A-Za-z0-9]+)*', key):
        raise ValueError('expected a plan key, not a path or filename')
    if not body.decode('utf-8').strip():
        raise ValueError('expected nonempty Markdown on stdin')
    root = primary_control()
    target = PLANS / (key + '.md')
    for folder in (root / PLANS.parent, root / PLANS):
        if folder.is_symlink() or os.path.lexists(folder / '.git'):
            raise ValueError(f'symlink or nested repository at {folder}')
    if (git(root, 'ls-files', '-z', '--', PLANS) or
            git(root, 'diff', '--cached', '--name-only', '-z', '--', PLANS)):
        raise ValueError(f'{PLANS} contains tracked or staged paths')
    for path in (str(PLANS) + '/', target):
        git(root, 'check-ignore', '-q', '--', path)
    docs = os.open(root / PLANS.parent, DIRECTORY)
    try:
        if action == 'create':
            try:
                os.mkdir(PLANS.name, mode=0o700, dir_fd=docs)
            except FileExistsError:
                pass
        directory = os.open(PLANS.name, DIRECTORY, dir_fd=docs)
        try:
            publish(directory, target.name, body, action)
        finally:
            os.close(directory)
    finally:
        os.close(docs)
    return root / target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['create', 'update'])
    parser.add_argument('key')
    args = parser.parse_args()
    try:
        print(write_plan(args.action, args.key, sys.stdin.buffer.read()))
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'plan: {error}\n')
