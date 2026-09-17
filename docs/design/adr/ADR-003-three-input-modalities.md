# ADR-003 — Three input modality groups; CAD excluded

**Status:** Accepted · **Date:** 2026-09-17 · **Impacts:** `ingest`

## Context

The PRD lists text, image, document and mixed bundles as modalities, and suggests CAD geometry and 3D layout as
extensions. It also notes that **depth in one modality beats shallow coverage of all three**.

The four supplied bundles contain 11 file types: `.pdf .docx .xlsx .csv .eml .md .txt .puml .mo .json .png`.
No CAD files.

## Decision

Support three modality groups:

1. **Text and documents** — `.pdf .docx .xlsx .csv .eml .md .txt`
2. **Structured engineering artifacts** — `.puml .mo .json`
3. **Images via vision** — `.png .jpg`, and PDF pages with no extractable text layer

**CAD and 3D geometry are out of scope.**

## Alternatives rejected

| Alternative | Why it lost |
|---|---|
| **Text only** | Satisfies minimum scope but discards the highest-signal inputs. The `Interface_Matrix` sheet is the only port-level topology evidence in any bundle, and every bundle's reference diagram is a PNG. |
| **Add CAD/STEP import** | No CAD files exist in the supplied cases. Building an importer for data we do not have is scope for its own sake, which the PRD explicitly does not reward. |
| **Vision for everything, including documents** | Slower, more expensive, and strictly worse than text extraction where a text layer exists. Vision is the fallback, not the default. |

## Consequences

- Group 2 is cheap and deterministic — PlantUML and legacy Modelica parse without a model call and seed the IR
  with real topology.
- Group 3 requires the strongest fabrication defences: vision elements are capped at confidence 0.8, sit at
  authority tier 8, and may never be the sole justification for a numeric value.
- The image-only-PDF fallback is mandatory, not optional. The hackathon briefing PDF proves the failure mode is
  real.
