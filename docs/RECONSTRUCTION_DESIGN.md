# Proposed reconstruction and learning baseline

Prepared 28 September 2026. **Design specification, not an implemented or trained FacetCensus reconstruction system.** The [main manuscript](../FACETCENSUS.md) defines the optical architecture. The [numerical study](../studies/layout-noise-2026-09-27/README.md) implements a much smaller two-patch inverse problem without learning or rotation.

## Implemented restricted example

A subsequent [synthetic demonstrator](../studies/scene-reconstruction-2026-09-28/README.md) implements joint xyz/three-band-reflectance fitting for three known-area, known-normal patches and refits their persistent sparse state as observations accumulate. It includes translations/rotations, held-out poses, planar controls and retained failures. It does not implement the general surface field, trained regularizer, unknown-surface discovery or calibrated uncertainty described below. The full baseline remains a design specification.

## 1. Inputs and calibration

Each observation records receiver position, optical region, spectral condition, exposure interval, whole-pixel emitter/receiver assignment, illumination pattern, panel pose and its uncertainty. Regions of one receiving pixel are read independently. An emitting pixel is not assumed to receive its own already-departed reflection in a later ordinary display frame. Passive observations and concurrent spatially interleaved illumination/reception are distinct acquisition modes.

Calibrate receiver angular/spectral response, source output, channel gains, offsets, coupling, saturation, timing and the relative locations of all regions. Calibration must contain enough known positions and depths to test the proposed spatial operator. A uniform-light gain calibration alone is insufficient. Keep calibration uncertainty; do not fit an unrestricted offset per observation, which could absorb scene information. Pose is an externally supplied, time-aligned input in this first baseline. An inertial sensor alone is not assumed to provide drift-free metric translation.

The raw data are weighted mixtures of light from the scene, not conventional RGB images. Consequently, feeding a receiver grid into an ordinary image-depth network without modeling the acquisition is not the proposed baseline.

## 2. A specific first scene representation

For an initial bounded, static workspace, use a coarse-to-fine signed-distance field on a metric voxel grid, with a surface mesh extracted for light transport. Store three-band diffuse reflectance only when three independent calibrated spectral conditions exist; otherwise use one band. Associate cells or surface elements with observation count, visibility history, residual diagnostics and an uncertainty estimate. An unobserved cell stays unknown, rather than being assigned a confidently empty or solid state.

The first material model is opaque Lambertian reflection with direct illumination and single surface scattering. It excludes transparency and unresolved specular transport. Such observations must be treated as model mismatch, not silently used to invent geometry. Refine spatial resolution only when held-out measurements distinguish the added parameters. A fine grid is not evidence of fine measured resolution.

Use a bounded ensemble of initial scene hypotheses when initialization is ambiguous. One optimizer and one plausible mesh cannot demonstrate unique recovery. The persistent state stores scene estimates, not an asserted record of everything surrounding the device.

## 3. Forward model and non-learned estimator

For scene state x, pose q, acquisition e and calibrated instrument parameters k, predict a channel mean as

```text
mu = F_scene(x, q, e, k) + C_direct(e, k) + D_dark(k)
```

The scene renderer integrates source and receiver responses over their finite regions, including spectral overlap, distances, projected areas and visibility. Environmental illumination enters scene transport once. Direct emitter-to-receiver coupling is a separate path. At near-field ranges, replacing an extended facet by its center requires a convergence check.

Optimize a Poisson-plus-read-noise likelihood, or an explicitly justified approximation, with geometry and appearance regularization. If the mean coupling is subtracted, its photon variance remains. Saturated measurements need a censored model or exclusion; they are not ordinary low-precision samples. Pose and calibration refinement, if enabled later, must remain constrained by their measurements and priors so that arbitrary drift cannot explain away scene errors.

Alternate appearance updates with geometry updates, re-rendering visibility when the surface changes. Use coarse-to-fine initialization and compare the residuals of competing hypotheses. Regularization strength and stopping rules are selected on validation scenes, not final test scenes. Report retained ambiguity and sensitivity to material/illumination assumptions.

## 4. Optional learning, with an explicit role

A concrete candidate is an unrolled inverse solver. Each stage takes a physical data-gradient step followed by a learned spatial regularizer. Inputs to the learned module may include the current geometry/appearance grids, measurement-gradient backprojections, coverage and noise maps. It proposes a bounded state correction, then the forward model checks the proposal against measured data. This is a proposed implementation choice, not a claim that unrolling or learned regularization is new.

Train the regularizer using independently generated scenes and calibrated response families. Vary geometry, reflectance, illumination, noise, coupling, pose error and detector response within declared ranges. Include scenes that violate the baseline material model to test failure detection. Split by scene and acquisition configuration, not by adjacent exposures from the same scene. Include supervised geometry/appearance losses where ground truth exists and a sensor-space likelihood term. Synthetic training alone does not demonstrate transfer to fabricated hardware.

At inference, trained weights remain fixed. New measurements update the scene state and its support. A recurrent memory, if used, must not overrule contradictory observations merely because an old map is visually plausible. Uncertainty needs empirical calibration on held-out scenes; a neural confidence output or a local inverse Hessian is not automatically reliable under global ambiguity.

## 5. Sequential update and texture

Register each new acquisition before updating the map. Fit surface appearance through the calibrated transport model, rather than painting detector values onto the nearest mesh vertex. The diffuse baseline separates reflectance from controlled light only under its stated assumptions. More general view-dependent appearance is a different representation and must not be mislabeled as intrinsic material colour.

Start with static scenes. Later extensions can keep separate rigid-object transforms or deformation states. Inconsistent measurements trigger a dynamics/mismatch flag or a new hypothesis instead of unconditional averaging. Unseen surfaces remain unknown. Optional visual completion is stored separately from measurement-supported geometry and excluded from measured-coverage scores.

```text
calibrate instrument; freeze trained weights, if any
initialize bounded scene hypotheses with unknown coverage
for each synchronized acquisition block:
    read raw channels, illumination, poses and validity flags
    retain a predetermined subset for independent prediction checks
    for each scene hypothesis:
        predict scene transport, direct coupling and noise
        alternate geometry and appearance data-fitting steps
        optionally apply a learned regularizer; check sensor residuals
        update visibility, support and uncertainty diagnostics
    retain unresolved alternatives; flag dynamics or model mismatch
    evaluate predictions on held-out poses/illumination states
    output supported surfaces, appearance and unknown regions
```

This pseudocode specifies an intended experiment. It is not runnable software included in the package.

## 6. Rotation, distance and optional measurement selection

Changing orientation changes angular sampling and active illumination. For an extended panel, receivers away from the rotation axis also translate: their displacement between orientations is `2 r sin(a/2)`. Thus pure rotation of one central bearing sensor is not equivalent to rotating the complete panel. Nevertheless, the effective parallax decreases roughly with baseline divided by scene distance. Additional panel translation may provide a larger useful baseline. Dense angular sampling of a distant scene does not automatically determine its distance.

A later optional controller could choose the next feasible illumination pattern or suggest a pose that best distinguishes retained hypotheses at equal energy/time cost. Compare that controller with a fixed schedule. Active measurement selection is itself an established strategy; the contribution would have to be the specific operator, decision rule and demonstrated benefit. Do not assume the display can mechanically move itself.

## 7. Evaluation that can falsify the proposal

| Comparison | Question |
|---|---|
| Static / rotation / translation / combined motion | Which part of acquisition provides depth information? |
| Physical solver / learned regularizer / prior-only estimate | How much accuracy comes from measurements versus learned expectations? |
| Single acquisition / sequential state, matched total budget | Does fusion use observations more effectively? |
| Independent regions / their sum, matched aperture and readout | Do angular channels supply useful independent constraints? |
| Planar encoded receiver / facet candidate | Does the candidate outperform suitable established encoding? |
| Exact / perturbed calibration and poses | Does the result survive instrument mismatch? |

Use unfamiliar geometry, materials and lighting; ground-truth metric surfaces; held-out poses; and deliberately ambiguous scene pairs. Report depth/surface error, completeness, texture error under specified light, false surfaces, coverage and uncertainty calibration. Keep emitted energy, exposure time, aperture and readout resources accountable. When distance increases, do not restore a constant detected photon count by silently increasing illumination. No range, frame rate or neural performance is claimed for this unimplemented baseline.

## Sources and status

Known computational precedents include [FlatNet3D](https://opg.optica.org/josaa/abstract.cfm?uri=josaa-39-10-1903), which combines physical encoding with learned depth/intensity recovery, and [modular learned reconstruction](https://arxiv.org/abs/2502.01102), which studies physics and learning across lensless masks. Their results belong to their own instruments and datasets. The [related-work record](../research/RELATED_WORK.md) records access limitations. This design makes the proposed pipeline concrete enough to evaluate without representing it as completed research.
