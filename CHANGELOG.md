# Change record

## 2026.09.28 — expanded technical publication

- Added an explicit author-contribution note separating the proposed architecture, established ingredients and optional geometries/learning.
- Implemented a restricted three-patch joint xyz/appearance demonstrator with static/motion controls, 60 data sets and 360 multi-start optimizations (20 nonconvergences, three selected nonconvergences and 30 selected boundary fits retained). Added raw examples, sequential state, held-out prediction checks and noiseless diagnostics. General textured-scene reconstruction remains unimplemented.

- Added conditional tilt selection, matched planar/equal-area controls, 20,160 additional noisy fits, eight retained boundary fits, and scene/noise uncertainty analysis. Kept the changed validation ranking and the leakage scenario in which the planar control wins.
- Documented the raw mixed-response → registered panel motion → geometry/appearance/uncertainty sequence and checked four existing hardware classes with explicit readout and availability limits.

- Added the six-angle small-tilt diagnostic, including 15°, and separated frontal response, hypothetical acceptance gaps, direct coupling and angular contrast.

- Added an explicit proposed physical/learned reconstruction baseline and existing-display hardware feasibility requirements.
- Included the 18-configuration layout/coupling study, restricted depth recovery, fixed-signal noise control, raw data, scripts and numerical checks (8,800 noisy fits; one retained optimizer nonconvergence).
- Clarified that the tested square control uses identical orientations and does not represent the subsequently specified alternating-square proposal.
- Preserved original public archives and the earlier limited examples; no trained network, general textured-scene reconstruction, demonstrated useful distant range or hardware prototype is claimed.


## 2026.09.26-draft — unpublished intermediate draft, included in 2026.09.28

- Made environment geometry, surface appearance/texture and persistent scene updates the primary scope.
- Distinguished existing planar integrated photodiodes, dual-function emitters and multi-region receiving pixels.
- Added primary research on colour surface scanning, photo-responsive display scanning, coded planar imaging and volumetric computational imaging.
- Preserved whole-pixel roles and the exact author-specified vertically staggered, all-upright pyramid candidate in a supporting appendix.
- Included the limited single-patch calculation and finite-area angular benchmark with their separate assumptions and checks.
- Added conceptual system and scene-state figures, citation metadata and archived public text. No textured-scene reconstruction is claimed.

## 2026-09-25 — earlier public conceptual revision

The existing public text was verified at commit [c44b2e778741dea6f2f2821cf948a0eaca5a7d41](https://github.com/PhilDik/Perceptive-Pixel/commit/c44b2e778741dea6f2f2821cf948a0eaca5a7d41). It used the title Perceptive Pixel. A byte-preserving copy of its three files is retained under archive/2026-09-25, using a filesystem-safe alias for the historical path with a trailing space.

The expanded publication does not imply that its newly added details were present in the older public commit.
