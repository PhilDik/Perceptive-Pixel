# Small facet tilts and frontal reception

Computed 28 September 2026. Synthetic optical diagnostic; no new depth fits, learned model or hardware measurements.

The candidate remains the all-upright triangular pyramid with vertically staggered columns. Facet-normal tilt from the panel normal equals side-face tilt from the panel plane. Base side is 9 mm. Tilts of 5°, 10°, 15°, 20°, 30° and 45° are compared.

**The existing broad cosine-response model has no completely blind frontal direction at 45° or at 15°.** A normal is the direction of maximum response, not a single reception ray. At fixed base area the total frontal projected response is identical. At fixed total facet area it instead scales with cos(tilt); these resource normalizations must not be mixed.

| Quantity | 15° | 45° |
|---|---:|---:|
| Height for the illustrated base | 0.696 mm | 2.598 mm |
| Direct coupling, specified checkerboard schedule | 0.389% | 3.868% |
| Angular channel contrast relative to 45° | 0.268 | 1.000 |

The decrease in coupling is conditional on the geometry, opaque bodies and the specified whole-pixel emission/reception schedule. Surface area changes across slopes at fixed base area. Cover propagation, electrical leakage and internal reflection are excluded. Selected coupling refinement from 16 to 64 samples per face changes the 15°/45° results by 0.92%/0.71% relative to the refined value. No overall reconstruction advantage is inferred.

For three equal ideal facets, before cosine clipping or shadowing, normalized RMS channel spread is `tan(alpha)*tan(theta)/sqrt(2)`. Thus the 15° candidate provides about 3.73 times less relative directional contrast than 45°. This is not a depth-error multiplier. Broader signal collection and distinguishable scene parameters are different properties.

Hypothetical hard acceptance cones are included separately. In a co-located far-field angular model, the frontal axis is accepted if cone half-angle beta is at least facet tilt alpha. For beta=20°, 15° accepts that axis and 45° does not. The actual semiconductor/optical-stack response is unknown. A finite 4×4 array also has receiver-position effects: seven axial patch locations at 5–200 mm were evaluated. Broad reception remains nonzero in all these samples; narrow-cone curves illustrate changes with distance. This is not a map of the entire near field, a detection-threshold calculation, or a guarantee of depth observability.

![Small-tilt optical diagnostic](small-tilt.png)

The periodic calculation samples seven polar angles and 24 azimuths with 256 points per facet. Reported angular minima are sampled minima. Finite axial checks use 64 points per facet. Analytic frontal projection and channel-contrast identities were checked; ungated finite responses agree with the earlier kernel. Source hashes and raw outputs are in [results.json](results.json); the detailed [Russian report](REPORT_RU.md) states the normalization and limitations.

Run `python sweep.py` with NumPy, SciPy and Matplotlib, preserving the sibling layout/noise and facet-motion dependency folders. This script does not train a network or reconstruct a scene. **15° is a candidate for evaluation, not an established optimal angle.**
