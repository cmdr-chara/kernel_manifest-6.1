# Malachite MT6878 kernel workspace

This repository coordinates a **separate kernel workspace**, not the Android product checkout. The Android device tree still forces the transitional prebuilt kernel. No file here authorizes phone access, firmware changes or deployment.

## Source snapshots

`default.xml` preserves the original upstream AOSP projects, toolchains and seven entry-point linkfiles. Only the four device-specific projects are redirected to `cmdr-chara` and pinned to inspected `lineage-23.2` commits.

- `snapshots/2026-09-05.xml`: immutable baseline for all **22 projects**, plus the upstream superproject revision. It was actually synced and configured; the original compilation failure is retained in [BUILD_RESULTS.md](BUILD_RESULTS.md).
- `snapshots/2026-09-05-kmi-candidate.xml`: includes that baseline and changes **only** `kernel-6.1` to `fc1616578c449fc0bf4a6a061046e2992347f3c6`, with an exact `base-rev` assertion. This is the two-symbol KMI candidate from [kernel PR #1](https://github.com/cmdr-chara/android_kernel_xiaomi_mt6878/pull/1), not an automatic promotion to the Android prebuilt tree.

The baseline remains reproducible independently of the experimental candidate. A default-branch name or a successful ref lookup is not a complete binary-reproducibility claim. Record the manifest repository commit and generated `repo manifest -r` alongside every build.

## Build topology

| Path | Role |
| --- | --- |
| `common` | Upstream AOSP GKI/common source, not the Xiaomi tree |
| `kernel-6.1` | Owned Xiaomi/MediaTek source at a fixed revision |
| `kernel_device_modules-6.1` | Device/platform modules, malachite configuration and Kleaf target |
| `vendor/mediatek/kernel_modules` | MediaTek connectivity/camera/GPU and other external module projects |
| `build/bazel_mgk_rules` | MediaTek Kleaf rules and root BUILD/WORKSPACE templates |
| `build/kernel`, `prebuilts/*`, `external/*` | Standard upstream build rules and tools, kept upstream |

The manifest links `tools/bazel`, root BUILD/WORKSPACE and build configuration files. The MediaTek WORKSPACE creates local module repositories from the vendor subtree. The verified source target is:

```text
//kernel_device_modules-6.1:mgk_64_k61_customer_dist.user
```

The `ack` variant references a different `common-6.1` path and was not validated by the customer-user test. Do not silently substitute it or the AOSP `common` project for the Xiaomi kernel. The pinned configuration selects clang-r487747c and the malachite overlay.

## Reproduce on an isolated Linux build host

The hosted probes use Ubuntu 24.04, the snapshot-provided tools, and official git-repo commit `b85886fa9f5b4e2189cc5b2f40bd0a80459d4c77`. Their complete setup is checked in under `.github/workflows/`. Use sufficient storage/RAM for the source, toolchains and intermediate outputs; record actual capacity and full logs rather than assuming a configured target is cheap to compile.

Select a reviewed **manifest commit** from this branch and set `MANIFEST_REV` to its full SHA. Use an empty directory, with git-repo installed at the recorded official revision:

```sh
mkdir malachite-kernel
cd malachite-kernel
repo init -u https://github.com/cmdr-chara/kernel_manifest-6.1 \
  -b "$MANIFEST_REV" -m snapshots/2026-09-05.xml \
  --depth=1 --no-use-superproject \
  --repo-url=https://gerrit.googlesource.com/git-repo \
  --repo-rev=b85886fa9f5b4e2189cc5b2f40bd0a80459d4c77
repo sync -c -j4 --fail-fast --no-tags
repo manifest -r -o manifest.lock.xml
export KERNEL_VERSION=kernel-6.1
export DEFCONFIG_OVERLAYS=malachite.config
export SOURCE_DATE_EPOCH="$(git -C kernel-6.1 show -s --format=%ct HEAD)"

tools/bazel --batch cquery \
  //kernel_device_modules-6.1:mgk_64_k61_customer_dist.user \
  --//build/bazel_mgk_rules:kernel_version=6.1 \
  --repo_env=KERNEL_VERSION="$KERNEL_VERSION" \
  --repo_env=DEFCONFIG_OVERLAYS="$DEFCONFIG_OVERLAYS" \
  --repo_env=SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" --jobs=2

tools/bazel --batch build \
  //kernel_device_modules-6.1:mgk_64_k61_customer_dist.user \
  --//build/bazel_mgk_rules:kernel_version=6.1 \
  --repo_env=KERNEL_VERSION="$KERNEL_VERSION" \
  --repo_env=DEFCONFIG_OVERLAYS="$DEFCONFIG_OVERLAYS" \
  --repo_env=SOURCE_DATE_EPOCH="$SOURCE_DATE_EPOCH" --jobs=2
```

For the repair experiment, use the candidate XML in a **separate empty workspace**, with every other parameter recorded. The original snapshot is expected to reproduce the documented KMI failure; do not suppress it. `build` compiles the distribution target's dependencies; it does not run the `copy_to_dist_dir` executable or certify a populated release directory. No images are deployed by these commands.

## Local and hosted validation

From this manifest repository:

```sh
python3 -m unittest discover -s tests -v
python3 tools/verify_manifest.py
python3 tools/verify_manifest.py --resolve --output new-ref-evidence
```

The optional resolution command probes `default.xml`; it is not a general include/extend-project resolver or a substitute for `repo sync`. It rejects stale/mismatched resolution results and does not emit unsupported `upstream` attributes on superproject elements. The candidate build workflow additionally compares the fully expanded, synced 22-project inventory against the baseline with exactly one permitted revision change.

All final workflows use read-only repository permissions and publish evidence, not a flashable release. Artifacts are retained for seven days. The source-kernel repair's mechanical edit was isolated in its own repository/branch; its one-shot writer was replaced with read-only regression CI after the two-line commit.

## Gates before replacing prebuilts

A successful build is not proof that the current Android-consumed artifacts were reproduced. The prebuilt repository describes a selective stock/source module migration and uses an earlier ACK level than this source HEAD. Retain it as the compatibility baseline.

Compare configuration, Image/DTB provenance and placement, all expected module inventories, Module.symvers/KMI, vermagic/version CRCs, signing and load order. Run the relevant ABI checks and two clean reproducibility builds before claiming stable or bit-identical outputs. Then validate Android packaging, image sizes, VINTF, SELinux, encryption/recovery and the separately authorized device matrix. Keep DTBO excluded as documented in the device history; never compensate for a source mismatch by downgrading regional firmware, writing calibration-bearing partitions or disabling verification.

Full twelve-repository architecture, historical fixes and phone safety policy live in the owned [device bring-up documentation](https://github.com/cmdr-chara/android_device_xiaomi_malachite/tree/revival/workspace-audit/bringup).
