# From changing light measurements to a scene map

**Conceptual sequence, not an implemented general reconstruction algorithm.** The [main manuscript](../FACETSENSUS.md) describes the sensing architecture; the [reconstruction design](RECONSTRUCTION_DESIGN.md) specifies a candidate estimator and its evaluation.

Сначала элементы панели действительно могут давать лишь грубые световые «пятна»: набор более сильных и более слабых сигналов. Однако такое пятно относится к показаниям приёмников, а не обязательно к отдельному предмету или точке пространства. Когда вся панель перемещается, меняются положения приёмников, направления их чувствительности и условия подсветки. Алгоритм сопоставляет эти изменения с несколькими возможными объяснениями сцены: где находятся поверхности и как они отражают свет. Затем он проверяет, какое объяснение предсказывает весь набор показаний, и уточняет карту. Цвет требует независимых спектральных измерений; три наклонные грани сами по себе не являются RGB. Новые наблюдения уточняют состояние карты, а не обязательно переобучают нейросеть. Сходные сигналы могут соответствовать разным сценам, поэтому неопределённые области нельзя автоматически считать восстановленными.

## What the panel records

Each receiving region returns a number representing a weighted mixture of incoming light. Several surfaces can contribute to one reading, and one surface can affect many regions. A bright patch in a plot of receiver values is therefore not a directly located scene point. Comparing one channel across exposures does not automatically track the same physical feature.

Store the complete measurement vector with channel identity, exposure time, spectral condition, illumination pattern, whole-pixel emission/reception assignment, panel pose and uncertainty, and validity flags. Calibration supplies receiver positions, angular responses, spectral sensitivities, source output, coupling and noise. Three differently oriented regions with identical spectral sensitivity supply angular diversity, not three colour bands.

## How movement supplies constraints

The whole panel moves; its embedded receivers provide the successive observations. In the first proposed baseline, registered positions and orientations are supplied independently and synchronized with the source patterns. A separate imaging camera is not needed as the source of scene samples, but accurate panel pose is still a required input, not something automatically obtained from photocurrents.

Translation changes viewing positions. Rotation changes angular responses and illumination, and receivers away from the rotation axis also move through space. These changes can help distinguish scene hypotheses when they produce measurable differences. Neither motion nor a larger number of readings guarantees useful depth information.

For a restricted diffuse-reflection model with specified lighting, write:

```text
y_i(t) = sum_j A_ij(q_t, e_t, G) rho_j + C_i(t) + D_i + noise_i(t)
```

Here, `G` is candidate geometry; `rho_j` is surface reflectance in a supported spectral band; and `A` predicts how surface region `j` contributes to channel `i` at pose `q_t` under illumination `e_t`. It includes source and receiver responses, distance factors and visibility. Specified environmental lighting belongs in scene transport. `C` represents direct/internal optical coupling and `D` the dark/electronic offset.

## Compare explanations, then update the map

Begin with coarse candidate surfaces and appearance. Predict every channel response, compare predictions with observations, and adjust geometry and appearance to reduce discrepancies under the noise model. Recompute visibility as surfaces change. Compare changes across acquisitions as part of this complete fit, rather than assigning coordinates to isolated signal peaks.

Differences between readings can suppress a stable offset, but they retain ambiguities involving reflectance, illumination, pose and geometry; subtraction also retains noise. Competing scenes may explain the same changes. Keep those alternatives or mark the affected region uncertain.

```text
calibrate the panel; initialize coarse scene hypotheses
for each synchronized acquisition block:
    record all receiving channels, illumination and registered poses
    for each retained scene hypothesis:
        predict all channel responses and their uncertainty
        compare observed and predicted responses across poses
        update geometry and supported appearance; recompute visibility
    retain unresolved alternatives and flag inconsistent observations
    test predictions on reserved poses or illumination patterns
    merge supported updates into the persistent map
```

The map retains geometry, appearance, observation support and uncertainty. Learned regularization may propose updates, but trained weights can remain fixed while the scene state changes. Appearance unsupported by measurements remains a prediction.

The numerical calculations remain much narrower. An earlier example fits two patches with known lateral positions; a [subsequent demonstrator](../studies/scene-reconstruction-2026-09-28/README.md) jointly fits all xyz and three-band reflectances for three patches with known count, areas and normals, including registered translations/rotations and sequential re-fitting. Neither executes the complete general mapping sequence, reconstructs arbitrary objects, or trains a reconstruction network. The sequence combines established modeling and estimation principles into a proposed experiment; it makes no novelty or demonstrated-performance claim.
