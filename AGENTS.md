# AGENTS.md — ChemSpec Workbench (hard rules)

These rules bind humans and coding agents. Prefer under-claiming.

## Never

1. **No compound-ID claims.** Do not say the software “identifies,” “matches a library,”
   or “tells you what the sample is” unless a reviewed, cited library feature is
   Implemented **and** STATUS.md says so. Synthetic fixtures are not real compounds.
2. **No Planned-as-Done.** If it is not tested or demoed, it is Planned. Update STATUS.md.
3. **No hardware / NMR / RTL claims** in Phase 0 marketing copy or README badges.
4. **No clinical / regulated diagnostic language.**
5. **Do not oversell JCAMP.** Basic `.jdx`/`.dx` ingest via MIT `jcamp` is Implemented;
   do not claim multi-block / vendor certification / compound ID unless STATUS says so.
6. **Do not replace synthetic fixtures with unlabeled “real” spectra** without Chemistry review.
7. **Do not rewrite `spectrum_core` inside the UI** — call ingest / peaks / baseline / overlay.

## Always

1. **CSV-first.** Primary ingest path remains CSV with explicit column mapping;
   JCAMP is an additional basic adapter (`ingest_jcamp`).
2. **Honest units.** Store and display `nm` / `cm-1` and `A` / `percent_T` / `intensity` correctly.
3. **Label synthetics.** Fixture README and plot titles must say synthetic.
4. **Keep `spectrum_core` reusable** — no ChemSpec-only assumptions baked into the model.
5. **Tests for ingest / peaks / baseline** must stay green before claiming those features.
6. **Follow Project Truth** — feelings we protect beat feature greed.
7. **UI is optional.** Core + CLI/matplotlib demos must run without `pip install -e ".[ui]"`.

## Preferred stack notes

- Python + numpy/scipy; matplotlib for offline plots
- NiceGUI + Plotly for the interactive MVP (`[ui]` extra); demos must run without them
- Prefer fixing tests over deleting them

## When unsure

Under-claim, add a Planned row to STATUS.md, and ask Chemistry / JARTH for gates.
