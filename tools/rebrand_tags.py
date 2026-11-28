# -*- coding: utf-8 -*-
"""Recreate every release tag on a commit that carries fork branding.

For each tag, check out the tagged tree into a scratch branch, replace the
upstream Telegram handle, repository path and exe metadata with the fork's,
commit, and move the tag onto the new commit. The tag push afterwards makes
the release workflow rebuild that release from the rebranded source.

Only the three branding files are staged, so build leftovers under
tools/_runtime or scratch files can never end up in a tag commit.

Run from the repository root:  python tools/rebrand_tags.py
"""

import os
import subprocess
import sys

TAGS = ["v1.3.8", "v1.4.0", "v1.4.1", "v1.4.2", "v1.4.3", "v1.5.0"]

BRANDING_FILES = [
    "source/patcher/constants.py",
    "source/version.txt",
    ".github/workflows/release.yml",
]


def run(*args, check=True, cwd=None, env=None):
    return subprocess.run(
        ("git",) + args, check=check, text=True, capture_output=True, cwd=cwd, env=env
    )


def main():
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env.update(
        GIT_AUTHOR_NAME="mwri",
        GIT_AUTHOR_EMAIL="218238778+khode-mwri@users.noreply.github.com",
        GIT_COMMITTER_NAME="mwri",
        GIT_COMMITTER_EMAIL="218238778+khode-mwri@users.noreply.github.com",
    )

    changed = {}
    for tag in TAGS:
        old = run("rev-parse", "%s^{commit}" % tag, cwd=root).stdout.strip()
        run("checkout", "-q", "-B", "_rebrand_" + tag, old, cwd=root)

        substitutions = {
            "source/patcher/constants.py": [
                ('TELEGRAM_URL = "https://t.me/AmirOmidi_Dev"',
                 'TELEGRAM_URL = "https://t.me/bxiqm"'),
                ('TELEGRAM_HANDLE = "@AmirOmidi_Dev"',
                 'TELEGRAM_HANDLE = "@bxiqm"'),
                ('GITHUB_REPO = "DrAmir0240/Antigravity-Patcher"',
                 'GITHUB_REPO = "khode-mwri/Antigravity-Patcher-Persian"'),
            ],
            "source/version.txt": [
                ("'CompanyName', 'DrAmir0240'", "'CompanyName', 'khode-mwri'"),
                ("'LegalCopyright', '© 2026'", "'LegalCopyright', '© 2026 khode-mwri'"),
            ],
            ".github/workflows/release.yml": [
                ("Maintainer: DrAmir0240 <https://github.com/DrAmir0240/Antigravity-Patcher>",
                 "Maintainer: mwri <https://github.com/khode-mwri/Antigravity-Patcher-Persian>"),
                ("com.dramir0240.antigravity-patcher", "com.khode-mwri.antigravity-patcher"),
            ],
        }

        staged = []
        for rel in BRANDING_FILES:
            path = root / rel
            if not path.is_file():
                print("  %s: %s missing, skipped" % (tag, rel))
                continue
            text = path.read_text(encoding="utf-8")
            new_text = text
            for before, after in substitutions[rel]:
                new_text = new_text.replace(before, after)
            if new_text != text:
                path.write_text(new_text, encoding="utf-8")
                staged.append(rel)

        if not staged:
            print("  %s: nothing to patch" % tag)
            changed[tag] = (old, old, [])
            continue

        run("add", "--", *staged, cwd=root)
        run(
            "commit", "-q", "-m",
            "chore(release): rebuild %s from fork source with fork branding\n\n"
            "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" % tag,
            cwd=root, env=env,
        )
        new = run("rev-parse", "HEAD", cwd=root).stdout.strip()
        run("tag", "-f", tag, new, cwd=root)
        changed[tag] = (old, new, staged)

    run("checkout", "-q", "main", cwd=root)
    for tag, (old, new, staged) in changed.items():
        print("%s: %s -> %s (%s)" % (tag, old[:7], new[:7], ", ".join(staged) or "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
