# Kernel manifest agent instructions

## Workspace contracts

- This repository coordinates a separate kernel workspace, not the Android product checkout. Its instructions do not automatically become root policy for other synced Git projects.
- Preserve pinned revisions, project identities, linkfiles, upstream toolchains, and candidate `base-rev` assertions. Do not replace the Xiaomi kernel path with AOSP common or substitute another target merely because it configures.
- Keep historical snapshots independently reproducible. New integration inputs belong in a new candidate record; retain the manifest commit and resolved `repo manifest -r` with build evidence.
- Preserve KMI/ABI enforcement. Compilation, configuration equivalence, module-name coverage, a populated distribution, and bit-reproducibility are different claims.
- Never copy an arbitrary output directory over Android-consumed prebuilts or remove unmatched modules to make coverage green. Firmware, DTBO, signing, and device testing remain separately controlled.

## Guidance and verification

[README.md](README.md) owns the topology, target, and validation commands. [BUILD_RESULTS.md](BUILD_RESULTS.md) and [CONFIG_RESULTS.md](CONFIG_RESULTS.md) are evidence for their named revisions, not blanket release approvals.

For manifest/tool changes, run `python3 -m unittest discover -s tests -v` and `python3 tools/verify_manifest.py`. Network resolution and actual sync/build probes are separate checks; document their inputs and limits when required. Use new output locations for collected evidence.

Completion requires cross-project consistency, relevant rejection tests, and precise candidate evidence. Source/build permission does not authorize phone access, prebuilt replacement, firmware changes, or deployment.
