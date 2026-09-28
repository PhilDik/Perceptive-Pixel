# FacetSensus: Display-Integrated Optical Sensing for Scene Geometry and Surface Appearance

Philipp Dik · research concept · technical publication 2026.09.28

## Abstract

FacetSensus is a proposed sensing and reconstruction architecture in which a display-associated optical matrix acquires calibrated measurements across its area, illumination states and registered poses. The intended output is a persistent representation of the observable environment: geometry, surface appearance, visibility and uncertainty. Photodetectors integrated beside emitters, dual-function light-responsive pixels, and pixels with several independently readable optical regions are distinct candidate implementations. A three-facet pyramid is one such candidate, not a prerequisite for the architecture. Reconstruction and texture assignment must account for how each receiver mixes scene light; a detector address is not automatically a focused image coordinate. Existing work already demonstrates display-integrated sensing, surface colour scanning and computational imaging. The present work organizes a testable system-level hypothesis and records its limits rather than claiming those broad principles as new. Reproducible calculations address an ideal single-patch example, geometric angular collection, direct optical coupling, restricted noisy two-patch depth recovery, and a subsequent synthetic three-patch example with all positions and three-band reflectances unknown. A proposed physics-based and optionally learned reconstruction baseline is specified separately. No calculation reconstructs a textured environment or validates fabricated hardware.

![Architecture from optical measurements to scene state](figures/01-system.svg)

*Figure 1. The proposed complete system. The scene and texture shown are schematic target representations, not reconstructed results. Pixel geometry is one implementation decision within the acquisition subsystem.*

## 1. Objective and scope

The central objective is to investigate whether a display-associated sensing matrix can accumulate enough calibrated information, including changes caused by panel motion and controlled illumination, to estimate the visible environment and attach supported appearance information to its surfaces. A hand is one possible moving object within this environment, not the definition of the system.

The original Screen Scanner proposal considered reversible emitting/receiving pixels. The multi-region extension preserves separate responses within a pixel rather than reducing them to one intensity before reconstruction. This revision explicitly compares that extension with already demonstrated planar receiver technologies. A panel with separate emitters and photodiodes is an alternative system implementation, not evidence that its individual emitting junctions are reversible.

The proposed state contains surface positions and normals, appearance under specified conditions, object or surface motion when needed, observation history and uncertainty. Its spatial extent is the part of the scene actually constrained by the acquisition trajectory and optical responses. A single panel view does not establish full surrounding or hidden-surface coverage.

The complete architecture includes optical encoding, electrical readout, calibration, a physically valid acquisition schedule, pose registration, scene inference and persistent fusion. A useful question is whether a particular combination improves scene estimation per unit area, photon budget, acquisition time and readout cost. This is an open research question; neither novelty nor an overall performance advantage is established.

The [author contribution note](docs/AUTHOR_CONTRIBUTION.md) distinguishes the proposed acquisition/estimation/state architecture from known ingredients and optional implementations. It records the author's proposals without establishing priority or a patentable scope.

## 2. Sensing matrix: implementation options

The processing interface is a set of measurements indexed by receiver position, independently read optical channel, spectral or illumination condition, time and panel pose. Implementations must supply their actual response functions and uncertainty; these alternatives are not interchangeable without recalibration.

| Candidate implementation | Physical measurement | What must still be established |
|---|---|---|
| Planar display with separate integrated photodiodes | Independently addressed photocurrents, optionally through apertures or other encoding | Useful remote-scene information, optical isolation, spectral response and resource cost |
| Planar dual-function light-responsive pixels | The same purpose-built device is driven as an emitter or read as a detector | Mode recovery, sensitivity, spatial encoding and practical display/readout integration |
| Independently read angular or spectral regions | Several calibrated response functions associated with a receiver location | Their information diversity after noise and nuisance variables are included |
| Three-facet pixel on a staggered carrier | Separate ideal facet responses in the present examples | Manufacturing, coatings, electrical isolation and reconstruction benefit relative to planar alternatives |

Established OLED/photodiode integration and photo-responsive emitters motivate the first two options [1–4]. A bare unencoded flat photodiode array is a relevant baseline, but its irradiance map is not automatically a remote-scene image. A mask, aperture, diffractive structure, angularly selective pixel, illumination pattern or adequate motion can change the measurement operator. Which combination preserves useful distinctions must be measured or modeled.

For the reversible multi-region variant, emission/reception roles are assigned to **whole pixels**. In a receiving pixel, all of its sensing regions receive and are read separately; some facets are not silently reassigned as emitters. Other whole pixels can illuminate the scene during the same interval. In a separate-photodiode panel, the emitters and receivers are physically different devices and its scheduling must be described accordingly.

The [geometric appendix](docs/GEOMETRY_EXAMPLE.md) retains the author's upright triangles and vertically offset columns. That carrier is one worked candidate, not the principal definition of FacetSensus.

### 2.1 Existing-screen feasibility

An existing display is usable as a receiver only if its optical response, electrical readout and raw data access support that role. Output-only display interfaces and framebuffer readback do not provide optical measurements. Some accessible LED matrices already use emitting junctions to estimate ambient light; that capability is not a calibrated image or depth map. Integrated photodiode panels and purpose-built reversible emitters are distinct research precedents, not verified plug-in replacements. The [hardware assessment](docs/HARDWARE_PATHS.md) defines the required interfaces without assuming a software-only conversion of an arbitrary screen.

## 3. Measurement model and calibration

Let p denote a receiver location, k an independently read optical region, c a spectral/acquisition condition, and t an exposure. A schematic intensity model is

\[
\mu_{pkct}=\int_{T_t}\!\int_\lambda\!\int_\Omega
 R_{pkc}(\omega,\lambda;q_t)\,
 L_{\rm scene}(p,\omega,\lambda,\tau;G,\rho,e_t,q_t)\,
 d\omega\,d\lambda\,d\tau + C_{pkct}(e_t)+D_{pkct}.
\]

Here R includes collection area and calibrated optical/spectral transmission; q is panel pose; G is scene geometry; rho denotes a specified material-response model; e describes controlled illumination. Pose transforms receiver and emitter locations and directions into scene coordinates. The displayed expression assumes negligible motion within an exposure; otherwise time-dependent pose q(tau) and illumination remain inside the transport integral. L_scene includes scene radiance under controlled and ambient illumination, with the latter specified or estimated as a nuisance quantity. C is direct/internal emitter-to-receiver coupling, and D is the detector/electronics dark offset. Ambient scene light is therefore not added a second time in D. Actual readings additionally include photon fluctuations, readout noise, drift and possible saturation. A background-subtracted implementation must explicitly model the subtraction and its residual noise.

The response is generally an integral over many scene points and directions. Three broad facet signals are not three focused images or a complete light field. Spectral encoding and angular encoding are different: three faces do not by themselves provide red, green and blue measurements. Optical carrier phase and arbitrary spectral resolution also do not follow from intensity detection. Time-of-flight or modulation-phase measurements would require additional specified hardware and calibration.

Calibration must characterize geometry, relative poses, angular and spectral response, emitter radiance, exposure timing, gains/offsets, coupling and noise. A geometric ray model cannot substitute for a measured semiconductor/cover-stack response. The receiver PSF or general forward operator must be obtained for the relevant depths and operating conditions rather than borrowed from an unrelated optical configuration.

## 4. Illumination, timing and panel motion

Passive acquisition uses continuing external illumination. Active reflection sensing requires receivers to be sensitive while the controlled illumination returns from the scene. Spatial interleaving of emitting and receiving pixels is a valid candidate schedule; known work already demonstrates this principle [3,12]. Roles can be exchanged in later intervals. Illumination coding, readout and pose timestamps must be synchronized.

For a near-normal round trip to a target z metres away in air, the delay is approximately 2z/c: 0.67 ns at 0.1 m and 6.67 ns at 1 m. Turning the whole display off and starting reception in an ordinary later display frame does not retain a prompt reflection that already passed. Fast pulse-and-gate acquisition is a separate hardware option requiring justified pulse duration, recovery, bandwidth and return window. No such device timing capability is claimed here.

Registered translations of the complete panel can provide additional viewpoints and constraints. Rotations can change angular sampling but do not alone guarantee range observability. Pose may come from an independent tracker or a jointly estimated trajectory; the latter introduces further gauge freedoms and uncertainty. Dynamic objects require separating their motion from panel motion. The concept does not assume that measured light automatically yields accurate pose or unrestricted simultaneous localization and mapping.

## 5. From measurements to environment geometry

The [measurement sequence](docs/MEASUREMENT_SEQUENCE.md) explains the intended process in plain terms: the panel first records mixed light responses, then compares how the complete set changes as the whole panel moves through registered poses under recorded illumination. Candidate geometry and appearance predict those responses; their agreement with the observations guides joint updates of surface coordinates, spectrally supported colour and uncertainty. No individual response is assumed to identify a scene point. This general sequence remains a proposed reconstruction method.

For a chosen state x and calibrated acquisition model F, a candidate estimator minimizes a noise-appropriate data residual together with explicit regularization or priors. Unknown appearance, lighting, coupling and pose must be treated as nuisance variables or estimated jointly. The following stages describe a proposed implementation, not an executed reconstruction pipeline:

1. Retain raw channel readings and acquisition metadata; correct calibrated offsets and identify saturation or invalid samples.
2. Register observations into a common frame, including pose uncertainty and an appropriate model of object motion.
3. Fit geometry and appearance against the full measurement operator across receivers, optical channels, illumination states and poses. If a particular encoded sensor first provides reconstructed images, their artifacts and uncertainties must enter subsequent geometry estimation.
4. Fuse compatible surface evidence, preserve unresolved alternatives, and update visibility and confidence. Do not force ambiguous data into a complete surface.
5. Add new measurements when they constrain missing or uncertain regions; retain the distinction between newly observed structure and prior-based completion.

An elementary ambiguity illustrates the need for these conditions. For an unresolved source with readings proportional to alpha times r^-2 times max(0,n_k dot u), distinct normals may help estimate direction u while unknown source strength alpha remains coupled to range r. Scaling r by two and alpha by four leaves those readings unchanged. A textureless surface, unknown reflectance, shadows and specular returns introduce other ambiguities. More channels help only when they add useful independent information at sufficient signal-to-noise ratio.

For an instantiated forward model, Jacobian/singular-value analysis, ambiguous-scene tests and held-out reconstructions can examine observability. Local full rank alone does not prove globally unique recovery. The present package does not establish room-scale capture, metric depth accuracy, arbitrary-scene uniqueness or a working pose-and-map system.

### 5.1 Proposed reconstruction baseline

The [algorithm design](docs/RECONSTRUCTION_DESIGN.md) makes one candidate concrete: a bounded metric scene field and surface appearance, a calibrated light-transport likelihood, alternating geometry/appearance fitting, and optional learned regularization within an unrolled solver. Registered measurements update scene state while pretrained weights remain fixed. Sensor residuals, held-out poses, ambiguity tests and calibrated uncertainty distinguish observed support from completion. The design includes pseudocode and resource-matched ablations; no trained network or full reconstruction implementation is included.

## 6. Surface appearance and texture assignment

Surface texture is a central intended output, together with geometry. Three different quantities must be kept distinct:

| Output | Meaning | Evidence required |
|---|---|---|
| Apparent colour/texture | Surface-associated appearance under recorded lighting and viewing conditions | Spectrally calibrated observations and a defensible correspondence/forward model |
| Reflectance or albedo estimate | An intrinsic parameter within a specified material/lighting model | Enough constraints to separate illumination, geometry and material response |
| Predicted completion | Appearance or geometry for insufficiently observed regions inferred from a prior | An explicit inferred/unknown label, separate from acquired evidence |

A photosensitive display can acquire colour information with suitable spectral channels or a calibrated sequence of coloured illumination; planar near-contact colour scanning has already been demonstrated [2]. That result does not supply a textured 3D environment. Different illumination spectra, detector sensitivity, surface motion and changing ambient light can all alter the observations.

For focused or sufficiently reconstructed views, texture samples can be associated with visible surfaces using calibrated geometry, visibility tests and exposure/colour correction. For broad mixed measurements, raw detector values cannot simply be painted onto a mesh at their detector coordinates. Surface appearance must instead be estimated through the measurement operator, potentially jointly with geometry. A rendered plausible texture is not evidence that it was sensed.

A persistent representation should attach observation support, illumination/view metadata and uncertainty to surface appearance. Conflicting observations may indicate geometry error, motion, specularity, lighting changes or calibration drift; blindly averaging them creates seams or blur. Unobserved back sides remain unknown. View-dependent appearance can be retained when justified, rather than mislabeling it as diffuse albedo. No recovery of arbitrary material properties is assumed.

![Geometry, appearance and unknown regions in a persistent scene](figures/07-scene-state.svg)

*Figure 2. Proposed scene-state update and texture association. Colours illustrate a target representation; they are not output from measured or simulated scene reconstruction.*

## 7. Persistent state and learned models

The environment model can preserve stable surfaces while updating pose, visibility, dynamic objects and uncertain geometry or appearance. A hand-interaction mode is one application: stable shape may be retained while articulation changes. A model must allow previously unseen objects, tracking loss, reinitialization and invalidated geometry.

New registered measurements update the scene state. They do not require online retraining of a pretrained model. Learned priors are optional and must be evaluated on held-out scenes and materials. A geometrically or visually plausible output can be produced even when measurements are insufficient; evaluation must distinguish measured support, uncertainty and completion. Predictions behind occlusions are not fresh observations.

## 8. Closest demonstrated capabilities and the remaining gap

| Prior work | Demonstrated or described capability | Boundary relevant to this proposal |
|---|---|---|
| Bidirectional LEDs [1] and light-responsive nanorod LEDs [10] | Component-level emission and reception | Not a textured environment reconstruction |
| Integrated RGB OLED + OPD panel [2] | Colour scanning of a printed image placed on the display | Separate planar emitter/receiver devices; near-contact 2D scanning |
| Photo-responsive perovskite display [3] | Surface-pattern scanning using adjacent emitting and receiving pixels | Not metric 3D shape or a demonstrated colour environment map |
| Sensor OLED [4] | Integrated optical receiving elements and contact-area sensing | Aperture, coupling and readout trade-offs remain; remote geometry is not demonstrated |
| BiDi Screen [5] | Display-associated light-field acquisition and depth-aware interaction | Coded display and a separate sensor configuration |
| FlatCam [6] / DiffuserCam [7] | Computational imaging with a planar sensor and mask/diffuser | Separate cameras; calibrated encoding and scene assumptions matter |
| Angle-sensitive pixels [8] / OrbCam [9] | Direction-dependent optical measurements | Different architectures and calibration; not proof of this display system |

Earlier technical disclosures also describe combined LED/OLED sensing arrays and interleaved operation [11,12]. These are engineering precedents, not verified performance measurements for FacetSensus. The [related-work record](research/RELATED_WORK.md) distinguishes full primary text, indexed primary sections and access gaps.

The broad ideas of a sensing display, reversible optoelectronic element, computational imaging and reconstruction across observations are established research directions. The proposed work concerns a particular system formulation and the resource-matched evaluation of candidate sensing matrices within it. Failure to find an exact combination in a limited search is not evidence of novelty.

## 9. What the present calculations establish

**Single-patch explanatory example.** A 4 × 4 triangular array, three known translations and two complementary whole-pixel illumination/reception slots produce 144 synthetic regional observations. A noise-free grid fit recovers the stipulated on-grid patch position under the same model used to generate the data. Its location, normal restrictions and unknown common amplitude are explicit in the [worked example](example/EXAMPLE.md). It is a consistency demonstration, not an image, textured object or general-scene reconstruction. It approximates facets as co-located and excludes noise and optical coupling.

**Finite-area angular geometry comparison.** The [separate benchmark](angular-comparison/README.md) traces ideal rays from actual facet areas in periodic opaque arrays. It compares equal-density layouts with the same pyramid dimensions. At 85° from the panel normal, the refined sampled worst-azimuth total response is approximately 16.5% of frontal response for upright pyramids with vertically staggered columns, versus 14.8% for horizontal staggering and 14.1% for a square lattice. Up to 60°, total responses coincide; azimuth-averaged collection is very similar. These conditional results support reduced grazing-angle troughs in the tested geometry, not a universal maximum field of view, minimum refraction or reconstruction advantage.

The two calculations have different assumptions and purposes. The finite-area shadow model does not retroactively validate the co-located patch example. Neither includes a fabricated optical stack or a reconstructed textured environment. Their source, numerical outputs and independent checks are retained for inspection.

**Layout/noise and two-patch study (27 September).** The [new numerical package](studies/layout-noise-2026-09-27/README.md) contains 18 shape/tilt/layout configurations and 8,800 noisy fits, including a separate fixed-signal noise control. In a specified checkerboard schedule, vertical staggering alone reduced direct coupling by about 15% for triangular pyramids; the author's changed pitches plus stagger reduced it by about 20%. Other schedules gave smaller reductions. Lower added background improved depth estimates at fixed useful signal. Full layout comparisons did not establish a universal reconstruction winner. One optimizer nonconvergence is retained and disclosed. Known patch lateral positions, areas and normals restrict the inverse task; poses translate but do not rotate. Real materials, internal coupling, saturation, learned reconstruction and textured mapping remain untested.

**Square-control correction (28 September).** The square pyramids in that study all have the same orientation. The author subsequently specified alternating square orientations with corners directed toward neighboring sides. That alternative has not been calculated. Neither its performance nor a triangular advantage over it is established by the figures or statistics. The original triangular orientation remains unchanged.

These newer calculations add evidence on noise and a restricted inverse problem without changing the limitations of the earlier examples. The preparation dates are not public release dates.

**Small-tilt diagnostic (28 September).** A [six-angle optical comparison](studies/small-tilt-2026-09-28/README.md) adds 5°, 10°, 15° and 20° candidates to 30°/45° controls. Under the broad cosine response, neither 45° nor 15° has a completely blind frontal direction. With equal base area, total frontal projection is unchanged. At 15°, the illustrative height is 0.696 mm and direct checkerboard coupling is about 0.389%, versus 2.598 mm and 3.868% at 45°. Relative angular channel contrast falls to approximately 0.268. Separate hypothetical cone calculations illustrate when true acceptance gaps can occur; actual optical acceptance is unknown. The diagnostic does not evaluate detection thresholds, full near-field coverage or depth accuracy, and does not establish 15° as optimal.

**Conditional angle selection (28 September).** The [angle-selection study](studies/angle-selection-2026-09-28/README.md) adds 20,160 noisy fits, planar split/pooled controls and a second comparison at equal total sensitive area. Initial selection favored 15° under a predeclared smallest-within-10%-of-minimum rule (minimum 20°); three subsequent scenes favored 30°. An additional twelve-scene challenge gave a mean-error minimum at 20° and again selected 15° by that rule in both area normalizations. At equal sensitive area and assumed direct-leakage transmission η=10⁻⁶, mean relative depth error was 5.81% for pooled planar, 4.76% for 15°, 4.57% for 20° and 5.92% for 45°. The 15°–20° difference is unresolved by the descriptive bootstrap intervals. Prioritize 15–25° while retaining 30° as a control; this is a proposed experimental range, not a confidence interval for an optimum. The smallest positive angle in the twelve-scene challenge was 15°, so smaller tilts are not excluded on those scenes.

No physical suppression mechanism achieving η=10⁻⁶ is demonstrated. At η=10⁻⁴ on the preceding three validation scenes, the planar control outperformed the faceted candidates. Equal-area geometries were physically resized, changing gaps and visibility as well as area. Eight boundary fits are retained; all new fits met optimizer convergence criteria. The bounded, known-lateral-position problem does not establish continuous near-field coverage, arbitrary-scene depth, rotation-based mapping or performance of a commercial display. A fixed-budget far-scene local-information diagnostic was severely ill-conditioned.

**Joint xyz/appearance demonstrator (28 September).** A [subsequent runnable example](studies/scene-reconstruction-2026-09-28/README.md) removes the known-lateral-position assumption: all nine coordinates and nine three-band reflectances of three small patches are fitted from raw mixed measurements. Patch count, areas and world normals remain known. Static, translated and translated/rotated panels use five poses, six illumination patterns, equal active area, equal optical energy/integration allocation and 8,640 raw reads. Mechanical motion costs are excluded. The 60 data sets involve 360 optimizer runs, including 20 retained nonconvergences; three chosen best fits do not converge and 30 reach a coordinate or reflectance boundary.

On the near/oblique scene, median xyz RMSE over three noise realizations changes from 3.45 mm (15° static) to 1.07 mm (15° combined motion), with reflectance RMSE 0.080 to 0.014. The flat combined control also recovers that scene (1.39 mm), and outperforms 15° on another scene (2.61 vs 6.93 mm). Close equal-colour patches fail across all tested configurations, sometimes despite sub-percent held-out signal errors. A separate 1/3/5-pose refit demonstrates accumulated sparse state, with increasing energy/data; it does not prove a matched-budget fusion advantage. Noiseless matched-model diagnostics recover selected scenes, but are consistency checks, not independent validation. The working 15° choice from the prior bounded depth task is not established as optimal for this larger inverse problem.

The demonstrator uses no learned prior and reconstructs no extended texture, unknown normals, new surfaces or dynamic objects. Strong leakage suppression remains hypothetical. These results add a concrete computational example and expose ambiguity rather than establishing general scene reconstruction.

## 10. Evaluation needed for the system-level hypothesis

The next substantive comparison must hold scene, panel footprint, actual detected photons, emitted energy, trajectory, acquisition time and readout budget accountable. Relevant baselines include planar integrated photodiodes with suitable encoding, dual-function planar pixels, single-region pixels, multi-region outputs summed before reconstruction and the explicit facet candidate. Existing sensor demonstrations are technical starting points, not off-the-shelf substitutes assumed to satisfy the entire proposal.

First evaluate an independently specified scene model with geometric detail, colour variation, unfamiliar materials, shadows, occlusions and motion. Include pose, calibration and spectral mismatch. Test ambiguous scene pairs and failure cases before concluding that a richer output implies richer information.

Report geometry error and completeness on independently measured surfaces, pose drift, false reconstructed structure, uncertainty calibration, and sensitivity to unfamiliar scenes. For appearance, report colour error under specified illumination, surface registration, texture resolution, seams, consistency on held-out views and errors caused by lighting/material mismatch. Do not count inferred hidden texture as acquired coverage. Measure crosstalk, saturation, display quality, sensing duty cycle, bandwidth, energy and computational cost.

Adding K readout regions does not multiply photons collected by a fixed effective aperture. At equal sampling rate and precision it increases raw data volume approximately with K; at fixed bandwidth, other dimensions must trade off. More surface area, a brighter illuminator or a longer scan can create an apparent advantage that is not attributable to better encoding. Subtracting mean crosstalk does not eliminate its photon noise.

Only retain a claimed benefit when it survives these matched-resource and independent-scene comparisons. The present concept states no demonstrated range, scene-scale resolution, texture fidelity, frame rate or power target.

## 11. Publication status and attribution

This is an open technical publication, with reproducible limited calculations and an explicit prior-work review. It documents a proposed mechanism and evaluation criteria without asserting that the complete idea is unprecedented.

The repository previously used the title Perceptive Pixel. FacetSensus is the current project designation; neither that name nor its etymology restricts the architecture to facets. The [change record](CHANGELOG.md) distinguishes the earlier public revision from this expanded publication, version 2026.09.28. [Citation metadata](CITATION.cff) identifies the author, version and publication date. Cite the specific Git commit for the exact contents; the newly added details are not attributed to the earlier public revision.

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
