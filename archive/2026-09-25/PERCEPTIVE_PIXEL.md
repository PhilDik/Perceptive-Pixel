# Perceptive Pixel: Angularly Diverse Sensing in a Bidirectional Display

Conceptual research manuscript · 25 September 2026

## Abstract

This manuscript describes a proposed display architecture in which each purpose-built optoelectronic pixel can emit light and provide several independently readable optical responses. Differently oriented or optically structured regions are intended to encode complementary angular information. An array of these pixels would combine calibrated measurements, controlled illumination and registered device motion for computational scene estimation. A three-facet pixel and alternating triangular layout are candidate implementations. An optional temporal representation would preserve relatively stable object shape while updating pose, visibility and uncertain geometry. We define the measurement quantities, distinguish passive acquisition from active reflection sensing, and identify restrictions imposed by light-return timing, photon collection, crosstalk, readout and inverse-problem ambiguity. Close precedents already combine displays with lensless light-field acquisition; the general combination is not presented as established novelty. Whether a particular multi-region reversible pixel improves reconstruction at a fixed resource budget remains an open hypothesis. No fabricated pixel, validated optical simulation, trained reconstruction system or experimental advantage is reported.

## 1. Scope and research question

The original Screen Scanner concept treats a display as both an emitting surface and a source of optical measurements. The Perceptive Pixel extension adds multiple separately readable regions within an individual display pixel. The intended contribution is additional physical measurement diversity before reconstruction, not a pixel that directly outputs depth.

The research question is whether a specified multi-region bidirectional pixel, acquisition schedule and array layout can improve scene estimation sufficiently to justify their costs relative to simpler sensing surfaces. The complete system includes the optical stack, independent electrical readout, calibration, illumination, device pose, temporal state and reconstruction. Selecting three facets alone does not define that system.

The proposal requires purpose-built hardware. It does not assume that an existing display provides independently accessible photocurrents, suitable spectral sensitivity or sufficiently fast switching. Emission and detection by one device must each be characterized in their respective operating states.

## 2. Pixel and matrix organization

Let p identify a display pixel and k one of its K sensing regions. During display operation the regions contribute to the visible output. During reception they provide separate measurements y[p,k,t]. Independent electrical channels are necessary, but are not sufficient to make their information independent: their optical response functions must differ in useful, calibrated ways.

Possible realizations include tilted facets and optically structured regions with different angular weighting. A triangular footprint does not by itself establish three tilted sensing surfaces. Surface normals, exposed areas, spectral response, contacts, occlusion, cover-layer refraction and optical isolation all remain to be specified.

K = 1, 3 and 4 are useful comparison cases. Three regions may use fewer readout channels than four at the same sample rate and precision, but this does not establish lower total system cost or adequate depth information. An alternating triangular array could change direct neighbor coupling and angular coverage; it could also reduce collection in useful directions. Its net effect is unknown.

The functional flow is:

```text
illumination / display schedule + receiver assignment + measured display pose
                                  |
                                  v
           calibrated multi-region optical measurements
                                  |
                                  v
       background and coupling model + uncertainty estimation
                                  |
                                  v
       joint estimation across regions, pixels and device poses
                                  |
                                  v
            scene state / optional persistent object model
```

## 3. Forward measurement model

For an incoherent intensity-detection model, an expected detector reading can be written schematically as

\[
\mu_{pkt}=\int_{T_t}\!\int_\lambda\!\int_\Omega
 R_{pk}(\omega,\lambda;q_t)\,L_{\mathrm{scene}}(p,\omega,\lambda,\tau;G,\rho,e_t)\,
 d\omega\,d\lambda\,d\tau + C_{pkt}(e_t)+B_{pkt}.
\]

Here R is calibrated responsivity, including effective collection area and stack transmission; q is display pose; G is scene geometry; rho denotes material scattering properties; e is the illumination schedule. C represents direct/internal emitter-to-receiver coupling and B represents ambient and dark contributions. Measured y additionally contains photon and readout fluctuations. Time-dependent transport in L must include emission timing and the propagation path when that timing matters.

This is a bookkeeping model, not a solved transport equation or a validated device model. It makes the missing specifications explicit. A receiver without angular encoding integrates contributions from many scene directions. Its coordinate on the display is not automatically a coordinate in a focused scene image. Several broad angular integrals also do not constitute an unrestricted measurement of the complete light field.

Color requires characterized spectral channels. Direct intensity detection does not automatically measure optical carrier phase or resolve arbitrary optical frequencies. Modulation-envelope phase or time-of-flight requires a specified transmitter, clock, detector bandwidth and demodulation/gating mechanism. These capabilities cannot be inferred from the ability to blink or change display color.

## 4. Emission and acquisition timing

Passive reception can occur while the surface is not emitting if external illumination continues. Active reflection sensing requires the receiver to be sensitive when the emitted light returns.

For a near-normal monostatic path to a target at distance z in air, the approximate round-trip delay is 2z/c. At 0.1, 0.5, 1 and 2 metres this is approximately 0.67, 3.34, 6.67 and 13.34 nanoseconds. Other source-target-receiver geometries use their actual total path length. These elementary timing values do not predict achievable sensing range.

Consequently, ordinary frame-scale switching of the entire display from illumination to reception will miss the prompt return of an earlier pulse from a nearby non-persistent reflector. Exposure duration does not store light that arrived while a detector was insensitive. Fluorescence or other persistent responses would require a different, explicitly justified scene model and are not assumed here.

Two physically distinct scheduling options require evaluation:

1. **Spatial interleaving.** Some complete pixels emit while others receive the reflected signal; all regions of each receiving pixel are read independently, and later intervals exchange pixel roles. Each pixel can remain bidirectional over the complete sequence. Illumination coding and receiver timing must be synchronized, and direct coupling is present during acquisition.
2. **Fast pulse and gate.** A receiver becomes sensitive within a justified return window after emission. Pulse duration, switching recovery, detector bandwidth and saturation must be specified. This is an additional hardware requirement, not a capability established for the proposed pixel.

Spatial interleaving is an implementation option already known in prior work [5]. Introducing it here resolves an under-specified measurement schedule; it is not a new contribution. A prototype must choose and model its actual schedule before any claim about active depth is meaningful. Temporal separation at the display level alone does not solve active-return collection and crosstalk simultaneously.

## 5. Depth, motion and identifiability

Unknown reflectance, surface orientation, occlusion and ambient illumination can imitate changes in distance. For example, a simplified single-location observation of one unresolved isotropic source can have the form

\[
y_k=\alpha r^{-2}\max(0,\mathbf n_k\cdot\mathbf u).
\]

Even if sufficiently distinct normals determine direction u, unknown source strength alpha remains coupled to range r. Doubling r and multiplying alpha by four leaves every channel unchanged. This illustrative counterexample does not describe the full active system; it shows why three intensity channels do not intrinsically supply metric depth.

Measurements from separated pixels and known device translations can add constraints. Useful range estimation still requires an adequate baseline, calibrated directional response, sufficient photons, correspondence or an appropriate joint scene model, and distinguishable scene responses. Device rotation alone does not guarantee useful triangulation of unknown range. Moving objects also require separating object motion from display motion.

For a specified forward model F(theta), the sensitivity matrix J = dF/dtheta can reveal local degeneracies and poorly constrained parameter combinations after nuisance parameters are included. More rows improve observability only if they carry complementary information at adequate signal-to-noise ratio. Full local rank is not a proof of globally unique reconstruction. Singular-value or uncertainty analysis must accompany reconstruction quality when evaluating a future model.

The proposed system should therefore report supported geometry, uncertainty and failure cases. Neither motion nor a learned prior guarantees recovery in every scene.

## 6. Temporal object model and learned reconstruction

An optional hand/finger interaction mode maintains an object state across observations. Relatively stable shape can be retained while position, orientation, articulation and visibility change. New registered measurements update geometry where they add evidence, rather than requiring a complete shape estimate from every frame.

In generic terms, the prior state is propagated by a motion model, then revised using the new optical observations and their uncertainty. The representation must permit previously unseen surfaces, model mismatch, entry of a different object, tracking loss and reinitialization. A predicted continuation behind an occlusion is not a fresh measurement.

A learned reconstruction function can be trained against independently obtained reference geometry. In the proposed operating description, new observations update the scene state; online modification of model weights is not required. Training data, held-out objects and the model itself do not yet exist for this proposed device. A plausible hand-shaped output cannot establish that the measured data contained enough information to identify its depth.

## 7. Photon, electrical and optical budgets

Dividing fixed effective sensitive area into K regions does not multiply the collected photons by K. Region signals may become weaker, and separate readouts can add noise and wiring overhead. Distinct angular responses may nevertheless make the available photons more informative for a particular task. That trade-off requires quantitative comparison.

At fixed pixel count N, sampling rate f and word length b, raw readout scales as N K f b before metadata and processing. Three regions require three times the channel payload of one and three quarters of four under those assumptions. At fixed total bandwidth, increasing K instead forces a trade in spatial samples, sample rate, precision or compression. Both optical and communication budgets must be stated.

Alternating orientations, barriers and stack design can change internal coupling, but subtraction of its mean does not remove the photon shot noise it produces. Saturation, drift and imperfect calibration can make subtraction ineffective. Internal reflections, optical guiding in cover layers and electrical coupling also require characterization.

Display brightness, angular appearance, fill factor, sensing duty cycle, heat and readout energy belong in the system budget. A geometry that improves a reconstructed image while collecting more light, using more acquisition time or reducing display quality has not yet shown an advantage at matched resources.

## 8. Closest prior work and limits of the contribution

Reversible LED sensing is established at the component level [1]. BiDi Screen demonstrated display-associated lensless angular sampling and depth-aware interaction [2]. Angle-sensitive pixel arrays demonstrated optical angular encoding [3]. These precedents preclude attributing the broad ideas of display reception, lensless spatial inference or angularly informative pixels to this proposal.

A particularly close patent disclosure is **US9626023B2**, first published in its application form in 2012 [4]. Independent claim 1 describes an OLED array, optical vignetting that produces different incoming light-field samples at individual OLEDs, detection intervals, an emitting arrangement and processing. Dependent claim 2 identifies the emitting devices as OLEDs of that array. Its description discusses using a common array for display and lensless acquisition. Thus, even the general combination of a reversible display array and angularly differentiated sensing has a close earlier disclosure. These claim references describe the cited document; they do not establish a legal conclusion about a proposed device.

US7598949B2 describes interleaved emitting and sensing LEDs for observing reflected/scattered light [5]. It is relevant to the physically workable acquisition schedule as well as to prior art. OrbCam supplies another comparison for lensless imaging with differently oriented detector pixels [6], although its demonstrated architecture should not be equated with this proposed reversible display.

The remaining research hypothesis is narrower: a concretely specified pixel containing multiple independently read regions, together with its layout, calibration and acquisition schedule, might improve estimation per unit resource. The selected sources do not establish that a three-facet alternating reversible display has already been implemented exactly as proposed. Absence of that exact match in a limited review also does not establish novelty. No claim of a first implementation, patentability or measured superiority is made.

## 9. Future evaluation criteria

The following sequence defines future validation; it is not a report of completed experiments.

1. Specify surface geometry, optical stack, angular and spectral responses, detector noise, independent contacts and a physically valid emission/reception schedule. Check that source spectra overlap detector sensitivity and that receive recovery permits the selected schedule.
2. Form the forward model including scene transport, direct coupling, ambient light, unknown materials and pose uncertainty. Seek ambiguous scene pairs before optimizing reconstruction.
3. Compare one-, three- and four-region geometries under the same display footprint, total sensitive area, emitted energy, acquisition duration, trajectory and task. Report projected aperture and actual detected photons: equal material area need not imply equal throughput. Include both equal per-channel precision and equal total readout-budget comparisons.
4. Separate the effects of angular regions, array alternation, active coding, motion and temporal state. Include a single-region baseline, the sum of multi-region outputs, and a non-oriented subdivision baseline to distinguish angular information from additional readouts.
5. Evaluate depth/shape error, failure rate, uncertainty calibration, robustness to unfamiliar reflectance and motion, crosstalk, photons, time, bandwidth and energy. For the hand mode, include new hands, changing articulation, occlusion and loss of tracking.
6. Retain the proposed geometric advantage only if it persists under matched resources and independent scenes. If different channels are redundant, or improvement disappears after accounting for collection area and bandwidth, the corresponding claim should be withdrawn or narrowed.

No dimensions, sensing distance, resolution, frame rate or power target can yet be stated as a demonstrated device capability.

## 10. Conclusion

Perceptive Pixel is an unvalidated system architecture for acquiring multiple optical responses per display pixel and combining them across space, illumination and time. Its scientific value currently lies in a testable implementation question. A defensible description must preserve the full system while separating angular measurement from depth inference, active return capture from display switching, and a proposed geometry from an established advantage.

## References

1. Dietz, Yerazunis and Leigh, *Very Low-Cost Sensing and Communication Using Bidirectional LEDs* (2003). [MERL author report](https://www.merl.com/publications/docs/TR2003-35.pdf).
2. Hirsch, Lanman, Holtzman and Raskar, *BiDi Screen: A Thin, Depth-Sensing LCD for 3D Interaction using Light Fields* (2009). [Author manuscript and publication record](https://dspace.mit.edu/entities/publication/0f809c3e-b842-4784-8302-217860d795f9).
3. Wang, Gill and Molnar, *Light field image sensors based on the Talbot effect* (2009). [Full research article](https://pmc.ncbi.nlm.nih.gov/articles/PMC2892475/).
4. Ludwig, *LED/OLED array approach to integrated display, lensless-camera, and touch-screen user interface devices and associated processors*. [US9626023B2](https://patents.google.com/patent/US9626023B2/en); [application publication US20120006978A1](https://patents.google.com/patent/US20120006978A1/en) (2012).
5. *Multi-touch sensing light emitting diode display and method for using the same*. [US7598949B2](https://patents.google.com/patent/US7598949B2/en) (2009).
6. Hua, Zhao and Sankaranarayanan, *Angle Sensitive Pixels for Lensless Imaging on Spherical Sensors* (2023), describing OrbCam. [Author preprint](https://arxiv.org/html/2306.15953v1).
