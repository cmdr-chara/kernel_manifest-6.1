#!/usr/bin/env python3
"""Copy a built Kleaf config and test the production serializer using native Bazel.

Run only in an isolated kernel workspace. This script never checks out sources,
loads modules, invokes device tools or publishes binary artifacts.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

TARGET = '//kernel_device_modules-6.1:mgk_64_k61.user_config'
OPTIONS = ['--//build/bazel_mgk_rules:kernel_version=6.1',
           '--repo_env=KERNEL_VERSION=kernel-6.1',
           '--repo_env=DEFCONFIG_OVERLAYS=malachite.config',
           '--repo_env=SOURCE_DATE_EPOCH=1788641561', '--jobs=2']


def capture_config(workspace, output):
    query = subprocess.run([str(workspace / 'tools/bazel'), '--batch', 'cquery', TARGET,
                            '--output=files', *OPTIONS], cwd=workspace,
                           check=True, text=True, capture_output=True, timeout=180)
    configs = []
    for line in query.stdout.splitlines():
        path = workspace / line.strip()
        if not line.startswith('bazel-out/'):
            raise ValueError(f'Unexpected config output: {line!r}')
        if path.is_dir():
            configs.extend(path.rglob('.config'))
        elif path.name == '.config':
            configs.append(path)
    if not configs:
        directory = workspace / 'bazel-bin/kernel_device_modules-6.1/mgk_64_k61.user_config'
        if directory.is_dir():
            configs.extend(directory.rglob('.config'))
    payloads = {p.read_bytes() for p in configs}
    if len(payloads) != 1:
        raise ValueError(f'Expected one unique .config, found {len(payloads)} from {configs}')
    if output.exists():
        raise ValueError('Refusing to overwrite captured evidence')
    output.write_bytes(payloads.pop())
    print(f'PASS: captured {TARGET} from {len(configs)} matching output copies')


def native_serializer(workspace, source, expect_fixed):
    bazel = workspace / 'prebuilts/bazel/linux-x86_64/bazel'
    jdk = workspace / 'prebuilts/jdk/jdk11/linux-x86'
    skylib = workspace / 'external/bazel-skylib'
    if not bazel.is_file() or not (jdk / 'bin/java').is_file():
        raise ValueError('Pinned native Bazel/JDK is missing')
    cases = [('plain', 'malachite.config', True), ('quote', 'malachite"test', False),
             ('backslash', r'kernel\new', False), ('newline', 'one\ntwo', False)]
    for name, value, works_before in cases:
        with tempfile.TemporaryDirectory(prefix='mgk-native-') as temporary:
            work = Path(temporary)
            shutil.copyfile(source, work / 'key_value_repo.bzl')
            (work / 'WORKSPACE').write_text(
                'workspace(name = "serializer_test")\n' +
                f'local_repository(name = "bazel_skylib", path = {json.dumps(str(skylib))})\n' +
                'load("//:key_value_repo.bzl", "key_value_repo")\n' +
                f'key_value_repo(name = "values", additional_values = {{"EXTRA": {json.dumps(value)}}})\n')
            (work / 'check.bzl').write_text(
                'def verify(actual, expected):\n    if actual != expected:\n        fail("Configuration string did not round-trip")\n')
            (work / 'BUILD').write_text(
                'load("@values//:dict.bzl", "DEFCONFIG_OVERLAYS", "EXTRA")\n' +
                'load("//:check.bzl", "verify")\n' +
                f'verify(DEFCONFIG_OVERLAYS, {json.dumps(value)})\n' +
                f'verify(EXTRA, {json.dumps(value)})\nfilegroup(name = "check")\n')
            env = dict(os.environ, DEFCONFIG_OVERLAYS=value)
            command = [str(bazel), '--batch', f'--server_javabase={jdk}',
                       f'--output_user_root={work / "output"}', 'query', '//:check', '--noshow_progress']
            result = subprocess.run(command, cwd=work, env=env, text=True,
                                    capture_output=True, timeout=90)
            success = result.returncode == 0
            expected = expect_fixed or works_before
            if not success and not expected and not any(marker in result.stderr for marker in ('dict.bzl', 'Configuration string did not round-trip')):
                raise ValueError(f'Failure was not caused by generated configuration: {result.stderr[-3000:]}')
            if success != expected:
                raise ValueError(f'Native {name}: expected success={expected}, exit={result.returncode}\n{result.stderr[-6000:]}')
            print(f'PASS: native Starlark {name}; success={success}; expected={expected}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    parser.add_argument('--output-config', type=Path)
    parser.add_argument('--serializer', type=Path)
    parser.add_argument('--expect-fixed', action='store_true')
    args = parser.parse_args()
    root = args.workspace.resolve()
    if not (root / '.repo').is_dir():
        parser.error('Expected an isolated repo-managed kernel workspace')
    if args.output_config:
        capture_config(root, args.output_config)
    if args.serializer:
        native_serializer(root, args.serializer, args.expect_fixed)
    if not args.output_config and not args.serializer:
        parser.error('Select a config capture or serializer check')


if __name__ == '__main__':
    main()
