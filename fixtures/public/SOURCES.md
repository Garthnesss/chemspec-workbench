# Public chem spectrum fixtures — sources & licenses

These JCAMP-DX files are **real measured spectra** redistributed from the
[NIST Chemistry WebBook](https://webbook.nist.gov/chemistry/) (SRD 69).
They are **not** ChemSpec synthetic demos.

**Honesty:** ChemSpec Workbench / `spectrum_core` make **no compound-identification
claims** from these (or any) spectra. Filenames and titles mirror NIST labels for
provenance only; loading a file labeled “Ethanol” does not mean ChemSpec identified
ethanol.

**Do not bundle Coblentz Society spectra** (all rights reserved). None of the files
below are Coblentz collection spectra.

Retrieval date (America/Los_Angeles): **2026-09-19**.

---

## Common NIST attribution & disclaimer

Data from NIST Standard Reference Database 69: NIST Chemistry WebBook.

The National Institute of Standards and Technology (NIST) uses its best efforts to
deliver a high quality copy of the Database and to verify that the data contained
therein have been selected on the basis of sound scientific judgment. However, NIST
makes no warranties to that effect, and NIST shall not be liable for any damage that
may result from errors or omissions in the Database.

Customer support: data@nist.gov (NIST Standard Reference Data products).

WebBook pages also carry U.S. government / NIST site notices; see each compound URL
and [NIST copyright / fair-use / licensing for SRD](https://www.nist.gov/open/copyright-fair-use-and-licensing-statements-srd-data-software-and-technical-series-publications).

JCAMP download pattern used:
`https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=<ID>&Index=<n>&Type=IR`

---

## Fixtures

### `ethanol_ir_pnnl.jdx`

| Field | Value |
|-------|--------|
| Compound (NIST title) | Ethanol |
| CAS | 64-17-5 |
| Technique | IR (condensed / liquid); PNNL n/k composite JCAMP |
| Spectrum page | https://webbook.nist.gov/cgi/cbook.cgi?ID=C64175&Index=29&Type=IR-SPEC&Units=SI |
| JCAMP URL | https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C64175&Index=29&Type=IR |
| Owner / license (quote from file/page) | **Owner: Public domain** |
| Origin (quote) | Pacific Northwest National Laboratory Under IARPA Contract |
| Notes | Multi-block JCAMP (`dispersion index` + `absorption index`). Ingest via MIT `jcamp` typically exposes the absorption-index block as intensity. |

### `methanol_ir_pnnl.jdx`

| Field | Value |
|-------|--------|
| Compound (NIST title) | Methanol (Methyl Alcohol) |
| CAS | 67-56-1 |
| Technique | IR (liquid); PNNL n/k composite JCAMP |
| Spectrum page | https://webbook.nist.gov/cgi/cbook.cgi?Contrib=IARPA-IR-L&ID=C67561&Index=0&Type=IR-SPEC |
| JCAMP URL | https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C67561&Index=28&Type=IR |
| Owner / license (quote from file/page) | **Owner: Public domain** |
| Origin (quote) | Pacific Northwest National Laboratory Under IARPA Contract |
| Notes | Same multi-block PNNL layout as ethanol. |

### `toluene_ir_pnnl.jdx`

| Field | Value |
|-------|--------|
| Compound (NIST title) | Toluene |
| CAS | 108-88-3 |
| Technique | IR (liquid); PNNL JCAMP |
| Spectrum page | https://webbook.nist.gov/cgi/cbook.cgi?Contrib=IARPA-IR-L&ID=C108883&Index=0&Type=IR-SPEC |
| JCAMP URL | https://webbook.nist.gov/cgi/cbook.cgi?JCAMP=C108883&Index=29&Type=IR |
| Owner / license (quote from file/page) | **Owner: Public domain** |
| Origin (quote) | Pacific Northwest National Laboratory Under IARPA Contract |
| Notes | Downloaded file is a single `dispersion index` (real refractive index) block; stored as intensity by ingest. |

---

## Not included (license)

- **Coblentz Society** IR spectra on WebBook: owner text includes “All rights reserved” — **not** redistributed here.
- **Acetone / water:** no PNNL/IARPA **Public domain** IR JCAMP was available for acetone (CAS 67-64-1) or water at retrieval time under the same Owner=Public domain pattern; EPA/Sadtler gas-phase acetone is NIST SRD (“All rights reserved” U.S. Secretary of Commerce notice) and was deliberately omitted to keep this folder public-domain-only.
- Open UV-Vis JCAMP with equally clear public-domain labeling was not located for these compounds at retrieval time; UV-Vis demos remain synthetic under `fixtures/`.

