# Hardware feasibility and existing displays

Prepared 28 September 2026. This is a functional hardware assessment, not a bill of materials or a tested conversion of a commercial screen.

## A display cannot gain a missing receive path through software

For optical acquisition, incoming light must produce a measurable electrical signal, that signal must reach a readout circuit, and software must receive calibrated samples with timing and channel identity. Photosensitivity of a semiconductor alone does not establish those capabilities in an assembled display.

An ordinary liquid-crystal pixel modulates transmitted light; it is not thereby a photodetector. An emitting OLED or LED junction may have a photoresponse, but an existing panel's transistors, wiring and controller need not expose it. Reading a display framebuffer returns commanded image data, not photons arriving from the environment. A touch controller or a single ambient sensor does not establish distributed optical readout of display pixels.

## Implementation paths

| Path | What can be reused | Additional requirement | What it would demonstrate |
|---|---|---|---|
| Ordinary output-only LCD/OLED panel | Display output or calibrated illumination patterns | A receiving subsystem; the ordinary display interface is insufficient | A system experiment, not sensing by the same pixels |
| Discrete LED matrix with accessible bidirectional drive/readout | Some emitting junctions and addressing | Characterized sensing bias, noise, spectral response, timing and independent samples | A low-resolution test of dual-function acquisition |
| Integrated emitter/photodiode panel | Planar source and receiver fabrication | Access to raw receive channels and controllable schedules; calibration and spatial encoding | Integrated sensing with physically separate receivers |
| Purpose-built reversible photo-responsive panel | The same junctions for light output and input | Suitable driver/readout access and calibrated acquisition | The reversible-pixel branch of the concept |
| Added sensing/encoding layer | Existing display as carrier or illuminator | Extra optical/electrical layer and its readout | A distinct layered architecture, not a software-only conversion |

Published research already demonstrates both integrated organic photodiodes and photo-responsive perovskite emitters. The former reports electrical and optical crosstalk; its alternative sensing schedule trades scanning time for reduced optical leakage. The latter demonstrates adjacent emitter/receiver surface scanning. Neither source establishes that an arbitrary retail panel provides user-accessible raw measurements or a textured metric environment map. [Integrated panel](https://www.nature.com/articles/s44172-024-00239-8), [reversible pixels](https://www.nature.com/articles/s41928-024-01151-x).

An existing educational LED matrix provides a useful documented precedent: its runtime can switch display drive pins into sensing inputs and estimate ambient illumination from voltage decay. The public high-level interface returns one light-level value; it does not expose a calibrated scene image or per-facet depth data. This demonstrates that limited reception by an already-built LED display is practical, not that a high-resolution consumer panel is interchangeable with it. [Official hardware description](https://tech.microbit.org/hardware/), [official interface documentation](https://microbit-micropython.readthedocs.io/en/latest/display.html).

## Documented examples checked on 28 September 2026

These examples distinguish a documented physical measurement from an interface that an independent experimenter can actually access. They do not prescribe a particular supplier or establish compatibility with the facet design.

| Functional class | Documented measurement and implementation | Availability and remaining gap |
|---|---|---|
| Educational 5 × 5 LED matrix | The documented light-sensing call returns one integer from 0 to 255 using reverse-biased display LEDs. Reading a displayed pixel's brightness is a different operation and does not measure incident light at that pixel. [Scalar light-sensing interface](https://microbit-micropython.readthedocs.io/en/v2-docs/display.html) | An existing programmable board, but this interface does not provide 25 independent calibrated optical channels or a scene image. Per-pixel acquisition would require separate verification. |
| Reversible 32 × 32 perovskite LED research display | The same elements can emit or receive. Methods describe shift-register drive, switch arrays selecting pixels, and an analogue input reading photovoltage. Surface scanning uses adjacent emitting and receiving pixels. [Reversible-pixel experiment and methods](https://www.nature.com/articles/s41928-024-01151-x) | A fabricated laboratory sample with a described acquisition circuit. A retail module, public acquisition SDK and independently readable inclined regions have not been established by this source. |
| Integrated planar OLED and organic-photodiode display | A 2026 demonstration places separate RGB emitters and OPD receivers in one layer and detects the optical response to display illumination. The reported 6.8-inch panel has 500 ppi display resolution; this does not establish 500 ppi OPD sampling. [Integrated source/receiver panel demonstration](https://global.samsungdisplay.com/31450) | The announcement establishes a display demonstration, but not an independently obtainable development panel, public raw-channel interface or user-controlled sensing schedule. It does not demonstrate reception by the emitting OLED elements themselves. |
| Standalone one-dimensional photodiode array | A catalogue component provides 64 channels at 0.8 mm pitch across a 51.2 × 0.8 mm image area, simultaneous integration and sequential readout. A dedicated driver is supplied separately. [Photodiode-array readout specification](https://www.hamamatsu.com/jp/en/product/optical-sensors/image-sensor/photodiode-arrays-with-amp/S11865-64.html) | A documented receiver component, with stock and delivery unverified. It is a line array, not a two-dimensional display, and does not emit. Its catalogue page does not establish a ready computer interface or SDK. |

This bounded check has not established a commercially available complete display with an open raw-readout interface for the same LEDs across the panel. A separate planar receiver can support a limited reconstruction experiment, but its measurements cannot validate reversible LED operation or the benefit of inclined facets. Each comparison must use the measured angular response, sensitivity, noise and acquisition timing of its own hardware.

## Minimum evidence for claiming compatibility with a particular screen

Identify the physical receiver and accessible readout path in that panel's documentation. Establish raw channel access, timing, illumination control, sensitivity/noise and spectral overlap. Measure spatial/angular response and direct coupling. Then test whether those responses distinguish different scene geometries. A demonstration of brightness detection is an acquisition sanity check, not spatial reconstruction.

Ordinary diagnostic registers, display memory readback, proximity gestures, contact fingerprint detection and a camera behind the display are different capabilities. Their existence cannot be substituted for the required receiver interface. No retail model has been verified as a ready-to-use FacetSensus sensor in this package; laboratory demonstrations are not procurement or SDK-availability claims.

## Relation to the facet candidate

The reconstruction architecture can first be investigated using calibrated planar receivers. It must not depend on unverified fabrication of independently readable emitting facets. Conversely, a separate receiver experiment cannot validate the proposed reversible facets. Each path needs its own calibration, readout and optical response, with the same resource accounting in comparisons.

An extended rotating panel may add angular diversity and receiver displacement, but neither an inertial sensor nor panel rotation alone guarantees metric depth. The [reconstruction design](RECONSTRUCTION_DESIGN.md) specifies how poses, unknown regions and model mismatch should enter the proposed estimator.
