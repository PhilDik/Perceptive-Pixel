"""Render reports from saved experiments without rerunning numerical fits."""
from pathlib import Path
import json
import math
import numpy as np

ROOT=Path(__file__).resolve().parent

def main():
    initial=json.loads((ROOT/'results.json').read_text())
    challenge=json.loads((ROOT/'range-results.json').read_text())
    summary=json.loads((ROOT/'range-summary.json').read_text())
    checks=json.loads((ROOT/'candidate-checks.json').read_text())
    modes=summary['area_modes']
    table='| Угол / чтение | Одинаковое основание | Одинаковая активная площадь |\n|---|---:|---:|\n'
    en_table='| Tilt / readout | Fixed footprint | Equal total sensitive area |\n|---|---:|---:|\n'
    for a,b in zip(modes['fixed_base']['scores'],modes['fixed_active']['scores']):
        label=f"{a['alpha_deg']}°" + (' / сумма' if a['mode']=='pooled' else ' / раздельно' if a['alpha_deg']==0 else '')
        enlabel=f"{a['alpha_deg']}°" + (' / pooled' if a['mode']=='pooled' else ' / split' if a['alpha_deg']==0 else '')
        table+=f"| {label} | {a['score']*100:.2f}% | {b['score']*100:.2f}% |\n"
        en_table+=f"| {enlabel} | {a['score']*100:.2f}% | {b['score']*100:.2f}% |\n"
    leakage='| Остаточная доля прямой засветки η | Плоская / сумма | 15° | 20° | 30° | 45° |\n|---|---:|---:|---:|---:|---:|\n'
    for eta in [0,1e-6,1e-4]:
        values=[np.mean([r['mean_relative_depth_error'] for r in initial['rows'] if r['stage']=='validation' and r['eta']==eta and r['alpha_deg']==a and r['mode']==m])*100 for a,m in [(0,'pooled'),(15,'split'),(20,'split'),(30,'split'),(45,'split')]]
        leakage+='| '+str(eta)+' | '+' | '.join(f'{v:.2f}%' for v in values)+' |\n'
    max_forward=max(v['forward_relative_l2'] for c in checks['checks'] for v in c['selected_scenes'])
    max_coupling=max(c['coupling_relative_l2'] for c in checks['checks'])
    max_noiseless=max(v['fine_truth_coarse_inverse_noiseless_max_depth_error_mm'] for c in checks['checks'] for v in c['selected_scenes'])
    ru=f'''# Условный выбор наклона: ближняя зона и широкий обзор

28 сентября 2026. Расчётная проверка концепта; не измерение изготовленного экрана.

**Рабочий кандидат — 15°; 20° даёт минимум наблюдаемой средней ошибки на расширенном наборе.** Это следует из заранее записанного правила: выбрать наименьший проверенный положительный угол, у которого средняя ошибка не более чем на 10% выше минимальной. Для дальнейшей проверки выделяем 15–25° и сохраняем 30° как обязательный контроль. Диапазон 15–25° — инженерный выбор, не доверительный интервал оптимального угла. При неизвестной реальной чувствительности и засветке универсальный оптимум не установлен.

## Что именно считали

Сохранена авторская укладка: все треугольные основания вершиной вверх, соседние столбцы сдвинуты вертикально. Угол α измеряется между нормалью грани и нормалью панели; это также угол боковой грани к плоскости экрана. При стороне основания 9 мм высоты для 15° и 20° равны 0,696 и 0,946 мм. Размеры иллюстративные: переход к микропикселям требует новой оценки сигнала, шумов и электроники.

Модель: 4×4 пикселя, три известные трансляции −20/0/+20 мм, два взаимодополняющих расписания излучения/приёма целыми пикселями. Три грани принимающего пикселя читаются отдельно. Три идеальные спектральные полосы моделируются независимо от граней. Два диффузных участка по 1 мм² имеют известные боковые координаты, площади и нормали; оцениваются только две глубины и шесть коэффициентов отражения. Глубина — координата z по нормали панели, а не расстояние до датчика.

Новые 12 сцен поровну распределены между центральными, наклонными и скользящими направлениями; параметры и правило сохранены до подгонок в [протоколе](range_protocol.json). Заданные диапазоны z составляют 25–180 мм, но центральная группа начинается с 75 мм. Поэтому непрерывное покрытие непосредственно перед экраном, в частности фронтальная зона 0–25 мм, этим опытом не проверено. Геометрическая ненулевая чувствительность в [предыдущем диагностическом опыте](../small-tilt-2026-09-28/REPORT_RU.md) не равна достаточной точности глубины.

Средняя абсолютная относительная ошибка — среднее |ẑ−z|/z по двум участкам, шумовым реализациям и сценам. Каждая из трёх групп имеет одинаковый вес. Суммарные энергия излучения, время и 1 728 исходных считываний одинаковы. Общий коэффициент пересчёта фотонов к электронам откалиброван один раз; дальним сценам дополнительный свет не добавляется. Фотоны прямой засветки учитываются до вычитания её среднего: их шум остаётся. Насыщение, внутрипанельные отражения и электрические наводки отсутствуют.

Первичная гипотеза η=10⁻⁶ означает пропускание одной миллионной рассчитанной прямой засветки. **Способ достижения такого подавления не реализован и не подтверждён.** Чувствительность, косинусный угловой отклик и шум общие идеализированные; это не характеристики какого-либо готового экрана.

## Плоские контроли и равная площадь

Контроль 0° содержит три настоящие плоские области в их пространственных положениях. «Сумма» получается сложением тех же трёх шумных наблюдений; дисперсия считывания равна 48 против 16 на отдельную область. Это не аппаратный одноканальный датчик с одним чтением. Иногда сумма даёт меньшую ошибку используемого оценивателя; это не означает, что уничтожение информации фундаментально улучшает измерение.

При одинаковом основании полная площадь граней растёт как 1/cosα. Во втором варианте все линейные размеры пирамиды уменьшаются в √cosα раз при неизменных центрах; суммарная чувствительная площадь становится равной плоскому контролю. Это меняет также высоту, зазоры и взаимную видимость. Следовательно, сравниваются физически разные конструкции с равной активной площадью, а не один искусственно масштабированный сигнал.

## Результат дополнительной проверки: 12 новых сцен

{table}
Здесь 48 шумовых реализаций на сцену и конфигурацию, η=10⁻⁶. Отличие двух столбцов у плоского контроля связано с независимыми шумовыми выборками: при 0° геометрии совпадают.

![Ошибка глубины по углам и группам сцен](angle-selection.png)

Минимум среднего — 20° в обоих столбцах. 15° отстаёт от него на 7,5% при одинаковом основании и 4,2% при одинаковой активной площади, проходя правило 10%. Но описательные 95%-интервалы разности 15°−20° включают ноль: приблизительно −0,15…+0,79 и −0,21…+0,66 процентного пункта. Превосходство одного из этих двух углов не установлено.

При равной активной площади 15° снижает среднюю ошибку с 5,81% у плоской суммы до 4,76% — примерно на 18% относительно. Описательный интервал разности составляет −1,97…−0,26 процентного пункта. Это условный результат данного оценивателя, сцен и шума; не процент улучшения будущего устройства.

Интервалы получены 2 000 повторными выборками сцен внутри каждой из трёх групп и шумовых реализаций внутри сцен. Сцены выбираются совместно для сравнений; шум между углами независим. Парность исходных наблюдений сохранена только для плоской суммы и раздельного чтения. Интервалы не скорректированы за выбор угла и множество сравнений. Четыре сцены на группу не описывают всё разнообразие окружения.

В этой дополнительной проверке 15° — наименьший положительный угол. Углы 5°/10° были в первом поиске, но не на новых 12 сценах: их конкурентоспособность на них не исключена.

## Почему результат не сводится к одному «оптимальному» углу

Первый поиск 0–60° на трёх исходных сценах дал минимум 20° и выбор 15° по правилу 10%. На следующих трёх сценах минимум сменился на 30°. Именно это стало причиной дополнительной проверки, а не основанием скрыть неудобные результаты. При η=10⁻⁶ на тех трёх сценах средние ошибки равнялись 4,25% для плоской суммы, 3,64% для 15°, 3,16% для 20° и 2,84% для 30°.

На тех же трёх проверочных сценах результат меняется с засветкой:

{leakage}
При η=10⁻⁴ плоская матрица оказывается лучше наклонных вариантов. В идеальной геометрии у плоскости нет прямого внешнего обмена между копланарными областями; её небольшие различия между строками — шум Монте-Карло. Это не отсутствие реальной внутренней засветки в плоском дисплее.

30° сохраняется контролем: он выиграл предыдущую проверку и находится в пределах 10% нового минимума при равной активной площади. Уменьшение наклона снижает прямую засветку, но ослабляет различия угловых каналов. Один этот геометрический аргумент не определяет точность восстановления.

## Дальняя сцена, проверки и границы вывода

Локальная линейная проверка участков на z≈0,50 и 0,91 м при том же световом бюджете и неизвестных боковых координатах показала очень плохую обусловленность глубины. Для 15° расчётные локальные масштабы неопределённости — десятки и сотни метров, существенно больше самой сцены. Такие числа — предупреждение о почти неразличимых объяснениях в данной модели, не достоверная оценка точности настоящего устройства. Восстановление дальней сцены не продемонстрировано.

Первый этап содержит {initial['fit_count']:,} шумных подгонок, дополнительный — {challenge['fit_count']:,}, всего {initial['fit_count']+challenge['fit_count']:,}. Несходимостей нет. В дополнительном этапе {challenge['boundary_fits']} подгонок достигли зоны 0,05 мм у границы разрешённой глубины 20–200 мм; они сохранены в статистике и перечислены в [проверках](candidate-checks.json). Нулевая несходимость не доказывает единственность решения.

Для 15/20/25/30° в обеих нормировках выполнено выборочное сгущение квадратуры с 16 до 64 точек на грань. Максимальное относительное изменение вектора прямой засветки — {max_coupling*100:.2f}%; сигнала в трёх выбранных сценах — {max_forward*100:.3f}%. Максимальная ошибка глубины при более точном бесшумном прямом расчёте и грубой обратной модели — {max_noiseless:.3f} мм. Это проверка численной согласованности, не независимый эксперимент и не граница ошибок для всех сцен.

Повороты, неизвестные произвольные поверхности, текстуры, оценка позы, реальная спектральная чувствительность, обученная сеть и изготовленные грани не проверены. Сравнение с чередующимся поворотом квадратных пирамид также не выполнено. [Готовые аппаратные классы и их интерфейсы](HARDWARE_RU.md) рассмотрены отдельно; численные результаты не переносятся на них без измеренной модели.

## Файлы и воспроизведение

Исходные [результаты первого этапа](results.json), [результаты 12 сцен](range-results.json), [статистика](range-summary.json), [правило первого выбора](selection_frozen.json) сохранены полностью. Использованы зависимости [предыдущего исследования](../layout-noise-2026-09-27/requirements.txt); сохраняйте соседние папки с его кодом и `facet-motion-2026-09-26/model.py`.

```text
python select_angle.py
python confirm_range.py
python analyze_range.py
python verify_candidates.py
python write_report.py
```

Последние команды анализируют сохранённые расчёты и выполняют выборочные проверки; ни один скрипт не подключает экран, не обучает нейросеть и не публикует файлы.
'''
    en=f'''# Conditional tilt selection and planar controls

28 September 2026. Synthetic, restricted two-patch inversion; no fabricated sensing display or learned scene reconstruction.

**15° is the working candidate under a predeclared smallest-within-10% rule; 20° has the lowest observed mean error in the 12-scene challenge.** Their descriptive difference intervals include zero. Prioritize 15–25° for subsequent investigation, retaining 30° as a control because it won the earlier three-scene validation. This is not a universal optimum or a confidence interval for the best angle.

The primary assumed direct-leakage transmission is **η=10⁻⁶, with no demonstrated suppression hardware**. The same-area comparison gives:

{en_table}
Values are mean absolute relative depth errors, equally weighted over two patches, 48 noise trials and 12 scenes (four central, four oblique, four grazing). In the equal-area case, 15° gives 4.76% versus 5.81% for the pooled planar control, about 18% lower in this conditional task. The descriptive difference interval is −1.97 to −0.26 percentage points. Intervals are exploratory, not adjusted for model/angle selection or multiple comparisons.

![Conditional angle comparison](angle-selection.png)

## Protocol and limitations

All triangular bases point in the same direction, with vertically offset neighboring columns. Tilt is facet-normal angle from the panel normal. Three known translations of −20/0/+20 mm and two whole-pixel source/receiver schedules are used on a 4×4 panel. Three spectral bands are independent of the three facets. Two 1 mm² diffuse patches have known lateral positions, areas and normals; only two depths and six reflectance coefficients are fitted. The later challenge samples axial depths in specified ranges 25–180 mm, but central scenes start at 75 mm. It does not establish continuous near-field coverage or depth performance immediately in front of the screen.

Emitted energy, exposure and 1,728 raw readouts are matched. The pooled planar control sums the same three noisy observations, with read variance 48 versus 16 per separate region; it is not a single-read physical detector. Better pooled estimates do not mean information removal is fundamentally beneficial. To equalize active area, all pyramid dimensions shrink by √cosα at fixed center spacing; gaps, height and visibility consequently change too.

Initial selection examined 0–60° on three scenes and selected 15° (minimum 20°). Three new validation scenes favored 30°. The additional 12-scene challenge therefore tests robustness, with its protocol saved before those fits. Only 15/20/25/30/35/45° and 0° were included in this challenge: it does not rule out 5°/10° on these scenes. Planar zero-angle differences across independent experiments are Monte Carlo variability.

At η=10⁻⁴ on the three validation scenes, pooled planar error was 3.96%, versus 5.53%, 5.56%, 5.90% and 6.97% for 15/20/30/45°. **The planar control wins that leakage scenario.** A fixed-budget far-scene local-information diagnostic is severely ill-conditioned; it does not demonstrate useful distant mapping. Internal crosstalk, saturation, real sensor spectra, pose error, panel rotations, unknown general surfaces and learned reconstruction are absent.

## Evidence and reproduction

The two new stages contain **20,160 noisy fits**, all optimizer-converged, with **eight retained boundary fits** in the challenge. Selected quadrature refinements change direct-coupling vector norms by at most {max_coupling*100:.2f}% and useful-signal norms by {max_forward*100:.3f}%; the largest selected fine-forward/coarse-inverse noiseless depth error is {max_noiseless:.3f} mm. These are numerical checks, not hardware validation.

The [Russian report](REPORT_RU.md) gives the complete protocol, leakage table and qualifications. Read the [hardware comparison](HARDWARE_RU.md), [first protocol](protocol.json), [frozen initial choice](selection_frozen.json), [challenge protocol](range_protocol.json), [initial raw results](results.json), [challenge raw results](range-results.json), [bootstrap summary](range-summary.json) and [numerical checks with retained flags](candidate-checks.json).

Install the [pinned dependencies](../layout-noise-2026-09-27/requirements.txt), preserve the adjacent layout/noise and facet-motion module paths, and run in this directory:

```text
python select_angle.py
python confirm_range.py
python analyze_range.py
python verify_candidates.py
python write_report.py
```

All randomness uses saved seeds. Bootstrap jointly resamples scenes within groups, independently resamples noise across angles, and preserves exact planar split/pooled pairing. No program controls hardware, trains a network or publishes a remote revision.
'''
    (ROOT/'REPORT_RU.md').write_text(ru,encoding='utf-8')
    (ROOT/'README.md').write_text(en,encoding='utf-8')
    print(json.dumps({'report_written':True,'total_new_fits':initial['fit_count']+challenge['fit_count']}))

if __name__=='__main__':main()
