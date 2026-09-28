"""Build the local report and publication-style plots for geometry_benchmark.py."""
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "geometry-mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import numpy as np

from geometry_benchmark import BASE_AREA, CELL_AREA, DEFAULT_LAYOUTS, LATTICES, Q, TILTS, geometry


NAMES = {"aligned_square": "Без сдвига Q×Q", "shifted_square": "Сдвиг Q/2 при Q×Q", "vertical": "Авторский сдвиг 5 мм"}
SHORT_EN = {"aligned_square": "Aligned Q by Q", "shifted_square": "Shift Q/2; Q by Q", "vertical": "Author's stagger"}
SHAPES = {"triangle": "Треугольная", "diamond": "Квадратная ромбом"}
COLORS = {"triangle": "#1769aa", "diamond": "#cf6a13"}
STYLES = {"aligned_square": "--", "shifted_square": ":", "vertical": "-"}


def key(shape, layout, tilt):
    return f"{shape}-{layout}-{tilt:.8f}"


def main():
    data = json.loads((ROOT / "geometry-results.json").read_text(encoding="utf-8"))
    assert data["status"] == "completed"
    results = data["results"]
    assert len(results) == 18
    summaries = [v["summary"] for v in results.values()]
    maximum_difference = max(s["maximum_coarse_to_refined_difference_at_selected_phis"] for s in summaries)
    rays = sum(s["independent_active_rays_checked"] for s in summaries)
    maximum_flux_excess = max(s["energy_bound_excess_mm2"] for s in summaries)

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "svg.fonttype": "none"})
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), sharex=True, sharey=True, constrained_layout=True)
    for row, shape in enumerate(["triangle", "diamond"]):
        vertices, faces, _, _ = geometry(shape, 30)
        for col, layout in enumerate(DEFAULT_LAYOUTS):
            ax = axes[row, col]
            basis = np.asarray(LATTICES[layout])
            for i in range(-1, 2):
                for j in range(-1, 2):
                    center = i * basis[0] + j * basis[1]
                    for facet, face in enumerate(faces):
                        ax.add_patch(Polygon(face[:, :2] + center, closed=True, facecolor=COLORS[shape],
                                             alpha=.34 + facet * .12, edgecolor="white", linewidth=.65))
                    ax.add_patch(Polygon(vertices[:-1, :2] + center, closed=True, fill=False,
                                         edgecolor=COLORS[shape], linewidth=.9))
                    ax.plot(center[0], center[1], ".", color="#253349", markersize=2)
            ax.set_aspect("equal")
            ax.set_xlim(-21, 21)
            ax.set_ylim(-21, 21)
            ax.set_xticks([-15, 0, 15])
            ax.set_yticks([-15, 0, 15])
            ax.grid(alpha=.12)
            ax.set_title(SHORT_EN[layout] + f"\nbase gap {summaries[0]['clearance_mm']:.2f} mm" if False else SHORT_EN[layout])
            if col == 0:
                ax.set_ylabel(("Upright triangular bases" if shape == "triangle" else "Square bases as diamonds") + "\ny (mm)")
            if row == 1:
                ax.set_xlabel("x (mm)")
            gap = results[key(shape, layout, 30)]["summary"]["clearance_mm"]
            ax.text(.03, .02, f"Minimum base gap: {gap:.3f} mm", transform=ax.transAxes, fontsize=9,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": .9})
    fig.suptitle("Equal base area and equal pixel density; every triangle keeps the same orientation", fontsize=13)
    fig.savefig(ROOT / "geometry-layouts.png", dpi=160)
    fig.savefig(ROOT / "geometry-layouts.svg")
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8), constrained_layout=True, sharey=True)
    for ax, tilt in zip(axes, TILTS):
        for shape in ["triangle", "diamond"]:
            for layout in DEFAULT_LAYOUTS:
                entry = results[key(shape, layout, tilt)]
                channels = np.asarray(entry["channels_mm2"])
                normalized = channels[-1].sum(axis=1) / BASE_AREA * 100
                label = ("Triangle" if shape == "triangle" else "Diamond") + ": " + SHORT_EN[layout]
                ax.plot(data["parameters"]["phi_deg"], normalized, color=COLORS[shape],
                        linestyle=STYLES[layout], linewidth=1.5, label=label)
        ax.set_title(f"Facet-normal tilt {tilt:.2f}°")
        ax.set_xlabel("Azimuth (degrees)")
        ax.set_xticks([0, 90, 180, 270, 360])
        ax.set_xlim(0, 360)
        ax.grid(alpha=.2)
    axes[0].set_ylabel("Total receiving response (% of frontal response)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, frameon=False, fontsize=9)
    fig.suptitle("Grazing reception: source at 85° from the panel normal (5° above the panel)", fontsize=13)
    fig.savefig(ROOT / "geometry-angular.png", dpi=160)
    fig.savefig(ROOT / "geometry-angular.svg")
    plt.close(fig)

    rows = []
    for tilt in TILTS:
        for shape in ["triangle", "diamond"]:
            for layout in DEFAULT_LAYOUTS:
                summary = results[key(shape, layout, tilt)]["summary"]
                a = summary["selected_angles"]
                rows.append(f"| {tilt:.2f}° | {SHAPES[shape]} | {NAMES[layout]} | {100*a['75']['worst_refined_sample']:.2f}% | {100*a['80']['worst_refined_sample']:.2f}% | {100*a['85']['worst_refined_sample']:.2f}% | {100*a['85']['mean_coarse']:.2f}% |")
    clearance_rows = []
    for shape in ["triangle", "diamond"]:
        values = [results[key(shape, layout, 30)]["summary"]["clearance_mm"] for layout in DEFAULT_LAYOUTS]
        clearance_rows.append(f"| {SHAPES[shape]} | " + " | ".join(f"{v:.3f}" for v in values) + " |")
    report = f"""# Треугольники и ромбы: отдельная проверка геометрического затенения

27 сентября 2026. Локальный численный эксперимент; физический прибор не изготовлен.

**Единого победителя по всем проверенным углам нет.** Авторская треугольная укладка лучше квадратных пирамид-ромбов по худшему суммарному отклику при 85° в этих вариантах размеров. При наклоне граней 30° и направлении 75° ромбы имеют больший худший отклик. Это сравнение приёма внешнего света, а не доказательство меньшей паразитной засветки или лучшего восстановления глубины.

## Сопоставимые размеры и контроль сдвига

У всех вариантов площадь основания {BASE_AREA:.6f} мм², площадь ячейки {CELL_AREA:.6f} мм² и заполнение 40,5%. Треугольник равносторонний со стороной 9 мм; квадрат со стороной {np.sqrt(BASE_AREA):.6f} мм повернут вершинами по ±x, ±y. Все треугольники направлены вершиной вверх, без чередования ориентации. При одинаковом наклоне нормалей формы имеют одинаковые суммарную площадь боковых граней и фронтальную проекцию. Высота различается; принимающих каналов три или четыре.

1. **Без сдвига Q×Q:** базис `(Q,0),(0,Q)`, Q={Q:.6f} мм.
2. **Сдвиг Q/2 при Q×Q:** `(Q,Q/2),(0,Q)`. Сравнение с первым вариантом изменяет только сдвиг, сохраняя оба шага и площадь.
3. **Авторская укладка:** `(8.660254,5),(0,10)` мм. Плотность та же; относительно первого варианта меняются и сдвиг, и отношение горизонтального/вертикального шагов.

Первоначальный контроль без сдвига при шагах 8,660254×10 мм **отклонён**: основания треугольников шириной 9 мм пересекаются. Такой вариант нельзя использовать для физического ранжирования. Он сохранён в `rejected_controls` исходных данных.

![Три физически допустимые укладки для каждой формы](geometry-layouts.png)

Минимальный зазор между основаниями, мм:

| Форма | Без сдвига Q×Q | Сдвиг Q/2 при Q×Q | Авторская укладка |
|---|---:|---:|---:|
{chr(10).join(clearance_rows)}

## Угловое сравнение

Угол источника θ отсчитывается от нормали панели; 85° — 5° над плоскостью. Отклик — сумма эффективных принимающих площадей всех граней одного целого пикселя, нормированная на фронтальный отклик. «Худший» — минимальный найденный по азимуту, а не математически доказанный непрерывный минимум.

| Наклон нормали | Форма | Укладка | Худший, θ75° | Худший, θ80° | Худший, θ85° | Средний, θ85° |
|---:|---|---|---:|---:|---:|---:|
{chr(10).join(rows)}

Десятые и сотые здесь позволяют сопоставлять расчёты; они не задают точность будущего устройства. Малые различия нельзя надёжно ранжировать без дальнейшего уточнения.

![Азимутальные срезы при скользящем внешнем освещении](geometry-angular.png)

## Метод и проверки

Бесконечная периодическая решётка непрозрачных выпуклых пирамид. Источник далёкий и коллимированный. Каждая боковая грань имеет косинусный отклик; лучи от равновеликих участков её реальной площади проверяются на пересечение с соседними телами. Неосвещённые грани имеют нулевой отклик; отдельного самозатенения положительно ориентированной грани выпуклой пирамиды нет.

Проверены θ=0°,30°,45°,60°,75°,80°,85°; азимут через 5°. Основной расчёт: **32²=1024 точки на грань**. Окрестности двух разнесённых кандидатов на минимум и максимум уточнены при 64²=4096 точках с локальным шагом азимута 2,5°. Максимальное изменение ответа 32²→64² на этих одинаковых выбранных направлениях — **{100*maximum_difference:.3f} процентного пункта** фронтального отклика. Это оценка сходимости выборок, не строгая граница ошибки.

- Проверены нормали, равнобедренность боковых граней, равные площади и плотности, непересечение оснований.
- Независимый алгоритм Möller–Trumbore дал те же решения о видимости на {rays} выбранных лучах от освещённых граней.
- Расширение радиуса соседей на 10 мм не изменило выбранные контрольные ответы.
- Аналитическая фронтальная проекция совпала; проверена граница потока на площадь ячейки. Наибольшее превышение расчёта над этой границей: {maximum_flux_excess:.6g} мм²; отрицательное число означает запас до границы.

**Границы:** не моделируются преломление, покрытия, дифракция, отражения между гранями, поддерживающие структуры, электрические помехи, шум, дальность и реконструкция сцены. Широкий суммарный отклик не равен независимости каналов. Большой зазор между основаниями сам по себе не устанавливает малую прямую оптическую связь между соседями. Влияние числа каналов на шум электроники здесь не сопоставлено. Полный FOV или глобальный оптимум не устанавливаются.

## Файлы

- [geometry_benchmark.py](geometry_benchmark.py) — модель и независимые геометрические проверки.
- [geometry-results.json](geometry-results.json) — все 18 допустимых конфигураций и отклонённый контроль.
- [geometry_report.py](geometry_report.py) — таблица и графики.

Воспроизведение: `python geometry_benchmark.py`, затем `python geometry_report.py`.
"""
    (ROOT / "GEOMETRY_RU.md").write_text(report, encoding="utf-8")
    print(json.dumps({"configurations": len(results), "independent_active_rays_checked": rays,
                      "maximum_refinement_change_percentage_points": maximum_difference * 100,
                      "report": "GEOMETRY_RU.md"}, ensure_ascii=False))


if __name__ == "__main__":
    main()

# Publication clarification; does not modify numerical calculations.
_clarification_path = __import__('pathlib').Path(__file__).resolve().parent / 'GEOMETRY_RU.md'
_clarification = '> **Уточнение от 28 сентября:** квадратные пирамиды в этом расчёте имеют одинаковую ориентацию. Предложенный автором вариант с чередующимся поворотом квадратных оснований не рассчитан. Сравнение с ним этими результатами не установлено.\n\n'
_report = _clarification_path.read_text(encoding='utf-8')
if _clarification not in _report:
    _heading, _body = _report.split('\n', 1)
    _clarification_path.write_text(_heading + '\n\n' + _clarification + _body.lstrip('\n'), encoding='utf-8')
