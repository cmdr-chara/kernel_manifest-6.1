# Kernel build evidence

This record describes host-side build evidence, not a bootable-ROM release.
No phone was accessed. The Android tree still uses its unchanged prebuilt kernel.

## Reproduced baseline failure

[Run 33990250234](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33990250234)
used the 22-project baseline, with Xiaomi kernel
`9f205dab5f27cf81e5036aeb46d7b79c13a751d9`. Its
`KernelBuildCheckSymbolViolations` action failed because `rtl8150.ko` requires
`__skb_pad`, and `rfcomm.ko`, `cdc-acm.ko`, and `usbserial.ko` require
`__tty_port_tty_hangup`. Evidence ZIP SHA-256:
`3a32c2c828808a9a90db4a7cfc41925df2f8301f13827073c2550434e7f646b6`.

[Kernel PR #1](https://github.com/cmdr-chara/android_kernel_xiaomi_mt6878/pull/1)
adds only those two entries to the consumed KMI list. The candidate kernel is
`fc1616578c449fc0bf4a6a061046e2992347f3c6`; enforcement is not disabled.

## Timeout is not a compiler defect

[Run 33994269935](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33994269935)
passed the normalized 22-project identity guard and reached external modules,
then hit the configured 20-minute compilation-step timeout. Evidence ZIP SHA-256:
`c46a5dbeb15831dd709ecae3303d9b1b50f8911a0f7d5cb3f69ca7e77fad9390`.
The subsequent experiment changed only the workflow time budgets, not source
revisions, toolchain, build target, parallelism or KMI checks.

## Successful candidate build

[Run 33995588360](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33995588360)
used manifest commit `b48599ccd2758a15809347c321f98f5286b63574` and
`snapshots/2026-09-05-kmi-candidate.xml`. The downloaded evidence archive was
checked against SHA-256
`85e586610de24ad607817bf26d8dce12121dea2bc2230dc0f9d2d7912a51b26d`
(artifact `9978464534`). Its complete `build.log` ends with:

```text
INFO: Elapsed time: 2229.083s, Critical Path: 1558.28s
INFO: 503 processes: 437 internal, 2 local, 64 processwrapper-sandbox.
INFO: Build completed successfully, 503 total actions
```

Recorded configuration:

```text
KERNEL_VERSION=kernel-6.1
DEFCONFIG_OVERLAYS=malachite.config
SOURCE_DATE_EPOCH=1788641561
```

Target: `//kernel_device_modules-6.1:mgk_64_k61_customer_dist.user`.
The workflow uses `tools/bazel --batch build`, `--jobs=2`, and the pinned
snapshot toolchains. Host evidence records four CPUs, approximately 15 GiB RAM,
and 66 GiB free storage after the build. These are observations, not minimum
system requirements.

`generated-files.txt` contains intermediate, staging and duplicate output paths.
It is NOT a release manifest. `build` does not execute the distribution-copy
program. The archive contains evidence, not flashable images.

## Verification matrix

| Claim | Status | Evidence / next gate |
| --- | --- | --- |
| Exact 22-project candidate sync | PASS | Expanded `manifest.xml` and normalized snapshot guard |
| Customer-user target compiles | PASS | Run 33995588360, 503 successful actions |
| Original missing KMI dependencies repaired | PASS | Same checks retained; candidate target completed |
| Two independent clean builds are reproducible | GAP | Only one complete candidate build inspected |
| Collected distribution is complete | GAP | Run reviewed dist-copy command and inventory outputs |
| Source outputs replace current prebuilts | GAP | Compare configurations, symbols/CRCs, module membership, signing and DTB container format |
| Clean kernel release provenance | GAP | Generated paths include `6.1.167-android14-11-maybe-dirty`; investigate stamping rather than editing the version string |
| DTS/Kconfig warnings resolved | GAP | Warnings remain; configuration-preserving fixes require focused evidence |
| Android packaging, AVB, VINTF and SELinux | GAP | Full Android build and generated-image inspection |
| Boot, recovery, encryption and hardware | GAP | Separate authorization and physical-device validation |

The prebuilt repository records a selective stock/source module mixture based on
ACK 6.1.166, not an exact build of this 6.1.167 source candidate. A successful
source build does not close that compatibility gap. Keep DTBO excluded; do not
change firmware, disable verification, or replace binary artifacts to make an
unproven combination boot.
