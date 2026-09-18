# Purpose: the distribution `spec-forge` (hyphen) needs an importable root package named
# `spec_forge` (underscore is the only legal Python identifier form, ADR-014). This package has
# no logic of its own — it only roots the thirteen layered subpackages described in
# docs/design/ARCHITECTURE.md and docs/design/packagedesign.md §2-3.
