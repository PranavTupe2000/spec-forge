# 04 — Ingestion Specification

**Status:** Baseline · **Decision:** ADR-003 · **Module:** `src/spec_forge/ingest/`
**Implements:** SF-MIN-01, SF-EXT-01 · **Produces:** `SourceDocument[]` + `SourceFragment[]`

---

## 1. Contract

```
ingest(paths: list[Path], manifest: CaseManifest | None) -> IngestResult
```

`IngestResult` = `SourceDocument[]`, `SourceFragment[]`, `ProtoGraph[]`, `Diagnostic[]`.

Four rules govern every loader:

- **I1 — Never reject.** An unsupported or corrupt file produces a `SourceDocument` with
  `ingest_method: "unsupported"` and a diagnostic. It never raises, and never removes the file from the record.
  *(The PRD guarantees inputs will be arbitrary; refusing to ingest is refusing to do the job.)*
- **I2 — Never interpret.** Ingestion extracts and locates. It does not decide what a component is, which value
  wins, or what a diagram means. All judgment happens downstream in `extract/` and `evidence/`.
- **I3 — Always locate.** Every fragment carries a reproducible `locator` (`03_system_ir_spec.md` §6.2). A
  fragment that cannot be pointed at is not admissible evidence.
- **I4 — Preserve verbatim text.** Fragment `text` is the source's own words, unnormalised. Normalisation
  destroys the alias evidence that alias resolution depends on.

## 2. Supported modalities

All three committed modality groups, covering 11 file types present across the four benchmark bundles.

| Group | Types | Loader | Phase |
|---|---|---|---|
| **Text / documents** | `.pdf` `.docx` `.xlsx` `.csv` `.eml` `.md` `.txt` | `pdf.py` `docx.py` `xlsx.py` `tabular.py` `email.py` `plaintext.py` | 1–2 |
| **Structured engineering artifacts** | `.puml` `.mo` `.json` | `plantuml.py` `modelica.py` `structured.py` | 2 |
| **Images (vision)** | `.png` `.jpg`, and PDF pages with no text layer | `image.py` + `vision.py` | 2 |

## 3. Dispatch

By **content sniff first, extension second** — a `.txt` holding an email header is an email; a `.mo` is
recognised by `within`/`model` keywords regardless of extension. Order:

1. Magic bytes / zip container inspection (`.docx` and `.xlsx` are OOXML zips).
2. Content heuristics (`@startuml`, `From:`+`Subject:` headers, `within`/`model`).
3. Extension.
4. Fallback: attempt UTF-8 text decode; if it fails, mark `unsupported`.

## 4. Loaders

### 4.1 PDF — `pdf.py`

Library: **PyMuPDF**. Per page:

1. `page.get_text()`. If yield ≥ `MIN_TEXT_CHARS` (default 40), emit `pdf` fragments per text block with
   `page`, `block`, `bbox`.
2. **If yield is below threshold, the page is image-only.** Render at `render_dpi` (default 140) and route to
   the vision path (§4.9), emitting `pdf_image` fragments.
3. Extract tables with PyMuPDF's table finder; emit one fragment per table **plus** one per row, so a single
   parameter row is citable on its own.

> **This fallback is not optional.** The hackathon's own Participant Briefing is a 13-page PDF with **zero**
> extractable text — every page is a single embedded image. A loader that trusts `get_text()` returns nothing
> and reports success. Regression test: `test/unit/ingest/test_pdf_image_only.py` asserts non-empty fragments
> from an image-only PDF.

### 4.2 Word — `docx.py`

Library: **python-docx**, with a raw-XML fallback (`word/document.xml`) for files it refuses. Paragraphs →
`docx` fragments with `paragraph_index`. Tables → one fragment per row with `table`/`row`/`col`, because the
benchmark design notes carry state-transition tables and revision-sensitive value tables that must be cited
per row. Headings are retained as structure hints on fragments (`section_path`).

### 4.3 Spreadsheet — `xlsx.py`

Library: **openpyxl**, `data_only=True` to read cached formula results, plus a second pass with
`data_only=False` to capture the formula text itself as a `derivation`.

Per sheet: detect the header row (first row with ≥3 non-empty string cells, skipping title banners), then emit
**one fragment per data row** with `sheet` and `cell_range`.

Certain sheet names carry precedence metadata and are routed to the evidence layer rather than treated as plain
content. Detected by fuzzy name match, never by exact case-specific string:

| Sheet pattern | Meaning | Consumed by |
|---|---|---|
| `*Change*Log*` | Document revision history with status and precedence notes | `evidence/precedence.py` |
| `*Source*Index*` | Per-artifact reliability and known caveats | `evidence/ledger.py` |
| `*Requirement*Register*` | Requirement rows with `Status` / `Superseded By` | `extract/requirements.py` |
| `*Interface*Matrix*` | From/To port-level connection table | `extract/topology.py` — **highest-quality connection evidence available** |
| `*Operating*Parameter*` | Values with `Revision Status` / `Effective?` | `evidence/precedence.py` |

The Interface Matrix deserves emphasis: it is the only input across the bundles that states connections at
**port level** (`TK-101.outlet → XV-102.inlet`) rather than part level. It resolves the proto-connection problem
(§4.5) directly and should be preferred over diagram-derived topology whenever present.

### 4.4 Email — `email.py`

Library: stdlib `email`. **Split the thread into individual messages** — walk quoted-reply boundaries
(`-----Original Message-----`, `---- reply ----`, `On <date> wrote:`) as well as MIME parts. Decode
quoted-printable (the L1 thread is QP-encoded, with soft line breaks splitting numbers mid-token, e.g. `0.80 m`
wrapping as `0.8=\n0 m`). Emit one `email` fragment per message with its own `Date`, `From` and message index.

Per-message granularity is mandatory: a thread routinely contains a stale value and its approved replacement.
Each message inherits its own date, which the precedence engine needs.

### 4.5 PlantUML — `plantuml.py`

Deterministic parse (no LLM). Extract `component`/`rectangle`/`node` declarations with their aliases and
multi-line labels, `-->`/`..>` edges with labels, and `note` blocks.

Produces a **`ProtoGraph`**: part-level nodes and edges, explicitly **not** connections, because PlantUML
records no ports. Notes are captured as fragments and matter more than they look — every benchmark `.puml`
carries a note stating what the draft **omits** (L1: "does not show LT-101/LT-102, START/STOP/SHUT inputs, pause
state"; L3: "does not expose leakage branch, electric ground, magnetic ground"). That is direct, citable
evidence of **known incompleteness**, and feeds `OpenQuestion` generation rather than being discarded.

### 4.6 Modelica — `modelica.py`

Deterministic parse of legacy `.mo` files: `model`/`within` declarations, `parameter` declarations with value,
unit and comment, component instantiations, `connect(...)` equations, `type ... = enumeration(...)`, and
`algorithm`/`equation` section text.

**Legacy models are ingested as evidence at the lowest authority tier (T11) and are never treated as ground
truth.** Every benchmark ships a legacy `.mo` that is deliberately stale — L1's predates CR-004 and still says
`0.78`/`10`/`10`, with its own comment admitting *"SHUT handling was not completed in this revision"*; L3's
v1.0 has superseded `sigma`, `mu_r` and coil turns. They remain valuable for **topology, instance names and
port structure**, which do not go stale the way parameter values do. The loader therefore tags parameter
fragments and structural fragments distinctly (`fragment.role = "parameter" | "structure"`) so the precedence
engine can demote the former without discarding the latter.

### 4.7 Tabular data — `tabular.py`

Library: **pandas**. CSV/TSV. **Do not emit a fragment per row** — a 3000-second run at 1 Hz would flood the
evidence store and the context window. Instead emit:

- one `tabular` fragment with the **schema** (column names, dtypes, row count, time range);
- one with **summary statistics** per numeric column (min/max/mean, first/last);
- one with **detected discrete events** (state-column changes, boolean transitions) — for L1 this recovers the
  command schedule at 20/220/280/650/700 s directly from the reference trace;
- the file is registered as a **reference trace** for simulation comparison (`09_validation_and_repair_spec.md` §7),
  not as design authority.

### 4.8 Structured JSON — `structured.py`

Walk the document; emit fragments per meaningful object with a `json_path` pointer. Used for BIM room exports
(L2), geometry metrology (L3) and layout coordinates (L4). Metrology exports are candidates for
`value_kind: as_built_measurement` — never for `nominal_design`.

### 4.9 Vision — `image.py` + `vision.py`

Applies to `.png`/`.jpg` and to image-only PDF pages.

1. Preprocess: ensure ≥1500 px on the long edge, normalise to PNG.
2. Single Claude vision call per image with a **structured-output schema**, not free prose. The model returns
   `{elements[], connections[], labels[], annotations[], legend[], unreadable_regions[]}`, each element carrying
   a normalised `bbox`.
3. Each returned element becomes an `image` fragment with its bbox as locator — so a part extracted from a P&ID
   cites a *region of the drawing*, and the UI can highlight it.
4. Emit a `ProtoGraph` as in §4.5.

Rules:

- **`unreadable_regions` is mandatory output.** The model must report what it could not read. Those become
  `OpenQuestion`s, not silence. A vision pass that claims full comprehension of a scanned P&ID is the single
  most likely place for confident fabrication, and this is our structural defence against it.
- Vision-derived elements start at **`confidence ≤ 0.8`** and **authority tier T8 (diagram)**. Topology
  evidence is good; values read off a drawing are weak and must lose to any tabular or textual source.
- Vision output is **never** the sole justification for a numeric attribute value. Enforced by `V-VIS-001`.

## 5. Progress and streaming

Ingestion emits `IngestProgress` events (`file_started`, `file_completed`, `fragment_count`, `file_failed`) over
the pipeline event bus, surfaced via SSE (`12_api_spec.md` §5) and a CLI progress bar. Required by SF-UX-03 —
the PRD penalises silence, not latency.

## 6. Caching and replay

Content-addressed by `sha256` of file bytes plus loader version, cached under `build/cache/ingest/`. Vision and
LLM calls are recorded to `runs/<run_id>/llm/` as request/response pairs.

`--replay <run_id>` re-runs a case entirely from cache with **zero network calls**. This exists for the
demo slot: the briefing warns that setup comes out of our 10 minutes and a toolchain that will not start is a
compile failure. Replay mode is our answer to a venue network failure, and it is exercised in CI so it cannot
rot. See ADR-013.

## 7. Alias resolution

Runs at the end of ingestion, before extraction, in `ingest/aliases.py`.

1. **Harvest** candidate identifiers: formal tags matching `[A-Z]{1,4}-?\d{2,4}` (`TK-101`, `XV-102`, `LIS-301`),
   code identifiers from `.mo`/`.puml`, and quoted names in prose.
2. **Seed from explicit alias columns** where the input provides them — `Equipment_Schedule.Alias`,
   `Component_Schedule.Alias / Legacy Name`, and the "Terminology reminders" blocks in field notes. These are
   authoritative and deterministic; no inference needed.
3. **Infer** remaining links with an LLM pass constrained to a fixed schema
   (`{canonical, aliases[], evidence_fragment_ids[], confidence}`).
4. **Canonical choice**: formal tag if one exists, else the most frequent surface form, else the longest.
5. Emit an `AliasSet` per entity; **never discard a surface form**.

Worked cases from the bundles: L1 `tank1 = T1 = TK-101`; L2 `volume = ZON-201`, `freshAir = SRC-OA-201`,
`traceVolume = SEN-CO2-201`; L3 measuring coil appears as both `40 turns` (old sketch) and `50 turns`
(Coil Data Rev B) — an alias *and* a conflict, which must be resolved as two separate concerns: the entity is
one object (alias resolution), its turn count has two candidates (precedence).

## 8. Case manifests

Each benchmark bundle carries `manifest.yaml` (`test/testdata/benchmarks/*/manifest.yaml`) declaring per-file
`document_number`, `revision`, `status`, `issued_date`, `authority_tier` and `reliability`.

**This is test fixture metadata, not production input.** In production those fields are extracted from document
content, and the manifest path is simply absent. The manifest exists so that ingestion and precedence can be
tested independently of extraction quality — and so the benchmark suite has a stated ground truth for what each
document *is*. Loading a manifest must never be required for the pipeline to run; `V-MAN-001` asserts every case
also passes with `--no-manifest`, which is how we keep SF-SCP-01 (no case-specific logic) honest.

## 9. Failure handling

| Failure | Behaviour |
|---|---|
| Unsupported type | `SourceDocument` with `ingest_method: "unsupported"`; warn diagnostic; pipeline continues |
| Corrupt file | Same, with the exception message in `notes` |
| Encrypted PDF | Attempt empty-password decrypt; if it fails, mark unsupported |
| Vision call fails | Retry once with backoff, then degrade: file recorded, no fragments, warn diagnostic |
| Zero fragments overall | **Blocking** — the pipeline cannot proceed and says so plainly |

Consistent with ADR-007: degrade, record, continue. Never crash, never pretend.
