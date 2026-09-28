# FacetSensus

**Display-integrated optical sensing for scene geometry and surface appearance.**

Research concept by Philipp Dik · technical publication `2026.09.28`

FacetSensus investigates how calibrated measurements across a display-associated sensing matrix, illumination states and registered panel motion could update a model of the visible environment: surfaces, appearance, motion, visibility and uncertainty. Planar photodiodes, dual-function light-responsive pixels and independently read optical regions are candidate implementations. A staggered three-facet pyramid is one example, not a requirement.

![Complete system](figures/01-system.svg)

Read the **[manuscript](FACETSENSUS.md)** or the **[Russian overview](OVERVIEW_RU.md)**. The scene illustrations are conceptual; no reconstructed environment or fabricated FacetSensus device is presented.

## Proposed implementation

- [Author contribution and scope](docs/AUTHOR_CONTRIBUTION.md): three explicit proposals, known precedents and unresolved claims; the architecture is not limited to pyramids or learning.

- [Measurement sequence](docs/MEASUREMENT_SEQUENCE.md): compare raw mixed responses as the whole panel moves, then jointly estimate surface coordinates, colour where supported by spectral measurements, and uncertainty. The sequence explains how candidate scenes predict the complete observations; an individual reading is not a ready-made spatial point.
- [Proposed reconstruction design](docs/RECONSTRUCTION_DESIGN.md): concrete scene state, physical inversion, optional learning, sequential updates and falsifiable comparisons. The general system remains a design; the separate three-patch demonstrator implements a restricted physical inversion without learning.
- [Existing-screen hardware paths](docs/HARDWARE_PATHS.md): the distinction between available light sensing and the readout needed for spatial reconstruction.

## Included evidence

- [Joint position/appearance demonstrator](studies/scene-reconstruction-2026-09-28/README.md): runnable synthetic inversion of all xyz and three-band reflectances of three patches, static/motion controls, retained failures and a sequential state example. Known count/area/normals; no full textured scene or trained network.

- [Conditional tilt selection](studies/angle-selection-2026-09-28/README.md): 20,160 additional noisy fits with planar and equal-area controls. Working candidate 15° under an explicit rule; observed minimum 20° on 12 new scenes. Results depend on assumed leakage and do not establish a hardware optimum.

- [Small-tilt diagnostic](studies/small-tilt-2026-09-28/README.md): 5–45°, including the 15° candidate; frontal response, direct coupling and the loss of angular contrast, with separate hypothetical acceptance cones.

- [Layout, coupling and noisy depth study](studies/layout-noise-2026-09-27/README.md): 18 configurations and 8,800 restricted noisy fits, with retained failure flags and a correction identifying the untested alternating-square variant.
- [Related work](research/RELATED_WORK.md): existing integrated receiver arrays, surface colour scanning and computational imaging, with source-access limits.
- [Single-patch worked example](example/EXAMPLE.md): 144 synthetic readings jointly fitted under ideal assumptions.
- [Angular layout comparison](angular-comparison/README.md): finite-area geometric calculation at matched density; source, results and independent checks.
- [Candidate pyramid geometry](docs/GEOMETRY_EXAMPLE.md): all bases point upward, neighboring columns shift vertically.
- [Change history](CHANGELOG.md), [citation metadata](CITATION.cff), and the [earlier public text](archive/2026-09-25/README.md).

The included calculations do not establish arbitrary-scene reconstruction, texture fidelity, manufacturing feasibility, overall novelty or a system performance advantage. Detector values cannot simply be projected onto a mesh without accounting for optical mixing, geometry, visibility and illumination.

## Reproduce the limited calculations

Install the numerical dependencies listed in [requirements.txt](requirements.txt), then run from the repository root:

```text
python example/model.py
python example/check_geometry.py
python angular-comparison/compare_layouts.py --subdivisions 8
python angular-comparison/compare_layouts.py --subdivisions 32
python angular-comparison/refine_results.py
python angular-comparison/refine_minima.py
python angular-comparison/independent_ray_check.py
```

The additional noisy study has its own [reproduction commands and pinned dependencies](studies/layout-noise-2026-09-27/README.md).

These scripts reproduce the numerical examples, not a complete scene reconstruction pipeline. Figures and numerical records are included for readers who do not run the code.

Earlier public revisions used **Perceptive Pixel**; the repository URL is retained for continuity. This expanded technical publication is version **2026.09.28**. See the [change record](CHANGELOG.md) and [citation metadata](CITATION.cff); cite the specific Git commit to identify the exact published contents. The new results are not attributed to the earlier public revision.
