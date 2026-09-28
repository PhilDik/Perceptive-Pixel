# Layout, direct optical coupling and restricted depth recovery

Computed 27 September 2026; publication clarification added 28 September. **Synthetic calculations, not a fabricated screen or a learned reconstruction system.**

## Geometry scope

All triangular bases point in the same direction. Neighboring columns shift vertically. The author's illustrative lattice uses column/row pitches 8.660254/10 mm and a 5 mm column offset. A valid aligned control and a pure-stagger control both use equal pitches of 9.306049 mm, preserving density. Simply removing the offset from the author's original lattice would cause triangular bases to overlap and was excluded.

The comparison square pyramids have equally oriented diamond-shaped footprints. **The later author-specified alternative with alternating square orientations has not been simulated. These results must not be presented as a comparison against that alternative.** Triangles and squares have equal base area; total facet area matches at a common slope but changes between slopes. Facet-normal tilts are 30°, 45° and 51.842773°; no universal optimum is established.

![Exactly the layouts simulated](geometry-layouts.png)

*The lower row is the tested same-orientation square control, not the untested alternating-orientation proposal.*

## Direct coupling result

For the specified two-slot checkerboard schedule, with whole pixels alternating emission and reception, the following fraction of emitted energy reaches receiving pixels directly before hypothetical suppression:

| Shape, 45° | Aligned | Pure vertical stagger | Author's pitches and stagger |
|---|---:|---:|---:|
| Triangle | 4.819% | 4.103% | 3.868% |
| Same-orientation square control | 5.017% | 4.175% | 3.977% |

For triangles, pure stagger reduces coupling by about 15%; the author's complete layout reduces it by about 20%. With other row/column schedules the latter reduction is only about 7%/2%. Therefore it is not a geometry-independent or schedule-independent percentage. Direct external optical coupling is not electrical leakage, cover-layer propagation or all possible crosstalk.

![Direct coupling and fixed-signal noise control](noise-and-leakage.png)

## Inverse problem and matched resources

The finite panel contains 4×4 pixels. Three known translations x=−20,0,+20 mm and complementary whole-pixel roles are used. Actual rotations are not simulated. Three ideal independent spectral bands do not correspond to the three facets. The scene consists of two small diffuse patches with known lateral positions, areas and normals. Only two depths and six reflectance coefficients are fitted. Truth depths lie off the 1 mm interpolation grid and span approximately 30–157 mm across three scenes.

Total emitted energy, exposure allocation and raw readout count are matched between shapes. There are 12 raw readings per receiving pixel/slot/band: three facets with four subexposures or four facets with three. Noise is sampled before subtracting known mean leakage; the leakage photon noise remains. Saturation, real spectral response, arbitrary textures, pose error, internal reflections and a persistent learned map are absent. Candidate optical leakage transmissions of 0, 10^-6 and 10^-4 are scenarios, not demonstrated suppression hardware.

There are 18 configurations × 3 scenes × 3 leakage levels × 48 noise realizations = **7,776 fits**. One fit did not converge within its evaluation budget and is retained with a failure flag in [solver-flags.json](solver-flags.json). A separate fixed-signal experiment has 4 background levels × 256 realizations = **1,024 fits**, for **8,800** total. In that control, median mean absolute depth error rises from 4.50 to 5.44, 10.14 and 22.37 mm as background increases. This isolates noise, not a change in geometry.

At 45°, author-layout medians for triangle/square are 5.45/4.84 mm in the central scene, 1.41/1.53 mm obliquely and 2.37/3.16 mm in the grazing scene. Bootstrap intervals do not establish a winner in the first two; the grazing result is exploratory and not corrected for multiple comparisons. Neither geometry is established as universally superior.

## Numerical verification and files

Refining direct-coupling integration from 16 to 64 samples per facet changed totals by at most 0.715% in four selected 45° controls. Useful-signal refinement changed relative vector norms by at most 0.805%; the largest further 64→256 change was 0.263%. The maximum recorded noiseless inverse depth error is 0.266 mm. The angular benchmark includes 996 selected rays checked by an independent intersection method. These are numerical consistency/convergence checks, not independent hardware validation or bounds for all scenes.

Read the detailed [Russian report](REPORT_RU.md), [angular geometry report](GEOMETRY_RU.md), [depth summary](depth-summary.csv), [coupling summary](leakage-summary.csv), [numerical checks](validation-depth.json) and [statistical comparisons](comparisons.json). Raw fitted realizations are in [depth-results.json](depth-results.json) and [controlled-results.json](controlled-results.json); angular results are in [geometry-results.json](geometry-results.json).

## Reproduction

Python 3.10 was used with the versions in [requirements.txt](requirements.txt). From this directory:

```text
python geometry_benchmark.py
python geometry_report.py
python depth_benchmark.py --trials 48 --facet-n 4
python controlled_noise.py
python validate_depth.py
python analyze.py
```

Keep the adjacent [retained dependency](../facet-motion-2026-09-26/model.py). Programs regenerate local results; they do not control hardware or train a network. The [proposed full algorithm](../../docs/RECONSTRUCTION_DESIGN.md) remains a separate design specification.
