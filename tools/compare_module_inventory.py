#!/usr/bin/env python3
"""Compare observed build filenames with prebuilt/load-list requirements, read-only.

Name coverage is necessary, not proof of ABI compatibility or dist completeness.
The generated-files input can contain duplicate/intermediate outputs. No module
is loaded, copied into a device tree or selected for deployment by this tool.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def safe_relative(value):
    if not isinstance(value, str):
        raise ValueError('Expected a relative path string')
    path = PurePosixPath(value)
    if (not path.parts or path.is_absolute() or '..' in path.parts or
            path.as_posix() != value or '\\' in value or '\x00' in value):
        raise ValueError('Invalid inventory path: ' + repr(value))
    return path


def observed_names(text):
    names = set()
    for number, line in enumerate(text.splitlines(), 1):
        fields = line.split('\t')
        if len(fields) != 2 or not re.fullmatch(r'[0-9]+', fields[1]):
            raise ValueError(f'Invalid generated-file record {number}')
        path = safe_relative(fields[0])
        if path.suffix == '.ko':
            names.add(path.name)
    if not names:
        raise ValueError('No module outputs observed')
    return names


def compare(generated, prebuilt, load_lists):
    observed = observed_names(generated)
    if prebuilt.get('schema_version') != 1 or prebuilt.get('status') != 'PASS':
        raise ValueError('Require successful version-1 prebuilt structural evidence')
    modules, paths, magics = set(), set(), set()
    for artifact in prebuilt['artifacts']:
        path = safe_relative(artifact['path'])
        if str(path) in paths:
            raise ValueError('Duplicate prebuilt path')
        paths.add(str(path))
        if not re.fullmatch(r'[0-9a-f]{64}', artifact.get('sha256', '')):
            raise ValueError('Missing prebuilt artifact digest')
        if path.suffix == '.ko':
            modules.add(path.name)
            magics.update(artifact.get('modinfo', {}).get('vermagic', []))
    if not modules:
        raise ValueError('No prebuilt modules')
    required = {}
    for name, text in sorted(load_lists.items()):
        entries = []
        for line in text.splitlines():
            line = line.split('#', 1)[0].strip()
            if not line:
                continue
            path = safe_relative(line)
            if len(path.parts) != 1 or path.suffix != '.ko':
                raise ValueError('Invalid load-list entry')
            entries.append(line)
        if not entries:
            raise ValueError('Empty load list')
        required[name] = {'entries': len(entries), 'unique_names': len(set(entries)),
                          'not_observed': sorted(set(entries) - observed)}
    return {'schema_version': 1, 'claim': 'Observed basename coverage only; not ABI or release validation',
            'source_equivalence': 'GAP', 'release_status': 'BLOCKED',
            'observed_source_module_names': len(observed), 'prebuilt_module_names': len(modules),
            'prebuilt_names_observed': len(modules & observed),
            'prebuilt_names_not_observed': sorted(modules - observed),
            'prebuilt_vermagic_values': sorted(magics), 'load_lists': required}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated-files', required=True, type=Path)
    parser.add_argument('--prebuilt-evidence', required=True, type=Path)
    parser.add_argument('--load-list-root', required=True, type=Path)
    args = parser.parse_args()
    names = ['modules.load.system', 'modules.load.vendor', 'modules.load.vendor_ramdisk', 'modules.load.recovery']
    paths = [args.generated_files, args.prebuilt_evidence] + [args.load_list_root / n for n in names]
    if any(p.is_symlink() or not p.is_file() for p in paths):
        parser.error('Inputs must be existing regular non-symlink files')
    result = compare(args.generated_files.read_text(), json.loads(args.prebuilt_evidence.read_text()),
                     {n: (args.load_list_root / n).read_text() for n in names})
    result['input_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
