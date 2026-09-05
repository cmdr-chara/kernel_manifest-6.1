#!/usr/bin/env python3
"""Validate malachite manifest contracts; optionally resolve public remote refs.

No checkout, source execution, build, Git writes, or device access. A successful
ref probe is not a repo-sync, Kleaf-build, or artifact-compatibility certificate.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import xml.etree.ElementTree as ET

OWNED = {
    "kernel-6.1": "android_kernel_xiaomi_mt6878",
    "kernel_device_modules-6.1": "android_kernel_device_modules",
    "vendor/mediatek/kernel_modules": "android_vendor_mediatek_kernel_modules",
    "build/bazel_mgk_rules": "kernel-build-bazel_mgk_rules",
}
LINKS = {
    ("build/kernel", "kleaf/bazel.sh", "tools/bazel"),
    ("build/kernel", "build_test.sh", "build/build_test.sh"),
    ("build/kernel", "config.sh", "build/config.sh"),
    ("kernel-6.1", "build.config.constants", "build.config.constants"),
    ("kernel_device_modules-6.1", "build.config.malachite", "build.config"),
    ("build/bazel_mgk_rules", "BUILD.bazel", "BUILD"),
    ("build/bazel_mgk_rules", "kleaf/bazel.WORKSPACE", "WORKSPACE"),
}
SHA = re.compile(r"[0-9a-f]{40}")


def safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(path.parts) and not path.is_absolute() and ".." not in path.parts and ".git" not in path.parts and path.as_posix() == value and "\\" not in value and ":" not in value


def validate(root: ET.Element) -> list[str]:
    errors = []
    if root.tag != "manifest":
        return ["Expected manifest root"]
    remotes = {r.get("name"): r.get("fetch") for r in root.findall("remote")}
    if len(remotes) != len(root.findall("remote")):
        errors.append("Duplicate remote")
    if remotes.get("cmdr-chara") != "https://github.com/cmdr-chara/":
        errors.append("Owned remote must resolve to cmdr-chara")
    defaults = root.findall("default")
    if len(defaults) != 1:
        return errors + ["Exactly one default is required"]
    default = defaults[0]
    if default.get("remote") not in remotes or not default.get("revision"):
        errors.append("Unresolvable default")
    paths, links, destinations, seen_owned = set(), set(), set(), set()
    for project in root.findall("project"):
        path = project.get("path", project.get("name", ""))
        if not safe_path(path) or path in paths:
            errors.append(f"Unsafe or duplicate project path: {path}")
        paths.add(path)
        remote = project.get("remote", default.get("remote"))
        revision = project.get("revision", default.get("revision", ""))
        if remote not in remotes or not revision:
            errors.append(f"Unresolvable project: {path}")
        if path in OWNED:
            seen_owned.add(path)
            if project.get("name") != OWNED[path] or remote != "cmdr-chara":
                errors.append(f"Wrong owned project identity: {path}")
            if not SHA.fullmatch(revision):
                errors.append(f"Unpinned owned project: {path}")
            if project.get("upstream") != "refs/heads/lineage-23.2":
                errors.append(f"Missing baseline upstream hint: {path}")
        elif remote != "aosp":
            errors.append(f"Unexpected non-AOSP dependency: {path}")
        for link in project.findall("linkfile"):
            src, dest = link.get("src", ""), link.get("dest", "")
            if not safe_path(src) or not safe_path(dest) or dest in destinations:
                errors.append(f"Unsafe or duplicate linkfile: {path}:{dest}")
            destinations.add(dest)
            links.add((path, src, dest))
    if seen_owned != set(OWNED):
        errors.append("Missing owned project")
    if links != LINKS:
        errors.append("Kernel entry-point linkfile contract changed")
    if len(paths) != 22:
        errors.append("Expected 22 baseline projects; review dependency changes explicitly")
    return errors


def probe(item: dict) -> dict:
    result = dict(item)
    ref = item["upstream"] if SHA.fullmatch(item["revision"]) else item["revision"]
    if not ref.startswith("refs/"):
        ref = "refs/heads/" + ref
    try:
        run = subprocess.run(["git", "ls-remote", "--exit-code", item["url"], ref],
                             capture_output=True, text=True, timeout=90,
                             env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        rows = [line.split() for line in run.stdout.splitlines() if line.strip()]
        matches = [sha for sha, name in rows if name == ref and SHA.fullmatch(sha)]
        if run.returncode or len(matches) != 1:
            raise ValueError(run.stderr.strip()[-1500:] or f"Ref not advertised: {ref}")
        result["resolved_revision"] = matches[0]
        if SHA.fullmatch(item["revision"]) and matches[0] != item["revision"]:
            result.update(status="STALE", detail="Branch moved; pinned object reachability requires an explicit fetch")
        else:
            result["status"] = "PASS"
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        result.update(status="FAIL", detail=str(error))
    return result


def resolve(root: ET.Element) -> list[dict]:
    remotes = {r.get("name"): r.get("fetch") for r in root.findall("remote")}
    default = root.find("default")
    items = []
    for project in root.findall("project") + root.findall("superproject"):
        remote = project.get("remote", default.get("remote"))
        items.append({"kind": project.tag, "path": project.get("path", project.get("name")),
                      "url": remotes[remote].rstrip("/") + "/" + project.get("name"),
                      "revision": project.get("revision", default.get("revision")),
                      "upstream": project.get("upstream", "")})
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(probe, items))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", nargs="?", type=Path, default=Path("default.xml"))
    parser.add_argument("--resolve", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("manifest-evidence"))
    args = parser.parse_args()
    root = ET.parse(args.manifest).getroot()
    errors = validate(root)
    print(json.dumps({"static": "FAIL" if errors else "PASS", "errors": errors}, indent=2))
    if errors or not args.resolve:
        return bool(errors)
    if args.output.exists():
        parser.error("Output must not exist; evidence is never overwritten")
    args.output.mkdir(parents=True)
    results = resolve(root)
    report = {"claim": "Remote ref resolution only", "build": "GAP", "results": results}
    (args.output / "remote-refs.json").write_text(json.dumps(report, indent=2) + "\n")
    for result in results:
        print(f"{result['status']} {result['path']}: {result.get('resolved_revision', result.get('detail'))}")
    if all(result["status"] == "PASS" for result in results):
        for project, result in zip(root.findall("project") + root.findall("superproject"), results):
            project.set("revision", result["resolved_revision"])
            project.set("upstream", result["upstream"] or "refs/heads/" + result["revision"].removeprefix("refs/heads/"))
        ET.indent(root)
        ET.ElementTree(root).write(args.output / "resolved.xml", encoding="utf-8", xml_declaration=True)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
