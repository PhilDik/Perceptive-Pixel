# FacetCensus: Display-Integrated Optical Sensing for Scene Geometry and Surface Appearance

Philipp Dik · research concept · technical publication 2026.09.29

**A census of surfaces — перепись поверхностей.**

## Abstract and scope

FacetCensus proposes a display-associated sensing matrix that records separate optical responses and uses their changes across registered acquisition states to estimate scene geometry and surface appearance. Differently oriented or optically encoded receiving regions provide different mixtures of scene light. Their arrangement and acquisition schedule also control direct light transfer from emitting elements into neighboring receivers. A persistent scene model integrates these measurements over time.

This publication describes the concept, its physical measurement model and a path to an experimental implementation. Supporting numerical studies cover idealized optical coupling and restricted synthetic reconstruction. Their assumptions, data and failure cases are collected in the [numerical appendix](docs/NUMERICAL_STUDIES.md). Hardware development begins with independently accessible elements and measured response functions.

![Conceptual acquisition and scene-state architecture](figures/01-system.svg)

## 1. Directional measurements as the starting point

Each receiving subelement supplies a calibrated light measurement. Keeping these responses separate preserves their differences in position, viewing direction, spectral sensitivity and visibility. The resulting vector contains mixtures of light from multiple surfaces. Reconstruction uses how the complete vector changes with panel pose, illumination and scene motion.

The intended output is a persistent map of observed surfaces: positions, normals, supported appearance, visibility, motion where tracked, and uncertainty. A broad bright region in the raw receiver map is an intermediate measurement pattern. Repeated registered observations constrain which spatial surfaces could have produced it.

The architecture comprises optical encoding, separate electrical readout, illumination scheduling, calibration, pose registration, scene inference and persistent updates. The [author contribution note](docs/AUTHOR_CONTRIBUTION.md) records these proposed elements alongside the established techniques on which they build.

## 2. Pixel geometry and direct optical coupling

The faceted candidate groups separately readable regions on inclined faces. Face orientation shapes the angular response; spacing, staggering and source/receiver timing affect external optical coupling. These are separate design variables. Evaluation therefore records both the useful scene response of each channel and the unwanted source-to-receiver transfer matrix.

The original triangular arrangement uses identically oriented bases, all pointing upward in plan view, and vertically offset neighboring columns. It has three facet-normal azimuths. A second family with 0°/60° cell orientations supplies six azimuths across the matrix. Four-facet cells supply four, or eight with 0°/45° orientations. Counts refer to distinct normal directions at nonzero tilt; the actual angular responses are broad functions. The [direction and component calculation](studies/component-baseline-2026-09-29/README.md) gives the vectors and a fixture-scale example. Mixed-orientation packing is a candidate to be laid out with explicit body clearances.

Vertical staggering changes channel positions, neighbor visibility and optical paths while preserving the orientation of each cell. Its intended role is to reduce unwanted direct illumination of receiving regions while retaining useful, distinguishable scene measurements. For every proposed packing, calculate or measure the full coupling matrix and inspect individual receiving channels as well as totals.

A planar array remains a useful control: spatially separated receivers, coded illumination and registered movement can already provide different measurements. Compare it with faceted channels under the same task, detector area, illumination, acquisition time and readout budget. Summed light collection, number of face normals and reconstruction accuracy are different metrics.

## 3. Hardware paths and acquisition

Three implementations fit the acquisition interface:

| Implementation | Signal provided | First development step |
|---|---|---|
| Reversible light-responsive LED elements | The same junction alternates emission and photocurrent/photovoltage reception | Characterize receive sensitivity, angular response, recovery and switching for the actual device |
| Separate emitters and photodiodes | Independent source drive and receiving currents | Calibrate source/receiver transport and optical coupling |
| Integrated display sensing regions with optical encoding | Raw channels with spatial, angular or spectral selectivity | Establish raw access, timing and the calibrated response operator |

The preferred initial experiment uses available components with independent electrical access. A small discrete-LED fixture tests the same-junction branch; a documented photodiode fixture supplies a separate receiver reference for the geometry. The [hardware assessment](docs/HARDWARE_PATHS.md) and [current component record](studies/component-baseline-2026-09-29/README.md) identify the evidence and interfaces needed for each route.

In the reversible-pixel arrangement, roles are assigned to whole pixels: receiving pixels read their subelements separately while other pixels provide illumination. Reception overlaps the return of the emitted light. Pulse-and-gate operation, if used, requires a separately specified timing and bandwidth budget. Dark and ambient-reference acquisitions characterize offsets and background.

## 4. Calibrated measurement model

For channel i and exposure t, write

```text
y[i,t] = F_i(G_t, rho_t, q_t, e_t; k) + C_i(e_t; k) + D_i(k) + noise[i,t]
```

Here G_t describes geometry and tracked object transforms; rho_t describes appearance under the chosen material model; q_t is registered panel pose; e_t records illumination; and k contains calibration. F integrates the angular and spectral receiver response, source output, distances, projected areas, visibility and exposure timing. Ambient illumination enters scene transport once. C represents direct or internal optical coupling and D the dark/electronic offset.

Calibration measures receiver positions, angular/spectral response, gains, offsets, source output, coupling, recovery, saturation and timing. Photon variance from unwanted light remains after subtraction of its mean. Wavelength-dependent measurements or calibrated coloured illumination provide colour information; facet directions provide angular information.

## 5. Motion, reconstruction and persistent state

Translation changes receiver positions and sight lines. Rotation changes response directions and moves receivers that lie away from the rotation axis. These registered changes give the estimator additional constraints on candidate surfaces. Independently moving objects carry their own time-dependent transforms; jointly tracking them prevents their observations from being averaged into the stationary background. Motion within an exposure is included in the integration model or controlled through shorter exposures.

The algorithm compares predicted and observed channel vectors over time:

1. Record separate channel measurements, illumination, exposure timing and registered panel pose.
2. Predict these measurements from candidate surface geometry, appearance and tracked object motion.
3. Adjust the scene parameters using a noise-aware data term and stated regularization.
4. Check predictions on reserved poses or illumination patterns and retain unresolved alternatives.
5. Merge supported updates into the persistent scene state, including visibility and uncertainty.

Thus movement can sharpen the *estimated map* by separating scene explanations. Its benefit depends on the measured responses and usable relative motion. For example, in a bearing-only model an unknown source strength and range can compensate for one another; useful range estimation requires additional constraints. This motivates varied positions, calibrated illumination and ambiguity tests.

The [measurement sequence](docs/MEASUREMENT_SEQUENCE.md) explains the process in plain terms. The [reconstruction design](docs/RECONSTRUCTION_DESIGN.md) specifies a candidate physical estimator, optional learned regularization and evaluation. A pretrained model may remain fixed while newly registered observations update the scene state.

## 6. Surface appearance and texture

The scene state associates appearance with surfaces through the calibrated light-transport model. Geometry and visibility determine which surfaces contribute to each reading; spectral measurements and recorded illumination constrain colour. Apparent colour under a particular illumination is stored separately from intrinsic reflectance estimated under a material model.

Each surface record retains its observation support and viewing/illumination conditions. Unobserved regions remain unknown; any prior-based completion carries its own label. New observations may refine geometry, appearance, motion or visibility, and may invalidate an earlier estimate.

![Conceptual geometry, appearance and uncertainty state](figures/07-scene-state.svg)

## 7. Existing capabilities and supporting calculations

Bidirectional LEDs and purpose-built light-responsive emitters establish relevant device behavior [1,3,10]. Integrated OLED/photodiode panels establish display-associated optical acquisition [2,4]. Coded and angle-sensitive imaging supplies precedents for recovering spatial information from mixed measurements [5–9]. Interleaved display-sensing disclosures describe related acquisition organizations [11,12]. The [related-work record](research/RELATED_WORK.md) identifies the inspected sources and the scope of each result.

The existing layout calculation addresses the staggering hypothesis directly. Under its stated conditions—whole Lambertian facets at 45°, a finite 4×4 array and checkerboard whole-pixel source/receiver scheduling—triangular pure staggering reduced directly coupled energy from 4.819% to 4.103%, about 15%. The author's pitch and stagger gave 3.868%, about 20% below the aligned control. Other schedules gave different reductions. The [full study](studies/layout-noise-2026-09-27/README.md) specifies the optical paths and normalization.

The [restricted reconstruction example](studies/scene-reconstruction-2026-09-28/README.md) fits positions and three-band reflectances of three small patches with known count, areas and normals. It retains static/motion controls, competing fits and failures. It provides a worked inverse problem for the measurement-to-state sequence. Its results are interpreted within those scene assumptions.

Earlier tilt sweeps and known-lateral-position depth fits remain in the [numerical appendix](docs/NUMERICAL_STUDIES.md). Their angle rankings belong to those particular synthetic tasks. Selection for an actual fixture instead uses its measured channel response, coupling and target reconstruction task. The [component calculation](studies/component-baseline-2026-09-29/README.md) starts with available-part dimensions and electrical access.

## 8. Experimental sequence and evaluation

First characterize one receiving/emitting element and its readout. Then measure angular response and the source-to-receiver coupling matrix on a small array. Compare aligned and staggered placement, and separately compare the direction sets available from one or two cell orientations. Preserve individual channel data for all comparisons.

Next acquire stationary reference objects under known panel motion, followed by tracked object motion. Evaluate geometric error, surface completeness, colour agreement, held-out measurement prediction and uncertainty. Record per-channel leakage, saturation, display duty cycle, bandwidth, energy and computation alongside reconstruction metrics. Match resources explicitly when changing the number of faces or detector area.

This sequence connects the pixel arrangement to its intended benefit: useful directional measurements with manageable optical interference, accumulated into a persistent surface map.

## 9. Publication history

FacetCensus means a census of surfaces. Earlier project names were Perceptive Pixel and FacetSensus. Version 2026.09.29 clarifies directional acquisition, distinguishes motion sources, adds the available-component planning calculation and moves detailed angle-selection results into an appendix. The [change record](CHANGELOG.md), [citation metadata](CITATION.cff) and Git history identify each public version and its contents.


## References

1. Dietz, Yerazunis and Leigh. *Very Low-Cost Sensing and Communication Using Bidirectional LEDs*. 2003. [MERL report](https://www.merl.com/publications/docs/TR2003-35.pdf).
2. Kamada et al. *OLED display incorporating organic photodiodes for fingerprint imaging*. 2019. [DOI 10.1002/jsid.786](https://sid.onlinelibrary.wiley.com/doi/full/10.1002/jsid.786).
3. Bao et al. *A multifunctional display based on photo-responsive perovskite light-emitting diodes*. 2024. [DOI 10.1038/s41928-024-01151-x](https://www.nature.com/articles/s41928-024-01151-x).
4. Kim et al. *Sensor organic light-emitting diode display, combining fingerprint and biomarker capturing*. 2024. [DOI 10.1038/s44172-024-00239-8](https://www.nature.com/articles/s44172-024-00239-8).
5. Hirsch et al. *BiDi Screen: A Thin, Depth-Sensing LCD for 3D Interaction using Light Fields*. 2009. [MIT record](https://dspace.mit.edu/entities/publication/0f809c3e-b842-4784-8302-217860d795f9).
6. Asif et al. *FlatCam: Thin, Lensless Cameras using Coded Aperture and Computation*. [Author preprint](https://arxiv.org/abs/1509.00116).
7. Antipa et al. *DiffuserCam: lensless single-exposure 3D imaging*. 2018. [DOI 10.1364/OPTICA.5.000001](https://doi.org/10.1364/OPTICA.5.000001).
8. Wang, Gill and Molnar. *Light field image sensors based on the Talbot effect*. 2009. [Full article](https://pmc.ncbi.nlm.nih.gov/articles/PMC2892475/).
9. Hua, Zhao and Sankaranarayanan. *Angle Sensitive Pixels for Lensless Imaging on Spherical Sensors*. 2023. [Author preprint](https://arxiv.org/html/2306.15953v1).
10. Oh et al. *Double-heterojunction nanorod light-responsive LEDs for display applications*. 2017. [DOI 10.1126/science.aal2038 / abstract](https://pubmed.ncbi.nlm.nih.gov/28183975/).
11. Ludwig. *LED/OLED array approach to integrated display, lensless-camera, and touch-screen user interface devices and associated processors*. [Application publication US20120006978A1](https://patents.google.com/patent/US20120006978A1/en).
12. *Multi-touch sensing light emitting diode display and method for using the same*. [US7598949B2](https://patents.google.com/patent/US7598949B2/en), 2009.
