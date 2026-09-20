# AGENTS.md — ChemSpec Workbench / Spectrum Family (hard rules)

These rules bind humans and coding agents. Prefer under-claiming.

## Never

1. **No compound-ID claims.** Do not say the software “identifies,” “matches a library,”
   or “tells you what the sample is” unless a reviewed, cited library feature is
   Implemented **and** STATUS.md says so. Synthetic fixtures are not real compounds.
   **LabRF does not identify chemicals via RF.**
2. **No Planned-as-Done.** If it is not tested or demoed, it is Planned. Update STATUS.md.
3. **No hardware / NMR / live RTL claims** without a hardware-verified STATUS row and
   named capture log. Mock IQ / synthetic fixtures are not live RF.
4. **No clinical / regulated diagnostic language.**
5. **Do not oversell JCAMP.** Basic `.jdx`/`.dx` ingest via MIT `jcamp` is Implemented;
   do not claim multi-block / vendor certification / compound ID unless STATUS says so.
6. **Do not replace synthetic fixtures with unlabeled “real” spectra** without Chemistry review.
7. **Do not rewrite `spectrum_core` inside the UI** — call ingest / peaks / baseline / overlay
   (LabRF: `iq_to_spectrum` → `Spectrum` / `find_peaks` / waterfall buffer).
8. **LabRF is receive-only.** No transmit, no TX helpers, no amplifier drive paths.
9. **Educational presets are not regulatory advice.** Never claim FCC/Ofcom compliance,
   “legal to monitor,” or certified EMI testing from LabRF presets or UI copy.
10. **No demodulation / decryption claims** in LabRF Phase 1 (power spectrum + waterfall only).

## Always

1. **CSV-first** for ChemSpec. Primary ingest path remains CSV with explicit column mapping;
   JCAMP is an additional basic adapter (`ingest_jcamp`).
2. **Honest units.** Store and display `nm` / `cm-1` / `Hz` / `MHz` and
   `A` / `percent_T` / `intensity` / `dB` correctly.
3. **Label synthetics.** Fixture README and plot titles must say synthetic.
4. **Keep `spectrum_core` reusable** — no ChemSpec-only assumptions baked into the model.
5. **Tests for ingest / peaks / baseline** (and LabRF mock FFT) must stay green before claiming those features.
6. **Follow Project Truth** — feelings we protect beat feature greed.
7. **UI is optional.** Core + CLI/matplotlib demos must run without `pip install -e ".[ui]"`.
8. **Advanced baselines are optional.** Polynomial must work without `pip install -e ".[baselines]"`; pybaselines is BSD-3 — note the license; never imply baseline correction identifies compounds.
9. **LabRF hardware is optional.** Mock IQ mode must work without `pip install -e ".[labrf]"` / dongle; CI must not require RTL-SDR.

## Preferred stack notes

- Python + numpy/scipy; matplotlib for offline plots
- NiceGUI + Plotly for interactive UIs (`[ui]` extra); demos must run without them
- Optional `pybaselines` (`[baselines]` extra, BSD-3) for AsLS / MPLS; polynomial remains default
- Optional `pyrtlsdr` (`[labrf]` / `[rtlsdr]` extras) behind a protocol; mock backend default
- Prefer fixing tests over deleting them

## When unsure

Under-claim, add a Planned row to STATUS.md, and ask Chemistry / JARTH for gates.
