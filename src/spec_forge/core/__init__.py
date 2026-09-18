# Purpose: every higher layer needs a dependency-free foundation to avoid import cycles. This
# package holds the IR Pydantic models (`ir/`), the pint unit registry, deterministic id
# generation and shared error types — nothing here depends on anything else in spec_forge
# (L0, docs/design/ARCHITECTURE.md).
