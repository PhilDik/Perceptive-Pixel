# Reproducible example: one patch, one moving array

**Status:** a small explanatory calculation added for this revision. Every dimension,
normal and optical parameter below is an analyst-selected assumption. This is not a
fabricated pixel, measurement, validated device simulation or demonstration of sensing performance.

## Defined scene and schedule

A 4 × 4 addressed array uses vertically staggered columns of upright pyramids.
Before subtracting the centroid, c(r,j) = (5√3 j, 10[r + (j mod 2)/2], 0) mm,
for row r and column j from 0 to 3. Consecutive columns are 8.660254 mm apart;
odd columns shift upward by 5 mm. Pitch along each column is 10 mm. All base
triangles point toward +y; none are reversed. The half-pitch offset is an illustrative
choice implementing the author's vertical-stagger requirement, not an optimized value.
The complete array translates to x = −20, 0, +20 mm with no
rotation. One static 1 mm² Lambertian patch is centered at (20, 0, 150) mm; its known
normal is (0, 0, −1), and y is fixed at 0 in reconstruction.

At each pose, slot A uses even-parity whole pixels as emitters and the other eight
whole pixels as receivers. Slot B swaps their roles. Each receiving pixel reads all
three facets separately and simultaneously during illumination. This schedule assumes
independently addressable purpose-built pixels; it does not establish a switchable
semiconductor implementation. No prompt reflection is collected after a frame ends.

Each emitting pixel is represented by an assumed equivalent +z Lambertian source.
Emission from individual tilted facets and its absolute throughput are not modeled.
All pyramids share one orientation. Each has a 9 mm equilateral base and an apex
1.5 mm above its centroid; its three congruent side faces are isosceles triangles.
Each ideal receiving face has area 13.5 mm². Its outward normal is tilted 30° from +z
at azimuth 30°, 150° or 270°. The base vertices have azimuths 90°, 210°, 330°.
The physical geometry is shared by the figures and this calculation. The radiometric
model approximates all three facets as co-located at the base center (z = 0).
It assumes sufficient optical separation that direct light does
not enter the reported signal. One arbitrary total emission-power unit is divided
equally among eight emitters. All channel gains are fixed and calibrated to unity.
These dimensions illustrate geometry; 10 mm pitch is not a display-density claim.

In the interior, six nearest centers have azimuths 30°, 90°, 150°, 210°, 270°, 330°.
Vertex directions (90°, 210°, 330°) point toward three of them; horizontal normal
projections (30°, 150°, 270°) point toward the other three. The earlier statement that
normal projections pass between nearest neighbors does not apply to this layout.
Base footprints do not overlap: minimum clearance is 10 − 9√3/2 = 2.205771 mm.
In the periodic limit bases cover 40.5% of the carrier plane; the remaining space
is open. An upward ray can clear a neighboring pyramid even when its plan projection
points at that neighbor. Broad useful angular coverage is the design objective;
an optimum and reduced refraction have not been established. Materials, coatings,
finite active areas, supports and other ray directions require separate evaluation.

Elements are treated by their center, area and normal. A 1 mm patch and the
9 mm carrier bases are smaller than the 100–200 mm candidate distances, but the
co-location and finite-area approximation errors are not quantified here. No
near-field wave effect or full finite-area integration is modeled. A cover layer,
occlusion and the physical facet supports are omitted.

## Forward model

For source j, patch t and receiving facet (p,k), let d_e and d_r denote source-to-patch
and patch-to-receiver distance. The receiver direction u points **from receiver to patch**.
Emission, incident, exiting and facet cosines use the facing surface normals:

```text
E_t = Σ_j (P_j / π) · cos_emit,j · cos_inc,j / d_e,j²
s_p,k = ρ · (E_t / π) · A_target · cos_exit,p · A_facet · max(n_k · u_p, 0) / d_r,p²
```

Lengths and areas are converted to SI units inside the calculation. Numerical signals
are then normalized by one common constant; they are not predictions of detector watts,
photocurrents or signal-to-noise ratio. A shared scale ρ = 0.6 generates the observations.
Reconstruction treats the product of reflectance and common gain as unknown and profiles
it as a nonnegative amplitude. No separate per-channel gain is fitted.

## What changes as the array moves

For pixel (row 1, column 1), local position (−4.330127, −2.5, 0) mm, slot B is its receiving
slot. Dividing each facet's signal by the sum of all three removes common illumination,
reflectance and distance factors **within that one pixel and exposure**:

| Whole-array x translation, mm | Facet 0 fraction | Facet 1 fraction | Facet 2 fraction |
|---:|---:|---:|---:|
| -20 | 0.384193 | 0.285681 | 0.330126 |
| +0 | 0.361971 | 0.307904 | 0.330126 |
| +20 | 0.339748 | 0.330126 | 0.330126 |

The fractions change because the direction from that moving pixel to the fixed patch
changes. They encode angular weighting in this restricted one-patch scene. Arbitrary
scenes mix contributions from many directions, so these ratios do not directly label a
scene point or supply a depth for each display pixel.

## Tiny inverse calculation

The script produces 144 values: 3 array poses × 2 slots × 8 receiving pixels × 3 facets.
It checks 8,181 candidates: x from −20 to +60 mm, z from 100 to 200 mm,
both in 1 mm steps. For each candidate, f is its full 144-channel prediction for unit
shared scale, and y is the synthetic observation:

```text
a = max(0, dot(f,y) / dot(f,f))
J(x,z) = ||a f(x,z) − y||² / ||y||²
J_depth(z) = min_x J(x,z)
```

The grid minimum is (20, 0, 150) mm,
with fitted scale 0.6 and J = 4.69422e-32.
This recovery is expected because the same noiseless model generates and fits the data.
The best other grid candidate is (20, 0, 151) mm,
with J = 1.99236e-06; a nonzero residual does not establish distinguishability
in a real instrument. The 1 mm grid step is not an achieved spatial resolution.

| Candidate z, mm | Best grid x, mm | J after profiling x and shared amplitude |
|---:|---:|---:|
| 100 | 11 | 0.00330753 |
| 125 | 15 | 0.000492482 |
| 140 | 18 | 6.13375e-05 |
| 149 | 20 | 2.05885e-06 |
| 150 | 20 | 4.69422e-32 |
| 151 | 20 | 1.99236e-06 |
| 160 | 22 | 4.65214e-05 |
| 175 | 25 | 0.000243739 |
| 200 | 31 | 0.000736777 |

As a deliberately underdetermined reference, a **single** coaxial, co-located planar
source/receiver and an on-axis patch provide one intensity s ∝ ρ/z⁴. With unknown shared
amplitude, every positive z fits that one value exactly by choosing amplitude proportional
to z⁴. This explains why one intensity alone is ambiguous; it is not a fair performance
comparison with the 144-channel acquisition or a ranking of facet counts. Angular diversity,
array aperture and registered poses act together in the example; their separate contributions
have not been isolated by a matched-budget experiment.

## Reproduce and inspect

Run from the repository root using Python with NumPy already installed:

```powershell
python example/model.py
```

The script writes [example.json](example.json) with all 144 normalized signals, facet
normals, selected-pixel fractions and 101 depth-objective samples. The corresponding
source is [model.py](model.py).

**Limits:** one isolated, static, known-orientation patch; known y and area; exact pose
and channel calibration; no noise, ambient, crosstalk, occlusion or device optics. The
calculation neither reconstructs a hand nor validates hardware, sensing range, accuracy,
uniqueness for a general scene, novelty, or an advantage over another sensor.
