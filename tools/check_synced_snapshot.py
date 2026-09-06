#!/usr/bin/env python3
"""Check a resolved kernel checkout against the baseline plus one pinned candidate."""
import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET


def inventory(root):
    remotes = {r.get('name'): r.get('fetch') for r in root.findall('remote')}
    default = root.find('default')
    result = {}
    for project in root.findall('project'):
        name = project.get('name')
        path = project.get('path', name)
        revision = project.get('revision', default.get('revision'))
        if path in result or not re.fullmatch(r'[0-9a-f]{40}', revision or ''):
            raise ValueError('Duplicate path or unpinned project')
        remote = remotes[project.get('remote', default.get('remote'))]
        result[path] = (name, remote, revision,
                        tuple(sorted((link.get('src'), link.get('dest')) for link in project.findall('linkfile'))))
    return result


def verify(baseline, actual, kernel_revision):
    if not re.fullmatch(r'[0-9a-f]{40}', kernel_revision):
        raise ValueError('Candidate must be an immutable commit')
    expected = inventory(baseline)
    if len(expected) != 22 or expected['kernel-6.1'][2] != '9f205dab5f27cf81e5036aeb46d7b79c13a751d9':
        raise ValueError('Unexpected inspected baseline')
    name, remote, _, links = expected['kernel-6.1']
    expected['kernel-6.1'] = (name, remote, kernel_revision, links)
    if inventory(actual) != expected:
        raise ValueError('Synced project identity, revision or linkfiles differ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('actual', type=Path)
    parser.add_argument('--kernel-revision', required=True)
    args = parser.parse_args()
    verify(ET.parse(args.baseline).getroot(), ET.parse(args.actual).getroot(), args.kernel_revision)
    print('PASS: all 22 source identities/revisions/linkfiles match the isolated candidate')


if __name__ == '__main__':
    main()
