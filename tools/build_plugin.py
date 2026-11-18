#!/usr/bin/env python3
"""Package the repo as an installable Cowork plugin: dist/pm-framework-<version>.plugin (a zip).

  python tools/build_plugin.py [--out DIR]

Includes the plugin manifest, skills, the pmf package, profiles, prompts, templates, framework modules, docs, examples,
README, LICENSE and CHANGELOG. Leaves out tests, tools, private files, caches and build output. Standard library only."""
import argparse
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUDE = ['.claude-plugin', 'skills', 'pmf', 'profiles', 'prompts', 'templates', 'framework', 'docs', 'examples',
           'README.md', 'LICENSE', 'CHANGELOG.md']
SKIP_DIRS = {'__pycache__', '.git', '_private', 'dist'}
SKIP_SUFFIX = ('.pyc', '.pyo', '.tmp')
REQUIRED = ['.claude-plugin/plugin.json', 'pmf/__main__.py', 'pmf/data/lifecycles.json', 'profiles/silicon.json',
            'profiles/software.json', 'skills/setup-program/SKILL.md', 'skills/log-and-triage/SKILL.md',
            'skills/brief-and-report/SKILL.md', 'skills/gate-review/SKILL.md', 'skills/health-check/SKILL.md']


def files(root=ROOT):
    for item in INCLUDE:
        path = os.path.join(root, item)
        if os.path.isfile(path):
            yield item, path
        elif os.path.isdir(path):
            for dp, dns, fns in os.walk(path):
                dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
                for fn in sorted(fns):
                    if fn.endswith(SKIP_SUFFIX):
                        continue
                    full = os.path.join(dp, fn)
                    yield os.path.relpath(full, root).replace(os.sep, '/'), full


def build(out_dir, root=ROOT):
    with open(os.path.join(root, '.claude-plugin', 'plugin.json'), encoding='utf-8') as f:
        meta = json.load(f)
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, '%s-%s.plugin' % (meta['name'], meta['version']))
    names = []
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for arc, full in files(root):
            z.write(full, arc)
            names.append(arc)
    return target, names


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', default=os.path.join(ROOT, 'dist'))
    a = ap.parse_args(argv)
    t, names = build(a.out)
    print('wrote %s (%d files)' % (t, len(names)))
    missing = [n for n in REQUIRED if n not in names]
    if missing:
        sys.exit('package is missing: ' + ', '.join(missing))


if __name__ == '__main__':
    main()
