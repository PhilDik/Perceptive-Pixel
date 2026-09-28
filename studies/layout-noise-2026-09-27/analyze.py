"""Summaries, bootstrap intervals, plots and the Russian experiment report."""
from pathlib import Path
import os,json,csv,math
import numpy as np
ROOT=Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR']=str(ROOT/'plot-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

d=json.loads((ROOT/'depth-results.json').read_text())
c=json.loads((ROOT/'controlled-results.json').read_text())
v=json.loads((ROOT/'validation-depth.json').read_text())
g=json.loads((ROOT/'geometry-results.json').read_text())
rows=d['rows'];geos=d['geometry']
SCENES=d['parameters']['scenes']
LABEL={'central':'Центральная','oblique':'Боковая','grazing':'Скользящая'}
LAYOUT={'aligned':'Ровная Q×Q','shifted':'Только сдвиг Q/2','vertical':'Авторская укладка'}
SHAPE={'triangle':'Треугольники','diamond':'Ромбы'}
ALPHAS=sorted(set(r['tilt_deg'] for r in rows))

def row(shape,alpha,layout,scene,eta=1e-6):
    return next(r for r in rows if r['shape']==shape and r['tilt_deg']==alpha and r['layout']==layout and r['scene']==scene and r['optical_leakage_transmission']==eta)

def errors(r):
    truth=SCENES[r['scene']]['z']
    return np.abs(np.array([t['z_mm'] for t in r['estimates']])-truth).mean(axis=1)

def interval(values,rng):
    draws=values[rng.integers(0,len(values),(2000,len(values)))]
    return np.quantile(np.median(draws,axis=1),[.025,.975])

rng=np.random.default_rng(1270927)
comparisons=[]
for alpha in ALPHAS:
 for scene in SCENES:
  for eta in [0.,1e-6,1e-4]:
    a,b=row('triangle',alpha,'vertical',scene,eta),row('diamond',alpha,'vertical',scene,eta)
    av,bv=errors(a),errors(b)
    aci,bci=interval(av,rng),interval(bv,rng)
    diffs=np.median(av[rng.integers(0,len(av),(2000,len(av)))],axis=1)-np.median(bv[rng.integers(0,len(bv),(2000,len(bv)))],axis=1)
    ci=np.quantile(diffs,[.025,.975])
    comparisons.append({'tilt_deg':alpha,'scene':scene,'eta':eta,
                        'triangle_median_mm':float(np.median(av)),'diamond_median_mm':float(np.median(bv)),
                        'triangle_median_bootstrap95_mm':aci.tolist(),'diamond_median_bootstrap95_mm':bci.tolist(),
                        'triangle_minus_diamond_median_mm':float(np.median(av)-np.median(bv)),
                        'difference_bootstrap95_mm':ci.tolist(),
                        'interpretation':'exploratory marginal interval; not corrected for multiple comparisons'})
(ROOT/'comparisons.json').write_text(json.dumps(comparisons,indent=2),encoding='utf-8')
fields=['id','shape','tilt_deg','layout','scene','optical_leakage_transmission','signal_electrons','background_electrons',
        'background_to_signal','median_mean_absolute_depth_error_mm','mean_absolute_depth_error_mm',
        'p90_mean_absolute_depth_error_mm','failure_gt10mm_fraction','nonconverged','grid_interpolation_relative_l2']
with (ROOT/'depth-summary.csv').open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
with (ROOT/'leakage-summary.csv').open('w',encoding='utf-8',newline='') as f:
    fields2=['id','shape','tilt_deg','layout','height_mm','facet_area_total_mm2','leakage_fraction_all_bands']
    writer=csv.DictWriter(f,fieldnames=fields2,extrasaction='ignore');writer.writeheader();writer.writerows(geos)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False})
fig,ax=plt.subplots(1,2,figsize=(12,4.6),layout='constrained')
for j,shape in enumerate(['triangle','diamond']):
    vals=[next(q['leakage_fraction_all_bands']*100 for q in geos if q['shape']==shape and q['tilt_deg']==45 and q['layout']==la) for la in ['aligned','shifted','vertical']]
    ax[0].bar(np.arange(3)+(j-.5)*.34,vals,width=.32,label='Triangles' if j==0 else 'Square diamonds',color=['#1769aa','#cf6a13'][j])
ax[0].set(xticks=np.arange(3),xticklabels=['Aligned\nQ by Q','Half-shift\nQ by Q',"Author's\nstagger"],ylabel='Energy entering receiving neighbours (%)',title='Direct optical leakage, 45° facet normals')
ax[0].legend()
for i,r in enumerate(c['rows']):
    e=np.abs(np.array([q['z_mm'] for q in r['estimates']])-c['scene']['z']).mean(axis=1)
    q=np.quantile(e,[.25,.5,.75])
    ax[1].errorbar(i,q[1],yerr=[[q[1]-q[0]],[q[2]-q[1]]],fmt='o',color='#1769aa',capsize=5)
ax[1].set(xticks=np.arange(4),xticklabels=['0','1','10','100'],xlabel='Background / fixed calibration reference',
          ylabel='Median depth error with interquartile range (mm)',title='Same useful signal; only contamination changes')
fig.suptitle('Synthetic optical model — equal area, energy and raw readout count',fontsize=13)
for ext in ['png','svg']:fig.savefig(ROOT/f'noise-and-leakage.{ext}',dpi=160)
plt.close(fig)

fig,axs=plt.subplots(1,3,figsize=(13,4.6),layout='constrained')
for alpha,ax in zip(ALPHAS,axs):
    for j,shape in enumerate(['triangle','diamond']):
        vals=[];lo=[];hi=[]
        for scene in SCENES:
            item=next(r for r in comparisons if r['tilt_deg']==alpha and r['scene']==scene and r['eta']==1e-6)
            prefix='triangle' if shape=='triangle' else 'diamond'
            med=item[prefix+'_median_mm'];ci=item[prefix+'_median_bootstrap95_mm']
            vals.append(med);lo.append(med-ci[0]);hi.append(ci[1]-med)
        ax.errorbar(np.arange(3)+(j-.5)*.12,vals,yerr=[lo,hi],fmt='o-',color=['#1769aa','#cf6a13'][j],capsize=3,
                    label='Triangles' if j==0 else 'Square diamonds')
    ax.set(xticks=np.arange(3),xticklabels=['Central','Oblique','Grazing'],title=f'Facet normals {alpha:.2f}°',
           ylabel='Median mean absolute depth error (mm)',ylim=(0,None))
    ax.legend(fontsize=9)
fig.suptitle("Author's stagger for both shapes; hypothetical leakage transmission 10⁻⁶\n48 trials/point; marginal bootstrap 95% intervals, no multiple-comparison correction",fontsize=12)
for ext in ['png','svg']:fig.savefig(ROOT/f'depth-comparison.{ext}',dpi=160)
plt.close(fig)

leak_table=['| Форма | Наклон | Ровная Q×Q | Только сдвиг Q/2 | Авторская укладка |','|---|---:|---:|---:|---:|']
for shape in ['triangle','diamond']:
 for alpha in ALPHAS:
    vals=[next(x['leakage_fraction_all_bands']*100 for x in geos if x['shape']==shape and x['tilt_deg']==alpha and x['layout']==la) for la in ['aligned','shifted','vertical']]
    leak_table.append(f"| {SHAPE[shape]} | {alpha:.2f}° | "+' | '.join(f'{x:.3f}%' for x in vals)+' |')
noise_table=['| Засветка / фиксированный эталон | Медианная ошибка глубины | 90-й процентиль |','|---:|---:|---:|']
for r in c['rows']:
    noise_table.append(f"| {r['background_in_reference_units']:.0f} | {r['median_mean_absolute_depth_error_mm']:.2f} мм | {r['p90_mean_absolute_depth_error_mm']:.2f} мм |")
depth_table=['| Сцена, 45° | Треугольники | Ромбы | 95% интервал разности медиан, мм |','|---|---:|---:|---:|']
for scene in SCENES:
    r=next(r for r in comparisons if r['tilt_deg']==45 and r['scene']==scene and r['eta']==1e-6)
    ci=r['difference_bootstrap95_mm']
    depth_table.append(f"| {LABEL[scene]} | {r['triangle_median_mm']:.2f} мм | {r['diamond_median_mm']:.2f} мм | [{ci[0]:+.2f}; {ci[1]:+.2f}] |")
maxq=max(r['leakage_total_relative_change_n4_vs_n8'] for r in v['rows'])
maxf=max(r['truth_forward'][s]['rgb_signal_relative_l2_n4_vs_n8'] for r in v['rows'] for s in ['central','grazing'])
failed=[{'id':r['id'],'scene':r['scene'],'eta':r['optical_leakage_transmission'],'trials':[i for i,t in enumerate(r['estimates']) if not t['success']]} for r in rows if r['nonconverged']]
(ROOT/'solver-flags.json').write_text(json.dumps(failed,indent=2),encoding='utf-8')
report=f'''# FacetCensus: сдвиг, помехи соседей и точность глубины

27 сентября 2026. **Локальная вычислительная проверка, не измерения изготовленного дисплея.**

Проверены 18 сочетаний формы, угла и укладки; выполнены **7 776 шумных восстановлений** в основном опыте и **1 024** в контроле влияния засветки. Всего **8 800** шумных подгонок. Не все реализации сходятся: один основной запуск не достиг критерия остановки в заданный бюджет; он отмечен ниже, результат не скрыт.

## Ответ на гипотезу

При сохранении полезного сигнала и его зависимости от сцены уменьшение посторонней засветки помогает восстановлению. Отдельный контроль с неизменной геометрией это подтверждает.

Для заданного чередования целых излучающих и принимающих пикселей авторская треугольная укладка уменьшила прямую оптическую связь соседей примерно на **20%** относительно допустимой ровной сетки той же плотности. Только полушаговый сдвиг при неизменных двух шагах уменьшил связь примерно на **15%**. Это подтверждает полезность укладки в рассматриваемой модели.

Однако квадратные пирамиды, поставленные ромбами, также получают пользу от сдвига. В авторской укладке их суммарная прямая засветка всего примерно на 3% больше треугольной при 45°. Полезные угловые сигналы и восстановление глубины различаются по сценам. **Универсальное превосходство трёхгранных пирамид над ромбами не установлено.** Угол 51,84° также не стал универсальным оптимумом.

## Что именно сопоставлялось

1. Треугольное основание со стороной 9 мм, все вершины направлены вверх в плане. Три независимые грани.
2. Квадратное основание равной площади, сторона 5,922333 мм, вершины по ±x/±y. Четыре независимые грани.

Площадь основания 35,074029 мм², площадь ячейки 86,602540 мм². Наклоны нормалей: 30°, 45°, 51,842773°. При одном наклоне одинаковы суммарная площадь граней и фронтальная проекция. Между разными наклонами площадь граней меняется: `A_base/cos(α)`. Высота при разных формах также различается; сравнение формы не сводится к одному числу граней.

Три укладки:

- **Ровная Q×Q:** шаг Q=9,306049 мм в обоих направлениях.
- **Только сдвиг:** те же шаги, нечётные столбцы подняты на Q/2. Это чистый контроль сдвига.
- **Авторская:** расстояние столбцов 8,660254 мм, вертикальный шаг 10 мм, вертикальный сдвиг нечётных столбцов 5 мм. Плотность сохраняется; по сравнению с ровной сеткой меняются сдвиг и соотношение шагов.

Простое удаление сдвига из авторской укладки при сохранении шагов 8,660254×10 мм приводит к пересечению треугольных оснований. Такой контроль исключён. Непересечение всех используемых оснований проверено.

![Формы и укладки](geometry-layouts.png)

## Три разных эффекта

**Затенение:** соседи перекрывают часть полезного внешнего света. Рассчитано отдельно для периодической матрицы, с интегрированием по граням и направлениям. При скользящих направлениях у треугольников бывают преимущества; при других углах лучше ромбы. Подробные таблицы: [геометрия](GEOMETRY_RU.md).

**Прямая засветка:** свет излучающего пикселя попадает в принимающий пиксель без отражения от объекта. Рассчитаны пары конечных площадок на гранях с их направлениями, расстояниями и перекрытием другими пирамидами. Модель предполагает непрозрачные пирамиды и идеальные ламбертовские грани. Внутренние отражения, покровный слой, волноводы, электрическая наводка и переотражения не учитываются.

**Восстановление:** совместное определение двух глубин и шести цветовых коэффициентов по сигналам всех принимающих граней при движении панели. Снижение засветки может помочь, но между геометриями меняется и полезная информация о сцене.

## Ресурсы и режим работы

Для обратной задачи панель содержит 4×4 целых пикселя. Они помещаются в общую выделенную область 40×48 мм; точные крайние положения элементов различаются между укладками. Края массива не периодические. Три известные позиции панели: x=−20,0,+20 мм. В каждой позиции два такта: восемь пикселей излучают всеми гранями, остальные принимают; затем роли меняются. Клеточный рисунок задаётся чётностью строки+столбца.

Полная энергия и время экспозиции одинаковы, энергия делится между тремя идеальными спектральными полосами. Число исходных считываний тоже одинаково: на принимающий пиксель и такт приходится 12 чтений — три грани по четыре подэкспозиции либо четыре грани по три. После сложения шум считывания каждой грани имеет дисперсию `(12/k)·4` электрон², суммарно 48 электрон² на пиксель. На весь опыт приходится 1 728 исходных значений. Предполагаются независимый шум, одинаковая стоимость считывания и отсутствие дополнительного времени переключения. Число физических каналов электроники остаётся разным.

## Прямая оптическая связь соседей

Таблица показывает долю всей излучённой энергии, которая прямо приходит в принимающие соседние пиксели за расписание из двух ролей, до любого дополнительного подавления. Это **условная геометрическая оценка**, не измеренная засветка будущего экрана.

{chr(10).join(leak_table)}

Схема включения тоже важна. Для треугольников при 45° переход от ровной к авторской укладке снижает засветку примерно на 20% при клеточном расписании, примерно на 2% при чередовании целых столбцов и примерно на 7% при чередовании строк. Альтернативные расписания проверены по засветке; их инверсия не выполнялась. Выигрыш нельзя целиком приписать одной форме основания независимо от режима работы.

![Засветка и независимый контроль её влияния](noise-and-leakage.png)

## Контроль: меняем только засветку

Фиксированы треугольная авторская укладка, наклон 45°, центральная сцена, полезный сигнал и обратная модель. Дополнительный фон равномерно распределён по каналам и не зависит от подбираемой сцены. Эталон — заранее заданные 100 000 электронов от отдельного белого участка на оси при 150 мм; полезный сигнал контрольной сцены — примерно 101 231 электрон.

Для каждого уровня выполнено 256 независимых реализаций. В каждом опыте берётся средняя абсолютная ошибка двух глубин; в таблице — её медиана и 90-й процентиль.

{chr(10).join(noise_table)}

Именно этот опыт проверяет причинную часть «меньше засветки → лучше оценка при прочих равных». В основном сравнении прочие условия геометрически различаются, поэтому там такой вывод нельзя предполагать заранее.

Физическая модель шума:

```text
raw = Poisson(S + L) + Normal(0, sigma_read²)
corrected = raw - L
Var(corrected) = S + L + sigma_read²
```

Даже точное вычитание средней засветки L оставляет её фотонный шум. При неизменном S уменьшение L на 20% не означает уменьшение ошибки глубины на 20%. Например, если L=S, стандартное отклонение суммарного фотонного шума уменьшается лишь примерно на 5%; при полностью доминирующем L — примерно на 11%. Это иллюстрация дисперсии измерения, не гарантия ошибки нелинейной реконструкции.

## Основной опыт восстановления

Известны координаты x,y двух участков, площадь 1 мм², нормали (0,0,−1), позы панели, мощность и калибровка каналов. Ищутся две глубины и шесть коэффициентов отражения в диапазоне 0…1. Центральная сцена имеет глубины 111,3/156,7 мм, боковая 80,7/117,3 мм, скользящая 30,3/50,7 мм; координаты полностью сохранены в JSON. Это три маленькие синтетические сцены, не карта произвольного окружения. Цветовые полосы условно независимы и калиброваны; три грани не отождествляются с RGB.

Грани интегрируются по 16 площадкам, каждый целый пиксель состоит из реальных наклонных граней с различными центрами. Полезный сигнал включает угловые множители при излучении и приёме и перекрытие другими пирамидами. Истинные глубины находятся между узлами сетки 1 мм. Поиск начинается с сетки 2 мм и непрерывно уточняется по интерполированной модели. Точная модель генерирует показания; интерполяция в инверсии даёт небольшое численное несовпадение.

Одна общая константа переводит энергию в условные электроны, её не подбирают заново под форму или сцену. Добавлены пуассоновский шум и шум считывания. Прямая связь соседей умножается на три **гипотетических** коэффициента передачи: 0, 10⁻⁶, 10⁻⁴. Это сценарии остаточной засветки; физическая реализация подавления на такую величину и сохранение полезного сигнала не доказаны. Даже малый остаток может быть большим относительно слабого отражения от маленького объекта. Не моделируются насыщение, ограничение динамического диапазона и фоновое освещение.

В основной инверсии средняя паразитная засветка считается точно известной и вычитается. Отрицательные остатки сохраняются. Используется взвешенный метод наименьших квадратов с дисперсией, оценённой по исходным показаниям; это не точное пуассоновско-гауссово правдоподобие. Отдельный диагностический опыт в JSON вводит фиксированную ошибку вычитания 0,1% при передаче 10⁻⁴.

Пример при наклоне 45°, авторской укладке обеих форм и передаче паразитного света 10⁻⁶:

{chr(10).join(depth_table)}

Интервалы получены по 2 000 bootstrap-выборок из 48 реализаций. Это исследовательская оценка случайного разброса; поправки на множественные сравнения нет. Небольшое различие медиан не следует называть установленным преимуществом. Все углы, укладки и уровни засветки доступны в [CSV](depth-summary.csv), а полные реализации — в [JSON](depth-results.json).

![Зависимость результата от формы и сцены](depth-comparison.png)

## Проверки и ограничения

- Проверены геометрия и равенство площадей, отсутствие пересечений оснований, сохранение энергии и взаимность прямой оптической связи.
- Для четырёх конфигураций при 45° уточнение двойного интегрирования засветки с 16 до 64 точек на грань изменило суммарную связь не более чем на {100*maxq:.3f}%. Это меньше найденного эффекта сдвига около 20%, но малые межформенные различия всё равно трактуются осторожно.
- В тех же контролях уточнение полезных сигналов центральной/скользящей сцен изменило их относительную норму не более чем на {100*maxf:.3f}%. Худший случай дополнительно проверен по 256 точкам на грань; следующее изменение около {100*v['worst_forward_n16_check']['rgb_signal_relative_l2_n8_vs_n16']:.3f}%.
- Максимальная относительная погрешность интерполяции в основных сценах — {100*max(r['grid_interpolation_relative_l2'] for r in rows):.3f}%; максимальная ошибка глубины в нешумном контрольном восстановлении — 0,266 мм. Это численная погрешность выбранного расчёта.
- Из 7 776 основных шумных подгонок одна не достигла критерия сходимости при лимите 180 оценок вектора невязок (max_nfev): `diamond-shifted-51.842773`, скользящая сцена, передача 10⁻⁶, реализация 17 с нуля. Её последнее приближение остаётся в исходной сводке и помечено `success=false`; для неё нельзя заявлять завершённую оптимизацию. Она не входит в таблицу выше, сравнивающую авторскую укладку при 45°.
- В геометрическом угловом опыте проверены 996 лучей независимым методом Möller–Trumbore; решения совпали. Уточнение 1 024→4 096 точек на грань изменило выбранные отклики не более чем на 0,625 процентного пункта фронтального отклика. Это выборочная сходимость, не строгая граница ошибки для всех направлений.
- Один и тот же класс модели используется для генерации и объяснения данных. Не моделируются неизвестные нормали/площади поверхностей, текстурированная сцена, ошибки позы, динамика, реальная спектральная чувствительность, покрытие и электрические наводки. Нейросеть и долговременная карта не реализованы.

## Итог для концепции

Расчёт поддерживает снижение прямой паразитной связи за счёт вертикального сдвига при выбранном режиме работы. Он подтверждает и вред дополнительного фотонного шума для обратной задачи. Следующее обоснованное утверждение — полезность **совместного выбора укладки, углов, расписания и калибровки**. Более сильное утверждение «эта треугольная матрица всегда лучше любых ромбов восстанавливает окружение» результатами не подтверждается.

## Воспроизведение

```text
python geometry_benchmark.py
python geometry_report.py
python depth_benchmark.py --trials 48 --facet-n 4
python controlled_noise.py
python validate_depth.py
python analyze.py
```

Нужны NumPy, SciPy и Matplotlib. Основной опыт с 7 776 шумными подгонками занял {d['elapsed_seconds']:.1f} с; контроль 1 024 подгонок — {c['runtime_seconds']:.1f} с. Это время исследовательского кода на текущем компьютере, не частота кадров будущего прибора. В архив включена используемая зависимость `../facet-motion-2026-09-26/model.py`; папки надо сохранять рядом.

[Протокол и независимые замечания](PROTOCOL_REVIEW.md) · [Проверка численной точности](validation-depth.json) · [Сравнения с интервалами](comparisons.json) · [Флаги сходимости](solver-flags.json)
'''
(ROOT/'REPORT_RU.md').write_text(report,encoding='utf-8')
print(json.dumps({'main_fits':sum(r['trials'] for r in rows),'control_fits':len(c['rows'])*c['trials_per_level'],
                  'comparison_intervals':len(comparisons),'report':'REPORT_RU.md','solver_flags':failed},ensure_ascii=False))

# Publication clarification; does not modify numerical calculations.
_clarification_path = __import__('pathlib').Path(__file__).resolve().parent / 'REPORT_RU.md'
_clarification = '> **Уточнение от 28 сентября:** квадратные пирамиды в этом расчёте имеют одинаковую ориентацию. Предложенный автором вариант с чередующимся поворотом квадратных оснований не рассчитан. Сравнение с ним этими результатами не установлено.\n\n'
_report = _clarification_path.read_text(encoding='utf-8')
if _clarification not in _report:
    _heading, _body = _report.split('\n', 1)
    _clarification_path.write_text(_heading + '\n\n' + _clarification + _body.lstrip('\n'), encoding='utf-8')
