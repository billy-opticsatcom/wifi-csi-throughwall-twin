# Research framework

This document describes *how* the study was carried out: how the problem was decomposed, how each design
question was answered, and how the results were verified. Numerical values and implementation details
are withheld; see the [README](../README.md#what-is-public-and-what-is-withheld).

## 1. Start from requirements, not from a design

Before each test, the study fixed measurable acceptance criteria and wrote them into a dated
pre-registration, together with its own predictions. Each criterion is a number with a tolerance:

| Area | Criterion (form) |
|---|---|
| Channel physics | Simulated Doppler follows the walker's kinematics and never exceeds 2v/λ |
| Receiver model | The 8-bit quantisation floor matches its closed-form value within a stated tolerance |
| Motion detection | False-alarm rate below a ceiling and detection rate above a floor, on held-out routines |
| Breathing / occupancy | Same form, with the bedroom empty but another person active elsewhere |
| Localisation | Share of walking moments placed in the right room or zone, false rooms per step, position error below a room-centre baseline |
| Real-data check | Numeric predictions for public recordings (signal level, empty-room spread, Doppler bound, detection through walls) |
| Robustness | Criteria still met after injecting measured real-world variability, with a stated drift margin |
| Controls | With no injection, the code reproduces the earlier result exactly |

Vague goals such as "detects breathing" were deliberately avoided: a requirement the code cannot test is a
requirement nobody can verify.

## 2. Decompose into design questions

The study was split into six milestones (see the table in the README). Each reads only the verified
outputs of earlier milestones, and each was approved by the project owner before the next started. This
keeps errors local: a receiver-model mistake is caught in milestone 2, not discovered later as an
unexplained detector failure.

## 3. Model the environment as a digital twin

- **Scene.** Walls and flat surfaces are single planes carrying their thickness in the radio material, as
  the ray tracer expects; every object maps to a material valid at 2.4 GHz; switchable doors exist in both
  states.
- **Occupants.** Articulated bodies posed by writing vertices each time step, driven by motion tables.
  Routines are generated randomly (path planning around furniture, chores including slow hand work that
  deliberately overlaps the breathing band) so detectors face many situations, not one script.
- **Channel.** Per-link, per-subcarrier, per-packet ray tracing on the GPU with diffuse body scattering,
  chosen by an A/B test against measured Doppler accuracy.
- **Receiver and environment.** A commodity-chip model and interference sources are applied on top, with
  independent random seeds, so the same scene can be judged over many noise realisations.

## 4. Treat physics and simulator identities as tests

Alongside the acceptance criteria, known results are asserted, for example:

- Doppler shift from a moving reflector is bounded by twice its speed over the wavelength.
- The quantisation noise of an 8-bit receiver held at a fixed level follows a closed-form expression.
- A frozen scene traced twice must give the same channel; a path that flips between identical solves points
  to coincident surfaces (a bug that was found this way and fixed).
- Single-antenna amplitude processing cannot recover the sign of the Doppler shift; a two-chain ratio can.
- Removing the injected disturbance reproduces the un-injected result exactly (control runs).

## 5. Record every design change with its evidence

Several assumptions did not survive testing. Each change was written down with the observation, the
experiment that resolved it and the resulting rule, and every change to a pre-registered plan went into a
dated amendment before the affected data were opened. The questions that drove the most important
decisions were:

1. **Receiver level.** At what signal level do real commodity chips actually operate, and what does that do
   to slow, millimetre-scale breathing motion?
2. **One chain or two.** What does a second receive chain on the same card buy, and what must it share for
   the ratio to work?
3. **Spatial contrast.** How can a detector distinguish motion in the bedroom from motion elsewhere when
   both disturb the same links?
4. **Breathing versus activity.** Can any feature separate breathing in bed from slow movement elsewhere in
   the home, or does breathing need a quiet home?
5. **Selection rules.** How must a model-selection rule be written so that it cannot pick the weakest
   candidate by satisfying a constraint by a hair?
6. **Simulator trust.** Which simulated effects are physical and which are artefacts of the ray tracer, and
   which claims therefore need real data?

The answers, and the experiments behind them, are part of the withheld material.

## 6. Compare against baselines, never in isolation

| Topic | Compared |
|---|---|
| Receiver | Ideal receiver, sanitised ideal, commodity chip without quantisation, full commodity chip |
| Breathing processing | Single-subcarrier, subcarrier averaging, PCA, link fusion, two-chain ratio, conjugate product |
| Motion contrast | Single-room energy, spatial contrasts between rooms, multi-link contrasts |
| Breathing / occupancy | Spectral-line detectors, activity-gated detectors, signal-strength shadowing |
| Localisation | Physics (geometric) model, signature model, fingerprint (nearest-neighbour) model, per-zone classifier |
| Environment | Clean home, home with oven, traffic and chain drift, injected real empty-building variability |

## 7. Experimental protocol

- **Pre-registration.** Method, criteria and predictions committed before the data they judge existed.
- **Held-out routines.** Detectors are designed on development routines (with routine-wise
  cross-validation) and tested once on fresh routines; used test sets are marked spent and never reused.
- **Frozen rules.** Thresholds and models are frozen and stored before any test file is opened.
- **Multiple seeds.** Receiver noise is random; every result is pooled over many seeds, never judged on one.
- **Honest intervals.** Wilson 95 % intervals over physical units (routine, door state, time step, person),
  not over correlated windows.
- **External check.** Public real recordings are parsed only after numeric predictions for them are fixed.

## 8. Known limitations

One simulated flat, one router position and a fixed set of devices; synthetic occupants with simple body
geometry; geometric-optics ray tracing that does not model near-grazing diffraction reliably and
exaggerates some broadband effects; a receiver model calibrated on public logs from one chip family; real
data from one office building with one person and one receive chain. Breathing, two-chain processing,
multi-person behaviour and bed occupancy are not validated on real home data. A short real recording in a
home (empty, walking, lying at several bed positions) with a two-chain receiver defines the next step of the
research.
