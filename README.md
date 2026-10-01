# Yuna Calendar Patches

Custom Morphe patches for **Your Calendar Widget 1.71.3** (`de.mash.android.calendar`, tested APK version code 523).

## Import on Android

1. Download `patches-1.0.1.mpp` from this repository's release or the provided original file.
2. In Morphe Manager, import the bundle as a local custom patch source/file (menu wording depends on Manager version).
3. Select the original Your Calendar Widget 1.71.3 APK.
4. Keep **Hide Free Edition reminder events** enabled.
5. Optionally enable **Enable local premium features** (off by default).
6. Patch and install. Back up widget settings first: the re-signed APK normally cannot update the original Play-signed installation in place.

The reminder patch disables only `Utility.createPromotionEvent`. It does not alter real events, reminders, permissions, purchase records, or the local premium checks.

The optional premium patch changes the two local `Utility.isProVersion` checks (product and database variants). It does not create a Google Play purchase/subscription. Google Tasks/Microsoft account features can depend on external OAuth/signature checks and are **not verified** by this patch.

## Build

Based on the official `MorpheApp/morphe-patches-template`, commit `0bbf39c4ff24c7799104f510b165e67c55b9d9cf`. GPLv3; retain upstream LICENSE/NOTICE.

The default build needs only Python 3 and Java 21, and uses hash-pinned public toolchain artifacts:

```sh
python3 scripts/build_public.py
python3 tests/verify_bundle.py
```

The original Gradle build remains available as an alternative. Its official Morphe plugin is hosted on GitHub Packages and needs a GitHub token with `read:packages`; pass credentials through environment variables, never committed files:

```sh
export GITHUB_ACTOR=your-github-user
# Supply GITHUB_TOKEN from protected configuration; never commit it.
./gradlew buildAndroid --no-daemon
```

Output: `patches/build/libs/patches-1.0.1.mpp`. No Android SDK or APK is needed to build these bytecode-only patches.

`.forgejo/workflows/release.yml` builds on the existing `collective-android` runner, verifies Morphe discovery and publishes tagged bundles using the ephemeral repository job token. No personal/organization tokens are placed on the shared buildserver. `.github/workflows/release.yml` is an optional build-only workflow for a GitHub mirror; the Forgejo workflow owns releases.

## Acceptance

Applied using official Morphe Desktop 1.18.0, patcher 1.14.1, against an APK from Aptoide:

- Original SHA256: `ff53d3ea24bf9ea86c7c4c301b732b28e27eeaad513f1aae2dcdd778254ab788`.
- APK signature validates using v1/v2. Certificate SHA256: `81939a3cdf1fc500139c7c5511efde39b787e281756f84580c23965633e513e3`; matches mirror metadata, not independently pinned against Play.
- Reminder-only patch: one patched method, premium checks unchanged.
- Combined patch: synthetic event generation disabled; both local premium checks return true.
- `tests/verify_smali.py` compares the disassembled methods against the original. The original fails the reminder assertion, patched outputs pass; all other Utility instruction streams remain unchanged.

Example local verification (keep APKs and decompiled code outside this repository):

```sh
java -jar morphe-desktop.jar patch original.apk -p patches-1.0.1.mpp --bytecode-mode=FULL -o reminder.apk
java -jar morphe-desktop.jar patch original.apk -p patches-1.0.1.mpp -e 'Enable local premium features' --bytecode-mode=FULL -o premium.apk
python3 tests/verify_smali.py original-decoded reminder-decoded
python3 tests/verify_smali.py original-decoded premium-decoded --premium
```

Initial reminder-only APK installed successfully and launched into the real onboarding activity in an isolated Android 15/API35 emulator. Full widget/UI and external account feature acceptance must be recorded separately; do not infer it from bytecode or installation success.

No original APK, decompiled proprietary source, signing keys, or credentials are published here. No affiliation with the app developer or Morphe project.
