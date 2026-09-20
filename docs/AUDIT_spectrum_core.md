# Audit notes — spectrum_core (ChemSpec 0.2 Measurement Integrity)

File-by-file notes while shipping peak contract / session identity / op preconditions.
Honesty: no compound ID; no hardware overclaims. Larger items stay here or in STATUS;
small fixes landed in the same PRs when safe.

| Module | Findings | Disposition |
|--------|----------|-------------|
| peaks.py | Semantics were already prominence-relative (SciPy peak_widths style) but not explicit on Peak. Area uses real x spacing via trapezoid. | Fixed (PR #35): contract fields + docs/tests (slope case, uneven dx, descending IR). |
| export_peaks.py | CSV lagged contract fields. | Fixed (#35). |
| session.py | format_version 1 had no computational identity; session_from_dict ignored migrate return (would have dropped v1→v2 upgrades). | Fixed (#36): v2 hashes + fingerprint; migrate wired into session_from_dict. |
| processing.py | Preconditions existed as bare ValueError; messages uneven; despike lacked window > n check; baseline degree vs length only inside baseline_polynomial. | Fixed (this PR): ProcessingError + clearer scientific messages; despike length check; baseline degree/length precheck in op_baseline. |
| baseline.py | Polynomial NaN-safe via finite mask; pybaselines path requires all-finite (documented). Unknown method / bad inputs → ProcessingError. | Fixed: bare ValueErrors wrapped as ProcessingError (still ValueError subclass). |
| ingest.py | Large; edge fixtures exist. JCAMP unit aliases for log10(ε) documented. | Larger (deferred): advanced JCAMP multi-block / DIFDUP still Planned; no silent unit auto-flip (good). |
| units.py | Intensity blocked from A↔%T — correct honesty. | OK. |
| folder.py / overlay.py | Stack offsets only; x_unit mismatch raises. | OK / Planned: richer time-axis metadata still Planned. |
| export_png.py | Honesty footer present. | OK. |
| spectrum.py | Minimal validation; empty rejected. | OK. |
| errors.py | New shared hierarchy. | Added (this PR). |

## Larger follow-ups (not blocking 0.2 MI)

1. UI replay of history on session load is still caller-driven (session stores raw + history); document UX if users expect auto-replay.
2. Peak table UI shows contract columns but not the full baseline_reference_note (CSV/session do).
3. ~~baseline_correct bare ValueError~~ — Fixed: raises ProcessingError; ImportError for missing pybaselines unchanged.
4. Units live in analysis_fingerprint, not raw_data_hash (arrays-only hash by design) — document for callers.
