# Purpose: one loader module per input file type (pdf, docx, xlsx, tabular, email, plaintext,
# plantuml, modelica, structured, image), dispatched by ingest/dispatch.py. Grouped here so
# ingest's public surface doesn't leak per-format detail (docs/design/packagedesign.md §2).
