# Configuration-preserving repair evidence

[Run 33998173925](https://github.com/cmdr-chara/kernel_manifest-6.1/actions/runs/33998173925)
completed at manifest commit `9e2f7d222b1ec6fea4d4daef454e9ed0605bfce3`.
Artifact `9978725140` was downloaded and verified against ZIP SHA-256
`3af50e4ee72abc75a29a74507e50bb2aeb2164bc5f1581cbc983580546144f5c`.

## Compared sources

The baseline is the 22-project KMI candidate documented in [BUILD_RESULTS.md](BUILD_RESULTS.md).
Only two source revisions changed in the configuration experiment:

| Project | Baseline | Candidate |
| --- | --- | --- |
| kernel_device_modules-6.1 | 034b70b1cbe1bb56f134bcb9d462daaec89aec7b | 1f98227e12a7bf94e5af8cc43501c0a4e376a422 |
| build/bazel_mgk_rules | d8ca975a69cedbfb9c24491fb5ef35ea4443498d | f955699182243b3bd9aa31b8938f33f8689cc8a1 |

The exact other 20 project identities, revisions and linkfiles were checked.
Toolchains, build arguments and `SOURCE_DATE_EPOCH=1788641561` were held constant.

## Actual checks

| Claim | Status | Result |
| --- | --- | --- |
| Full selected Linux 6.1 configuration preserved | PASS | `mgk_64_k61.user_config` produced byte-identical before/after `.config` files |
| Native Starlark serializer regression reproduced | PASS | Baseline normal string passed; quotes, backslashes and embedded newlines failed for the expected generated-configuration reasons |
| Native serializer fix | PASS | All four strings round-tripped through the production repository rule using the pinned Bazel/JDK |
| Complete distribution rebuilt with these two repairs | GAP | This experiment built the configuration target only |
| Binary reproducibility, ABI and current prebuilt equivalence | GAP | Separate comparison and clean-build gates |
| Android build, boot and hardware | GAP | No device operations occurred |

Both `.config` files are 246,778 bytes with SHA-256:
`5e192377b16b0807adea0136acbb3ca4175399ff66d57d846f3138e098262339`.

## Reuse the candidate without manual source edits

`snapshots/2026-09-06-config-candidate.xml` includes the immutable KMI snapshot
and extends only the two reviewed projects. Exact `base-rev` assertions protect
against accidentally applying this overlay to another baseline. Each updated
project has its own review-branch upstream hint; standard upstream toolchains
are unchanged.

Initialize an empty kernel build workspace with this manifest file and record
the full manifest repository SHA. Follow the setup in [README.md](README.md),
substituting this XML for the historical baseline. The configuration workflow
now exercises this reusable overlay with `repo init`/`repo sync` rather than
manual per-project checkouts. Its follow-up run is separate evidence for manifest
portability; do not infer that result solely from the earlier successful run.

These repairs do not authorize replacing the Android-consumed kernel artifacts.
The successful earlier source build still lacks reported coverage for 15 module
names in the current prebuilt load lists; see the owned prebuilt repository's
`SOURCE_MIGRATION.md` proposal. Preserve the prebuilt path, DTBO exclusion, firmware
policy and all phone-safety boundaries until the remaining gates are satisfied.
