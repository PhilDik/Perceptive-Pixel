"""Equal-density, finite-area geometric collection of opaque pyramidal pixels.

Python 3 + numpy + matplotlib. Run: python compare_layouts.py --subdivisions 8
No measured optical/electrical properties; results are idealized ray geometry.
"""
from pathlib import Path
import argparse
import json
import math
import time
import numpy as np

ROOT = Path(__file__).resolve().parent
SIDE = 9.0
HEIGHT = 1.5
PITCH = 10.0
CELL_AREA = math.sqrt(3) / 2 * PITCH**2
BASE_AREA = math.sqrt(3) / 4 * SIDE**2
RADIUS = SIDE / math.sqrt(3)
SX = PITCH * math.sqrt(3) / 2
Q = math.sqrt(CELL_AREA)
THETA = np.arange(0.0, 85.01, 2.5)
PHI = np.arange(0.0, 360.0, 5.0)
DESIGNS = {
    'vertical': dict(label='Вертикальный сдвиг 1/2', basis=[[SX, 5], [0, 10]], motif=[[0, 0]], rotation=0),
    'horizontal': dict(label='Горизонтальный сдвиг 1/2', basis=[[10, 0], [5, SX]], motif=[[0, 0]], rotation=0),
    'square': dict(label='Квадратная сетка', basis=[[Q, 0], [0, Q]], motif=[[0, 0]], rotation=0),
    'rotated15': dict(label='Вертикальный сдвиг; поворот 15°', basis=[[SX, 5], [0, 10]], motif=[[0, 0]], rotation=15),
    'rotated30': dict(label='Вертикальный сдвиг; поворот 30°', basis=[[SX, 5], [0, 10]], motif=[[0, 0]], rotation=30),
    'quarter': dict(label='Вертикальный сдвиг 1/4', basis=[[2*SX, 0], [0, 10]], motif=[[0, 0], [SX, 2.5]], rotation=0),
}


def geometry(rotation=0):
    a = np.radians(np.array([90, 210, 330]) + rotation)
    vertices = np.vstack([np.column_stack([RADIUS*np.cos(a), RADIUS*np.sin(a), np.zeros(3)]), [0, 0, HEIGHT]])
    faces = vertices[np.array([[2, 0, 3], [0, 1, 3], [1, 2, 3]])]
    cross = np.cross(faces[:, 1]-faces[:, 0], faces[:, 2]-faces[:, 0])
    norms = np.linalg.norm(cross, axis=1)
    normals = cross/norms[:, None]
    assert np.allclose(norms/2, 13.5)
    assert np.allclose(normals[:, 2], math.cos(math.radians(30)))
    return vertices, faces, normals, norms/2


def sample_faces(faces, n):
    # n^2 equal-area subtriangle centroids per face, no edge samples.
    uv = []
    for i in range(n):
        for j in range(n-i):
            uv.append([(i+1/3)/n, (j+1/3)/n])
            if i+j <= n-2:
                uv.append([(i+2/3)/n, (j+2/3)/n])
    uv = np.array(uv)
    assert len(uv) == n*n
    return faces[:, 0, None, :] + uv[None, :, :1]*(faces[:, 1]-faces[:, 0])[:, None, :] + uv[None, :, 1:]*(faces[:, 2]-faces[:, 0])[:, None, :]


def neighbors(design, own, radius):
    basis = np.array(design['basis'], dtype=float)
    motif = np.array(design['motif'], dtype=float)
    assert abs(abs(np.linalg.det(basis))/len(motif)-CELL_AREA) < 1e-9
    limit = math.ceil((radius+2*np.max(np.linalg.norm(motif, axis=1)))/np.linalg.svd(basis)[1].min())+2
    centers = []
    for i in range(-limit, limit+1):
        for j in range(-limit, limit+1):
            for m in motif:
                c = i*basis[0]+j*basis[1]+m-own
                if 1e-8 < np.linalg.norm(c) <= radius+1e-8:
                    centers.append([*c, 0])
    return np.array(centers)


def polygon_clearance(poly, centers):
    # Separating-axis test, then exact vertex-to-segment minimum distance.
    edges = np.roll(poly, -1, axis=0)-poly
    axes = np.column_stack([-edges[:, 1], edges[:, 0]])
    axes /= np.linalg.norm(axes, axis=1)[:, None]
    minimum = math.inf
    for c in centers[:, :2]:
        other = poly+c
        p, q = poly@axes.T, other@axes.T
        separations = np.maximum(q.min(0)-p.max(0), p.min(0)-q.max(0))
        if separations.max() < -1e-10:
            raise ValueError('Intersecting pyramid footprints')
        for aa, bb in [(poly, other), (other, poly)]:
            for v in aa:
                for a, b in zip(bb, np.roll(bb, -1, axis=0)):
                    edge = b-a
                    t = np.clip((v-a)@edge/(edge@edge), 0, 1)
                    minimum = min(minimum, np.linalg.norm(v-a-t*edge))
    return minimum


class RayModel:
    def __init__(self, design, n, theta_max=85, radius_extra=0):
        self.design = design
        vertices, faces, self.normals, self.areas = geometry(design['rotation'])
        self.samples = sample_faces(faces, n)
        self.n = n
        self.radius = 2*RADIUS + HEIGHT*math.tan(math.radians(theta_max)) + radius_extra
        self.planes = np.vstack([self.normals, [0, 0, -1]])
        offsets = np.r_[self.normals[:, 2]*HEIGHT, 0]
        self.numerators = []
        self.centers = []
        self.clearance = math.inf
        for own in np.array(design['motif']):
            centers = neighbors(design, own, self.radius)
            self.clearance = min(self.clearance, polygon_clearance(vertices[:3, :2], centers))
            relative = self.samples[:, :, None, :] - centers[None, None, :, :]
            self.numerators.append(offsets - relative@self.planes.T)
            self.centers.append(centers)

    def response(self, direction):
        den = self.planes@direction
        plus, minus, parallel = den > 1e-11, den < -1e-11, abs(den) <= 1e-11
        cosine = np.maximum(self.normals@direction, 0)
        outputs = []
        for numerator in self.numerators:
            visible = np.ones(3)
            for face in np.flatnonzero(cosine > 1e-12):
                num = numerator[face]
                t_enter = np.max(num[..., minus]/den[minus], axis=-1) if minus.any() else np.full(num.shape[:2], -np.inf)
                t_exit = np.min(num[..., plus]/den[plus], axis=-1) if plus.any() else np.full(num.shape[:2], np.inf)
                hit = (t_exit >= np.maximum(t_enter, 1e-9))
                if parallel.any():
                    hit &= np.all(num[..., parallel] >= -1e-10, axis=-1)
                visible[face] = np.mean(~np.any(hit, axis=1))
            outputs.append(self.areas*cosine*visible)
        return np.array(outputs)


def direction(theta, phi):
    t, p = np.radians([theta, phi])
    return np.array([math.sin(t)*math.cos(p), math.sin(t)*math.sin(p), math.cos(t)])


def integrate(values, theta=THETA):
    # values: theta x azimuth. Projected response already contains cosine.
    quadrature = getattr(np, 'trapezoid', np.trapz)
    return 2*math.pi*quadrature(values.mean(axis=1)*np.sin(np.radians(theta)), np.radians(theta))


def cone_interval(curve, threshold):
    first = np.flatnonzero(curve < threshold-1e-10)
    if not len(first):
        return [float(THETA[-1]), None]
    i = int(first[0])
    return [float(THETA[max(0, i-1)]), float(THETA[i])]


def calculate(key, n):
    started = time.perf_counter()
    model = RayModel(DESIGNS[key], n)
    channels = np.empty((len(THETA), len(PHI), len(model.numerators), 3))
    isolated = np.empty((len(THETA), len(PHI)))
    for it, theta in enumerate(THETA):
        for ip, phi in enumerate(PHI):
            v = direction(theta, phi)
            channels[it, ip] = model.response(v)
            isolated[it, ip] = np.sum(model.areas*np.maximum(model.normals@v, 0))
    total = channels.sum(-1).mean(-1)
    normalized = total/BASE_AREA
    loss = 1-total/isolated
    upper = CELL_AREA*np.cos(np.radians(THETA))[:, None]
    energy_excess = float(np.max(total-upper))
    isolated_error = float(np.max(abs(isolated[THETA <= 60]-BASE_AREA*np.cos(np.radians(THETA[THETA <= 60]))[:, None])))
    assert isolated_error < 1e-10
    assert np.allclose(total[0], BASE_AREA)
    # Per-face projected response >= half its own face-normal maximum.
    per_face_solid = np.array([[integrate((channels[:, :, m, f]/model.areas[f] >= .5).astype(float)) for f in range(3)] for m in range(len(model.numerators))])
    # Solid angle where every channel passes half its zenith response.
    all_three = np.min(channels/model.areas[None, None, None, :], axis=(2, 3)) >= .5*math.cos(math.radians(30))
    summary = dict(label=DESIGNS[key]['label'], subdivisions=n, samples_per_face=n*n,
                   clearance_mm=model.clearance, neighbor_counts=[len(c) for c in model.centers],
                   normalized_diffuse_0_85=integrate(total)/(math.pi*CELL_AREA),
                   half_response_cone_deg=cone_interval(normalized.min(1), .5),
                   weakest_facet_half_peak_solid_angle_sr=float(per_face_solid.min()),
                   mean_facet_half_peak_solid_angle_sr=float(per_face_solid.mean()),
                   all_channels_half_zenith_solid_angle_sr=integrate(all_three.astype(float)),
                   energy_bound_excess_mm2=energy_excess, isolated_error_mm2=isolated_error,
                   elapsed_seconds=round(time.perf_counter()-started, 3), selected_angles={})
    for angle in [30, 45, 60, 65, 70, 75, 80, 85]:
        it = int(np.flatnonzero(THETA == angle)[0])
        summary['selected_angles'][str(angle)] = dict(mean=float(normalized[it].mean()), worst=float(normalized[it].min()), best=float(normalized[it].max()), mean_shadow_loss=float(loss[it].mean()), worst_shadow_loss=float(loss[it].max()))
    print(json.dumps({'design': key, **summary}, ensure_ascii=True), flush=True)
    return dict(summary=summary, total_mm2=total.tolist(), isolated_mm2=isolated.tolist(), channels_mm2=channels.tolist())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--subdivisions', type=int, default=8)
    parser.add_argument('--designs', nargs='+', default=list(DESIGNS))
    args = parser.parse_args()
    results = dict(model='Opaque periodic pyramids; ideal cosine-sensitive side faces; collimated illumination', units='mm, degrees, steradians',
                   parameters=dict(base_side_mm=SIDE, height_mm=HEIGHT, facet_tilt_deg=30, cell_area_mm2=CELL_AREA, base_area_mm2=BASE_AREA, fill_fraction=BASE_AREA/CELL_AREA, theta_deg=THETA.tolist(), phi_deg=PHI.tolist()), designs=DESIGNS, results={})
    for key in args.designs:
        results['results'][key] = calculate(key, args.subdivisions)
        (ROOT/f'results-n{args.subdivisions}.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
