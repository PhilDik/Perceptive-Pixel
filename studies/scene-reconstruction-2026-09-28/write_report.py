"""Build bilingual scientific documentation from retained raw results."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent

def main():
    result=json.loads((ROOT/'experiment-results.json').read_text())
    stats=json.loads((ROOT/'summary.json').read_text())
    seq=json.loads((ROOT/'sequential-results.json').read_text())
    rows=stats['by_scene'];names={'separated_colours':'Разделённые цветные участки','near_oblique':'Ближние наклонные направления','similar_colours_close':'Близкие участки одного цвета'}
    table='| Сцена | Плоская: покой | Плоская: сдвиги | Плоская: сдвиги + повороты | 15°: покой | 15°: сдвиги | 15°: сдвиги + повороты |\n|---|---:|---:|---:|---:|---:|---:|\n'
    en_table='| Scene | Flat static | Flat translation | Flat combined | 15° static | 15° translation | 15° combined |\n|---|---:|---:|---:|---:|---:|---:|\n'
    for sc in names:
        values=[next(r['median_xyz_rmse_mm'] for r in rows if r['scene']==sc and r['alpha_deg']==a and r['mode']==m) for a in [0,15] for m in ['static','translation','rigid']]
        tail=' | '+' | '.join(f'{v:.2f}' for v in values)+' |\n'
        table+='| '+names[sc]+tail;en_table+='| '+sc+tail
    ru=f'''# От смешанных измерений к координатам и цвету: вычислительный демонстратор

28 сентября 2026. **Работающий код на синтетических данных. Три небольших участка с неизвестными xyz и отражательной способностью; изготовленного устройства, обученной сети и текстурированной карты окружения нет.**

## Что добавлено к предыдущим расчётам

Раньше боковые координаты участков были заранее известны и подбиралась главным образом глубина. Теперь решатель получает исходные смешанные сигналы и известные состояния панели, но не координаты или цвета сцены. Он одновременно оценивает **9 координат и 9 коэффициентов отражения**. Количество участков (три), площадь каждого (1 мм²) и одинаковые мировые нормали −z пока известны. Это задача локализации разреженных участков, а не восстановление произвольных протяжённых поверхностей.

Цвет здесь означает три идеальные откалиброванные спектральные полосы с коэффициентами отражения от 0 до 1. Три грани не принимаются за RGB. Отображение коэффициентов цветными маркерами в рисунке иллюстративно; ни реальная цветопередача материала, ни текстура внутри участка не моделируются.

## Конструкция опыта и ресурсы

Плоские области и грани 15° размещены в матрице 4×4 с авторским вертикальным сдвигом столбцов. Во всех вариантах три области на пиксель считываются отдельно. Суммарная активная площадь одинаковая: наклонная пирамида уменьшается в √cos15° по всем линейным размерам при прежних центрах. Исходная сторона треугольного основания — 9 мм; это иллюстративная крупная модель.

В каждом опыте пять поз и шесть рисунков излучения: шахматный порядок, столбцы и строки, каждый со сменой ролей источников и приёмников. В неподвижном контроле пять раз повторяется одна поза. При сдвигах панель занимает центр и положения ±20 мм по x/y; в комбинированном режиме к тем же сдвигам добавлены наклоны вокруг x/y до 10°. Поворот преобразует позиции и нормали всей панели, но не поворачивает мировые нормали участков вместе с ней.

Каждый случай содержит 2 160 агрегированных наблюдений — 5×6×24 принимающие области×3 полосы. В каждом агрегате суммируются четыре исходных считывания, всего **8 640**. Энергия источников и время интегрирования распределены одинаково, без выравнивания числа полезных принятых фотонов после расчёта. Время/энергия механического перемещения и успокоения панели не моделируются. Общая электронная шкала выбрана один раз: белый участок на 150 мм даёт 100 000 электронов в опорной конфигурации. Это условный бюджет, не измеренная характеристика LED.

Основной сценарий использует η=10⁻⁶ остаточной прямой засветки; физический способ такого подавления не показан. Засветка рассчитывается отдельно для геометрии и рисунка включения и не меняется при жёстком переносе панели. Шум Пуассона добавляется к сигналу вместе с засветкой, затем добавляется шум чтения. Вычитание среднего не устраняет шум засветки. Насыщение и внутрипанельные паразитные пути исключены.

Три сцены и случайные семена зафиксированы в [протоколе](experiment-protocol.json). На каждую конфигурацию приходится три независимых шумовых реализации. Итого 54 основных случая и шесть дополнительных проверок засветки/ошибки позы. Это небольшое описательное исследование; три повтора не дают основания заявлять статистическое превосходство на произвольных сценах.

## Как работает решатель

Откалиброванная прямая модель суммирует вклад всех участков в каждую принимающую область с учётом положений, углов, площадей, источников и расстояний. При предложенных xyz и отражениях вычисляются ожидаемые сигналы. Ограниченный нелинейный решатель уменьшает расхождение с измерениями, одновременно изменяя все 18 параметров. Используется приближение взвешенных квадратов с дисперсией по наблюдённым отсчётам; это не точное пуассоновское правдоподобие и не обученная нейросеть.

У всех вариантов одни и те же шесть общих начальных гипотез и лимит 220 оценок функции на старт. Истинные координаты/цвета не используются для старта или выбора лучшего решения. Выбор происходит только по невязке обучающих наблюдений. Оценка точности выполняется после оптимального сопоставления неупорядоченных троек по 3D-расстоянию. Четыре дополнительные позы используются только для проверки предсказания, не для подгонки или выбора старта.

Генератор данных интегрирует каждую грань по 16 точкам, обратная модель — по четырём. Дифференцируемая модель не учитывает затенение другими пирамидами; отдельная геометрическая проверка обнаружила нулевую долю такого затенения на проверенных истинных и итоговых координатах всех 60 случаев. Это не проверяет все промежуточные состояния оптимизации. Между самими малыми участками перекрытие, многократное рассеяние и протяжённость не моделируются.

## Результаты

Таблица — медиана по трём шумовым реализациям, в каждой сначала вычислена RMSE координат трёх участков; единицы — мм.

{table}
![Все шумовые реализации по координатам и отражению](reconstruction-results.png)

На ближней сцене для граней 15° движение с поворотами уменьшило медианную ошибку координат с 3,45 до 1,07 мм; медианная ошибка отражения — с 0,080 до 0,014. На плоской матрице та же сцена улучшилась с 7,23 до 1,39 мм. Это показывает полезность движения в данном примере, но не доказывает преимущество граней. На первой сцене в комбинированном режиме плоская матрица дала 2,61 мм, а 15° — 6,93 мм. Добавление поворота также не улучшает каждый конкретный шумовой результат.

Для близких участков одинакового цвета ошибки во всех конфигурациях велики: медианы около 28–39 мм. При этом предсказание на отложенных позах может отличаться от истинного сигнала менее чем на 1%. Следовательно, хорошее согласие сигналов само по себе ещё не означает правильные координаты и цвет.

![Исходные сигналы и восстановленные положения](reconstruction-example.png)

Рисунок показывает первую перечисленную сцену и первую шумовую реализацию для каждой траектории, без отбора красивого результата. Цвета отражают три условные полосы, маркеры увеличены для видимости; матрица яркостей слева — показания каналов, не фотография сцены.

## Неоднозначность и неудачи не скрыты

Сохранены все **360 запусков оптимизатора** для 60 наборов данных. Из них 20 не достигли критерия сходимости в выделенный бюджет. В трёх случаях выбранное по минимальной невязке решение также не сошлось; в 30 случаях выбранное решение близко хотя бы к одной границе допустимых координат или отражений. Все случаи включены в статистику. [Флаги](solver-flags.json) и [полные результаты](experiment-results.json) доступны вместе с графиками.

Разные старты трудной сцены давали решения, разделённые на десятки миллиметров, при близких невязках. Порог близости — 1% минимума или единица целевой функции, что больше. Это эвристическая диагностика, не доверительная область; ограниченное число стартов не доказывает единственность решения. Границы 0/1 для отражения тоже могут ограничивать найденную сцену и создавать систематическую ошибку.

После обнаружения трудных случаев проведена отдельная бесшумная диагностика: плоская/15°, первая/третья сцены, точная общая квадратура, шесть общих стартов и расширенный лимит. Во всех четырёх случаях решатель восстановил истинные параметры с численной точностью. Это проверяет согласованность реализации и показывает, что наблюдённые неудачи не сводятся к невозможности решить даже идеальную задачу этим кодом. Однако такой согласованный тест не является независимой валидацией и не доказывает глобальную идентифицируемость или реальную устойчивость. [Протокол диагностики](diagnostic-protocol.json), [результаты](diagnostic-results.json).

## Сохранение состояния и влияние ошибок

Отдельный пример сохраняет все полученные измерения и повторно уточняет одну тройку участков после 1, 3 и 5 поз. Предыдущее решение используется как один из шести стартов. Ошибка координат для фиксированного примера составила 61,43 → 18,05 → 6,93 мм, отражения — 0,276 → 0,108 → 0,089. Состояние включает координаты, отражения, число наблюдений и оговорку о неопределённости. Это реализованное накопительное уточнение разреженной статической сцены; обнаружения новых поверхностей, динамического сопоставления объектов и калиброванного распределения вероятностей здесь нет.

![Накопительное уточнение](sequential-update.png)

По мере получения поз растут и энергия, и число данных. Поэтому этот график иллюстрирует обновление состояния, но не доказывает преимущество последовательного алгоритма при одинаковом полном бюджете. Обучения или изменения весов модели нет. [Полное состояние по шагам](sequential-results.json).

При ошибках заданной позы с σ=0,5 мм по осям переноса и σ=0,5° по двум осям вращения медиана ошибки первой сцены для 15°/комбинированного движения выросла с 6,93 до 12,27 мм в трёх выбранных реализациях. Это иллюстрация чувствительности, не сертифицированный допуск. При η=10⁻⁴ медиана составила 5,42 мм, а средняя ошибка выросла с 6,51 до 7,40 мм: столь малая независимая шумовая выборка не даёт монотонного вывода о медиане. Условие сильного подавления засветки остаётся неподтверждённым аппаратно.

## Что это позволяет утверждать

Теперь есть воспроизводимый программный путь «смешанные отсчёты → известное движение → оценка xyz и трёхполосного отражения → обновление сохраняемого состояния» для строго ограниченной сцены. Он демонстрирует и удачные восстановления, и чувствительность к неоднозначности. Он не устанавливает новизну архитектуры, работоспособность готового экрана, преимущество определённого наклона, дальность, текстурную детализацию или пользу нейросети.

Следующее содержательное усиление — измеренная модель реального приёмника и проверка дополнительных рисунков подсветки/траекторий, которые различают конкурирующие сцены при том же бюджете. Затем можно расширять неизвестные площади/нормали/число поверхностей и сравнивать физический решатель с обучаемым регуляризатором. Последний должен проверяться на неизвестных сценах и не выдавать визуально правдоподобное дополнение за измеренную поверхность.

## Численная проверка и воспроизведение

Аналитические производные по xyz проверены центральной разностью: максимальное относительное расхождение около 1,6×10⁻¹⁰. Совместное жёсткое преобразование панели и сцены сохраняет сигналы с относительной ошибкой около 3,2×10⁻¹⁶. Для выбранной сцены переход квадратуры с 4 к 16 точкам на грань изменил оператор примерно на 0,062%, с 16 к 64 — на 0,016%. Проверены неизменность прямой засветки при позах, взаимность геометрического обмена, его энергетическая граница и дальний закон порядка r⁻⁴. Это проверки кода и выбранных геометрий. [Численные проверки](model-checks.json), [независимый предварительный разбор протокола](PROTOCOL_REVIEW.md).

Основной опыт: 60 наборов данных × 6 стартов = 360 оптимизаций. Накопительный пример: 18 оптимизаций. Бесшумная диагностика: 24. Одно предварительное пробное выполнение: 6, отдельно от основной статистики. Программная спецификация использует [зависимости прежней модели](../layout-noise-2026-09-27/requirements.txt); сохраните соседние каталоги моделей.

```text
python check_model.py
python run_experiment.py
python sequential_example.py
python diagnose_inverse.py
python analyze_scene.py
python write_report.py
```

Скрипты воспроизводят локальные вычисления и не публикуют материалы. [Сводка](summary.json), [таблица всех 60 случаев](metrics.csv), исходные отсчёты первых реализаций каждой основной конфигурации и все решения сохранены.
'''
    english=f'''# Joint xyz and three-band appearance reconstruction

**Implemented synthetic demonstrator; no fabricated device or trained network.** Three small diffuse patches have unknown positions and reflectances (18 fitted parameters). Patch count, 1 mm² areas and world normals are known. This extends the earlier known-lateral-position experiments, but does not reconstruct arbitrary surfaces or texture.

## Matched acquisition

A 4×4 panel compares coplanar regions and 15° facets at equal total active area. Five static/repositioned poses and six complementary checker/row/column source patterns give 2,160 aggregate measurements from 8,640 raw reads across three ideal spectral bands. Static acquisition repeats one pose. Translation uses centre and ±20 mm x/y positions; combined motion adds up to 10° rotations to the same centre positions. Panel positions and normals rotate in world space; scene normals remain fixed.

Total source energy and integration allocation are matched; mechanical motion/settling costs are excluded. One common electron calibration is used without equalizing collected photons. Primary direct-leakage transmission η=10⁻⁶ is hypothetical. Noise is sampled before mean leakage correction. There is no real sensor spectral response, saturation, internal coupling or fabricated isolation mechanism.

Truth uses 16 quadrature points/facet and inversion uses four. The forward operator omits panel shadows; separate sampled checks found none at any true or final estimated patch positions in these 60 cases. This does not check all optimizer intermediate states. Scene occlusion and extended-patch effects are excluded.

## Results

Median xyz RMSE in mm across three independent noise realizations per case:

{en_table}
![Every noisy result, positions and reflectance](reconstruction-results.png)

For the near/oblique scene, 15° combined motion reduces the observed median position RMSE from 3.45 to 1.07 mm and reflectance RMSE from 0.080 to 0.014. Flat combined acquisition also recovers that scene (1.39 mm). The first scene favors the flat combined control (2.61 vs 6.93 mm). The identical-colour scene fails across all configurations, with median position errors around 28–39 mm despite sometimes predicting held-out signals within 1%. There is no established universal facet or rotation advantage.

![Raw channel mixtures and one fixed illustrative reconstruction](reconstruction-example.png)

## Solver, retained failures and evolving state

All configurations use six generic starts, the same search bounds and 220-evaluation limit per start. Ground truth is used for data generation and scoring, not initialization or choosing the best start. The solver jointly estimates xyz and reflectance by observed-count-weighted least squares; it is not an exact Poisson likelihood. Four held-out poses check predicted signals without choosing the fitted solution. Matching unordered patches by position precedes appearance scoring.

The 60 data sets require 360 optimizer runs: 20 do not converge within budget; three selected best fits do not converge, and 30 best fits touch a coordinate or reflectance boundary. All are retained. Similar-cost starts can be tens of millimetres apart. The 1%-or-one-objective-unit diagnostic is heuristic, not a calibrated confidence set or proof of uniqueness. Only three scenes and three noise repetitions were studied; medians describe this experiment, not population-level superiority.

A separate accumulated-state example refits after 1/3/5 poses, retaining all measurements and using the previous state as one start. Position RMSE changes 61.43→18.05→6.93 mm. Energy/data increase with the sequence, so this is not a matched-budget fusion advantage. The stored state has no new-surface discovery, dynamic association, trained weights or calibrated posterior.

![Accumulated state example](sequential-update.png)

Pose perturbations of 0.5 mm/0.5° increase one condition's median RMSE from 6.93 to 12.27 mm across three realizations. A higher-leakage stress has median 5.42 mm but mean 7.40 vs 6.51 mm: the small independent noise sample is insufficient to infer a monotonic median trend. After the failures were observed, four matched-model noiseless diagnostics recovered the known scenes to numerical precision from generic starts. Those tests check implementation consistency, not independent physical identifiability or robustness.

## Reproduction and scope

Read the complete [Russian report](REPORT_RU.md), [pre-fit protocol](experiment-protocol.json), [protocol review](PROTOCOL_REVIEW.md), [source model](scene_model.py), [full results with raw first-trial measurements](experiment-results.json), [all case metrics](metrics.csv), [failure/boundary flags](solver-flags.json), [summary](summary.json), [sequential states](sequential-results.json), [post-result diagnostic protocol](diagnostic-protocol.json), [diagnostic results](diagnostic-results.json) and [model checks](model-checks.json). The separate pilot is retained in [pilot-results.json](pilot-results.json); it is excluded from main statistics.

Use the [existing pinned dependencies](../layout-noise-2026-09-27/requirements.txt) and retain adjacent model directories. In this directory:

```text
python check_model.py
python run_experiment.py
python sequential_example.py
python diagnose_inverse.py
python analyze_scene.py
python write_report.py
```

Checks cover analytic spatial derivatives, rigid-transform invariance, selected quadrature refinement, pose-invariant direct leakage, geometric reciprocity/energy and far-point scaling. Optical/electronic hardware, general-surface mapping, useful distant range, learned reconstruction and novelty remain unvalidated. The implemented state update is a restricted example within the broader proposed architecture.
'''
    (ROOT/'REPORT_RU.md').write_text(ru,encoding='utf-8');(ROOT/'README.md').write_text(english,encoding='utf-8')
    print('Wrote bilingual scene-reconstruction reports.')

if __name__=='__main__':main()
