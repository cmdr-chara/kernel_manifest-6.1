# Module coverage evidence

`2026-09-06-module-coverage.json` compares filename observations, not binary ABI.
It was generated with `tools/compare_module_inventory.py` from:

- Kernel build run [33995588360](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33995588360), manifest commit `b48599ccd2758a15809347c321f98f5286b63574`, kernel `fc1616578c449fc0bf4a6a061046e2992347f3c6`. Artifact `9978464534`, ZIP SHA-256 `85e586610de24ad607817bf26d8dce12121dea2bc2230dc0f9d2d7912a51b26d`.
- Prebuilt inspector run [33995771691](https://github.com/cmdr-chara/android_device_xiaomi_malachite-kernel/actions/runs/33995771691), inspector commit `323684f7f64d3b76677ba7e28da88c16fc37b8c9`; binary baseline `9668297071a1d920b8aa6765e148840763c74d50`. Artifact `9978002265`, ZIP SHA-256 `e99282d21c7a9b1928f1f37130f83467f4731c9348b0579aba9869cbc0781ea5`.
- The four load lists at the same prebuilt baseline. Every input file digest is recorded in the report.

After extracting the two evidence archives and checking out the prebuilt baseline, regenerate without loading or replacing any module:

```sh
python3 tools/compare_module_inventory.py \
  --generated-files "$BUILD_EVIDENCE/generated-files.txt" \
  --prebuilt-evidence "$PREBUILT_EVIDENCE/prebuilt-evidence.json" \
  --load-list-root "$PREBUILT_CHECKOUT" > module-coverage.json
```

817 distinct source-output basenames were observed; 467 of the 502 distinct prebuilt basenames match. The remaining 35 include names referenced by normal and recovery load lists. This does not prove those sources are absent or impossible to build: target selection, names and conditional configuration must be traced. Do not delete load entries or drop stock modules to make this check look complete.

The checked-in prebuilts contain three vermagic release strings (6.1.57, 6.1.115 and 6.1.166 families). Filenames alone cannot prove whether this historical mixture is compatible. Matching names can still differ in CRCs, configuration, signing or dependencies. The source build inventory includes intermediate/staging duplicates and is not a populated distribution. Consequently even complete name coverage never promotes `source_equivalence` above GAP or permits deployment.

Next: trace each required-but-unobserved name to its producer/configuration, run the reviewed distribution-copy target, then compare real ELF/version/configuration artifacts and perform a second clean build. See [BUILD_RESULTS.md](../BUILD_RESULTS.md). No phone operation is authorized.
