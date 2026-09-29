# FacetCensus: the author's proposed contribution

Philipp Dik · conceptual formulation · prepared 28 September 2026

This note identifies the proposals made in the [manuscript](../FACETCENSUS.md) and [reconstruction design](RECONSTRUCTION_DESIGN.md). Attribution here records what the author proposes in this project; it does not establish priority, novelty, successful implementation or measured advantage.

**Working definition.** FacetCensus is a proposed architecture that combines raw, spatially mixed optical measurements from a display-associated matrix across registered panel motion and recorded illumination conditions, with the aim of estimating surface coordinates and appearance and updating a persistent, evidence-qualified scene state.

**По-русски.** FacetCensus — предлагаемая архитектура, в которой матрица при дисплее регистрирует смешанные световые отклики. Их изменения при известном движении всей панели и записанных условиях освещения используются для совместной оценки координат поверхностей и их внешнего вида, а новые наблюдения уточняют сохраняемую модель сцены. Отдельный световой отклик не считается готовой точкой изображения или глубины; неопределённые и ненаблюдавшиеся участки остаются обозначенными как таковые.

## Three concrete proposals

1. **Preserve measurements across registered acquisition states.** Retain raw receiver responses together with receiver/channel identity, spectral condition, illumination, time and whole-panel pose. Fit them through the calibrated operator of the selected hardware, including coupling and noise. The proposal is a common acquisition-to-reconstruction interface for candidate sensing matrices, rather than a requirement for one pixel shape. Whether a chosen matrix and trajectory provide sufficient independent information remains a testable question.

2. **Estimate surface coordinates and appearance from the same mixed observations.** Compare candidate geometry and surface appearance against predicted optical responses across panel positions and acquisition conditions. Associate appearance with inferred surfaces through that transport model; do not assign detector values directly to mesh vertices. Colour requires sufficient calibrated spectral information. Separating intrinsic reflectance from lighting requires additional declared assumptions. The intended output is a supported scene estimate, with competing solutions retained when observations cannot distinguish them.

3. **Accumulate a persistent scene state with explicit observation support.** New registered measurements revise geometry, appearance, visibility and uncertainty instead of requiring a complete independent reconstruction at every exposure. Store which observations support each estimate, permit contradictions and reinitialization, and keep prior-based completion separate from measured support. If a pretrained regularizer is used, its weights remain fixed during these updates: the evolving object is the scene state. The proposal must be evaluated against independent reconstructions at the same total measurement budget.

## Directional acquisition emphasis, 29 September

The author emphasizes preserving distinct receiving-region responses and reducing direct illumination of neighboring subelements through geometry and scheduling. Directional diversity and optical coupling are separate quantities. Both original and mixed-orientation triangular candidates remain available; the first implementation follows independently accessible components. Registered panel motion and tracked object motion enter different transforms in the scene operator, with new measurements refining scene state. Earlier synthetic angle rankings remain study-specific evidence.

## Required architecture and optional implementations

The required architecture consists of accessible optical measurements, a calibrated measurement model, recorded acquisition states and registered panel poses, joint scene estimation, and persistent updates with support and uncertainty. Its intended scope includes geometry and surface appearance; an implementation with inadequate spectral information must restrict its appearance output accordingly.

Three-facet pyramids, a particular facet angle or carrier layout, reversible emitting/receiving junctions, and learned reconstruction are optional. Separate photodiodes beside emitters, planar dual-function pixels and angularly encoded receivers are candidate implementations. The formulation is independent of one hardware geometry; each implementation still needs its own physical calibration, valid timing and raw readout. It does not imply that arbitrary existing screens can sense a scene through software alone. The first reconstruction baseline uses externally registered poses and static scenes; autonomous pose recovery and dynamic mapping are further extensions.

## Existing capabilities, proposed combination and unresolved evidence

| What is already known | Proposed combination in FacetCensus | What remains unverified |
|---|---|---|
| [Integrated OLED/photodiode panels](https://sid.onlinelibrary.wiley.com/doi/full/10.1002/jsid.786) demonstrate display-integrated photodetection; [photo-responsive displays](https://www.nature.com/articles/s41928-024-01151-x) demonstrate emitting/receiving operation and surface-pattern scanning. | Use calibrated display-associated measurements across registered poses as inputs to a persistent geometry-and-appearance estimate. | Whether a practical panel supplies sufficient remote-scene information, sensitivity, isolation and readout access. |
| [BiDi Screen](https://dspace.mit.edu/entities/publication/0f809c3e-b842-4784-8302-217860d795f9) demonstrates display-associated angular acquisition and depth-aware interaction; [DiffuserCam](https://doi.org/10.1364/OPTICA.5.000001) demonstrates computational 3D imaging with another optical operator. | Fit geometry and surface appearance using the complete calibrated operator and registered acquisition sequence of the selected matrix. | General-scene identifiability, texture fidelity, useful working distance and robustness to calibration, lighting and pose errors. |
| [Angle-sensitive pixels](https://pmc.ncbi.nlm.nih.gov/articles/PMC2892475/) encode directional information in optical measurements. | Preserve independently read regions as one optional source of diversity alongside panel aperture, illumination and motion. | Whether facets improve reconstruction relative to suitable planar encoding or pooled channels at matched resources. |
| [FlatNet3D](https://opg.optica.org/josaa/abstract.cfm?uri=josaa-39-10-1903) combines physical encoding with learned depth/intensity recovery. | Optionally regularize the physical inverse problem while new observations update scene state and trained weights remain fixed. | Accuracy beyond a physical solver, transfer to actual hardware, calibrated uncertainty and the amount of output supported by measurements rather than priors. |

These links reuse the existing primary-source record; their demonstrated results belong to their respective instruments. This table is not an exhaustive novelty assessment. The [related-work record](../research/RELATED_WORK.md) retains source-access limitations.

## What would support the proposed contribution

Evaluate the combined architecture against meaningful alternatives: independent acquisitions versus persistent fusion; independent regions versus their sum; suitable planar encoding versus facets; and a physical solver versus an optional learned regularizer. Account for aperture, actual photon collection, emitted energy, trajectory, exposure time and readout cost. Use independent scenes and held-out acquisition states, including ambiguous cases and instrument mismatch. Report geometry, appearance, false structure and uncertainty together.

Existing limited calculations support only their stated restricted questions. This note adds no reconstruction result or claim of full-system feasibility. The proposed contribution remains the specific, falsifiable organization of acquisition, joint estimation and persistent state described above.

## Subsequent restricted implementation

The [joint position/appearance demonstrator](../studies/scene-reconstruction-2026-09-28/README.md) supplies one runnable synthetic instance: three patches with known count, area and normals; unknown xyz/reflectances; and a retained sparse state updated by refitting accumulated measurements. It reports successes, failures and ambiguous explanations. This does not implement the full proposed architecture or establish its novelty or general performance.
