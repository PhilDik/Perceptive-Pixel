# Related work and source-access record

Review date: 26 September 2026. Scope: existing display/photoelement matrices, optical encoding, scene imaging, geometry and surface appearance. This is a limited engineering literature comparison, not an exhaustive novelty determination. The table numbers match the manuscript references.

| Ref. | Primary source | Inspected evidence | Transfer boundary |
|---|---|---|---|
| 1 | [Dietz et al., 2003, bidirectional LEDs](https://www.merl.com/publications/docs/TR2003-35.pdf) | Author/laboratory report | Component sensing and communication do not supply a scene-imaging operator |
| 2 | [Kamada et al., 2019, OLED + OPD](https://sid.onlinelibrary.wiley.com/doi/full/10.1002/jsid.786) | Indexed primary sections, prototype table and Figure 15; direct page opening failed | Demonstrated colour scan uses printed paper on the panel, not a remote 3D surface |
| 3 | [Bao et al., 2024, photo-responsive perovskite LEDs](https://www.nature.com/articles/s41928-024-01151-x) | Full primary HTML, Figure 4 and Methods; supplements not independently examined | Adjacent emitting/receiving pixels scan printed surface patterns; general 3D colour capture remains unshown |
| 4 | [Kim et al., 2024, Sensor OLED](https://www.nature.com/articles/s44172-024-00239-8) | Full primary HTML, device/optics/coupling sections; supplements not independently examined | Integrated OPD reception and contact-area sensing do not establish free-space geometry |
| 5 | [Hirsch et al., 2009, BiDi Screen](https://dspace.mit.edu/entities/publication/0f809c3e-b842-4784-8302-217860d795f9) | Institutional record and indexed primary manuscript sections; no complete PDF readback | Prototype uses cameras behind a coded LCD; not a fabricated monolithic detector/display panel |
| 6 | [Asif et al., FlatCam, IEEE TCI 2017](https://imagesci.ece.cmu.edu/files/paper/2017/flatcam_tci17.pdf) | Complete primary author PDF; DOI 10.1109/TCI.2016.2593662; preprint 2015 | Colour 2D reconstruction on an ordinary matrix plus mask; separate camera, not textured 3D mapping |
| 7 | [Antipa et al., DiffuserCam, Optica 2018](https://arxiv.org/html/1710.02134v1) | Full author preprint model and physical 3D experiments; DOI 10.1364/OPTICA.5.000001 | Depth-dependent PSFs and regularization; scene-dependent resolution and omitted partial occlusion |
| 8 | [Wang et al., 2009, Talbot-effect pixels](https://pmc.ncbi.nlm.nih.gov/articles/PMC2892475/) | Indexed primary results/discussion; direct page had access restrictions | Optical angular encoding is an established mechanism; not every ASP setup is lensless |
| 9 | [Hua et al., OrbCam, 2023](https://arxiv.org/html/2306.15953v1) | Full author HTML, model and physical emulator | Rotating planar sensor emulates directional spherical sampling of a distant scene; not near-field metric depth |
| 10 | [Oh et al., 2017, nanorod light-responsive LEDs](https://pubmed.ncbi.nlm.nih.gov/28183975/) | Primary abstract plus indexed author PDF/Figure 4; direct PDF failed | Dual-function device precedent, not full environment reconstruction |
| 11 | [LED/OLED array disclosure, 2012](https://patents.google.com/patent/US20120006978A1/en) | Technical disclosure reviewed in the earlier local audit | Described system organization is not experimental validation |
| 12 | [Interleaved LED display sensing, 2009](https://patents.google.com/patent/US7598949B2/en) | Technical disclosure reviewed in the earlier local audit | Whole-pixel interleaving is an existing idea, not a new contribution here |

## Why the planar-matrix research matters

Colour scanning by the 2019 OLED/OPD panel is an especially direct precedent for appearance acquisition: sequential coloured illumination allows a broadband receiver to acquire separate colour-conditioned readings. It does not remove the geometric and optical mixing problem for remote surfaces. The 2024 perovskite work supports purpose-built flat pixels with both modes, whereas the Sensor OLED architecture uses physically separate emitting and receiving devices. Both are relevant implementation paths and must remain distinct.

FlatCam reconstructs colour images from mixtures measured through a mask on a planar sensor. DiffuserCam demonstrates 3D imaging with a diffuser and depth-dependent response, including extended objects. Its reconstructed voxel count is not a count of independently resolved measurements; sparsity/regularization, calibration and occlusion limits matter. Neither demonstration should be described as an emitting display already constructing a complete textured environment.

OrbCam is useful for combining direction-dependent readings under known reorientation. Rotation and far-field imaging do not establish metric distance to nearby surfaces. BiDi is a direct display-related precedent but its physical assembly must not be conflated with a thin integrated photodiode panel.

## Candidate-facet context

The supporting pyramid calculation also relates to fabricated [micro-pyramid LED arrays, 2021](https://www.mdpi.com/2073-4352/11/6/686), [pyramidal sun sensors, 2019](https://www.mdpi.com/1424-8220/19/6/1424) and [angle-diversity receiver design, 2013](https://link.springer.com/article/10.1186/1687-1499-2013-221). These sources establish relevant component geometry or directional sensing, not the optimum packing or reconstruction performance of this proposed display. The micro-LED article was available through indexed primary sections; the latter two through primary HTML. No previously published figure is reproduced in this package.

## Interpretation and remaining gap

The concept should therefore distinguish three layers: a realizable photoelement/readout, an optical/acquisition operator that encodes scene differences, and an estimator that reconstructs supported geometry and appearance from those readings. Better reception angle or a larger number of detector samples does not by itself establish recoverable texture detail.

The relevant uncompleted task is a matched-resource scene comparison with stated illumination, pose uncertainty, materials and missing surfaces. Observed colour under a particular light is not automatically intrinsic albedo; arbitrary reflectance or hidden texture recovery needs additional constraints. The present literature selection does not demonstrate the complete proposed moving display-based reconstruction system, and does not establish that no such complete analogue exists.

## Addendum, 28 September: learning and usable hardware

[FlatNet3D (2022)](https://opg.optica.org/josaa/abstract.cfm?uri=josaa-39-10-1903) is a primary precedent for learned depth/intensity recovery from a coded lensless capture. The inspected abstract and table report a simulated-test depth RMSE of 1.42 cm versus 5.26 cm for ADMM plus Graphcut; that table is not measured far-scene performance. Full subscription text was not inspected in this refresh. [Modular learned reconstruction (2025)](https://arxiv.org/abs/2502.01102) studies combined physical and neural processing and transfer across masks; the author's abstract was inspected. Neither result validates this proposed panel.

The [official LED-matrix hardware description](https://tech.microbit.org/hardware/) and [documented light-level interface](https://microbit-micropython.readthedocs.io/en/latest/display.html) confirm that an already-built emitting matrix can provide ambient-light sensing. The documented scalar output must not be represented as independently calibrated imaging channels.

The refresh of the 2024 integrated organic-photodiode paper found electrical leakage through shared layers and optical leakage reduced by alternate-column sensing at a cost of doubled scan time. The 2024 perovskite paper demonstrates reception by the emitting devices themselves, with device-area-dependent speed and prototype durability limitations. Their primary indexed experimental sections were accessible; direct publisher openings sometimes failed. This refresh does not imply new full-text access or verified retail availability.

The full author texts of OrbCam and DiffuserCam were inspected again. OrbCam's rotating masked sensor produces angular imagery; its mask incurs light loss and spacing constraints. DiffuserCam's specific prototype loses axial resolution beyond its approximately 2.3 m hyperfocal plane while remaining capable of 2D imaging. These are instrument-specific boundaries, not universal limits or evidence of a FacetCensus advantage.

Subsequent source check on the same date: the full main HTML of the [2024 reversible perovskite display paper](https://www.nature.com/articles/s41928-024-01151-x), including its display demonstration methods, was accessible. Supplementary videos and the supplementary PDF were not checked in this refresh. The [hardware examples table](../docs/HARDWARE_PATHS.md) records concrete readout capabilities and unresolved availability; it does not assume that a laboratory demonstration is a retail sensing panel.
