# Restoration roadmap
## Verified
- Archive research previously identified classic Mac resource forks with 68K CODE/CREL, PICT and snd resources.
- This repository includes only newly authored prototype source and CI, not proprietary game content.
- Portable C++ demo map and movement implemented; not a faithful reconstruction.
## Next
1. Confirm Android CI builds and install/test APK on physical Android hardware.
2. Decode original PICT sprites locally with provenance tracking and explicit redistribution approval.
3. Disassemble and annotate original 68K segments; distinguish hypotheses from verified behavior.
4. Reconstruct movement/combat/inventory/maps against observed original gameplay.
5. Implement an explicit versioned save-file format and cross-platform graphics/input layer.
6. Expose a stable **internal C ABI** for engine integration; consider an HTTP API only if there is an actual need.
7. Add Windows/macOS host apps, regression recordings, and release packaging.
## API design decision
The Android app uses JNI for now; a network API is not required for offline play. No production API exists today.
