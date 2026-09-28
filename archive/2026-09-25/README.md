# Perceptive Pixel

## A bidirectional display with independently sensed angular regions

**Status: conceptual research proposal; no fabricated device or measured performance advantage.**

Perceptive Pixel extends the Screen Scanner concept: a purpose-built display surface would emit light and acquire optical measurements, while several independently readable regions within each display pixel would provide different calibrated angular responses. Measurements across the array, illumination states and known display poses would support computational scene estimation.

Read the [conceptual manuscript](PERCEPTIVE_PIXEL.md) for the architecture, measurement model, physical limits, related work and future evaluation criteria.

The proposal includes reversible emitting/sensing elements, active illumination, motion-assisted reconstruction and an optional persistent model of an interacting hand or object. Three facets and alternating triangular arrangements are candidate geometries, not established optima. A normal display is not assumed to gain these capabilities through software alone.

The revised manuscript makes four boundaries explicit:

- Each channel records an angularly weighted optical signal, not a ready-made scene pixel or depth value.
- Active acquisition requires receivers to be sensitive while scene-return light is present. Ordinary display-frame alternation alone does not capture the earlier pulse after it has already returned.
- More channels do not guarantee more independent information or more photons.
- Bidirectional displays, lensless depth sensing and LED/OLED display-camera combinations already have close scientific and patent precedents. Novelty of the proposed implementation has not been established.

The earlier Screen Scanner text and September multi-facet extension are the conceptual lineage of this manuscript. This revision consolidates their scope and corrects their measurement assumptions. The historical repository path `No camera /screen sensitive` is retained as a short companion note; the manuscript is the authoritative description.

Future work is to specify a physical pixel and acquisition schedule, then compare one-, three- and four-region designs at matched optical, electrical and temporal budgets. These are evaluation requirements, not results reported by this repository.
