# Purpose: ADR-004 / D3 — LangGraph orchestration has exactly two agentic (looping) nodes, repair
# and clarification; everything else is a single call or plain code. pipeline/graph.py doesn't
# exist yet (Phase 1, 16_pipeline_orchestration_spec.md); this is the guard rail written now,
# waiting for that code, rather than retrofitted after.

from __future__ import annotations

import pytest

pytestmark = pytest.mark.xfail(
    reason=(
        "pipeline/graph.py doesn't exist yet (Phase 1, 16_pipeline_orchestration_spec.md). Once "
        "the LangGraph graph is built, this test will inspect the compiled graph and assert "
        "exactly two looping (agentic) nodes: repair and clarification (ADR-004, D3)."
    ),
    strict=True,
)

_EXPECTED_LOOPING_NODES = {"repair", "clarification"}


def test_graph_has_exactly_two_looping_nodes() -> None:
    from spec_forge.pipeline import graph

    compiled = graph.build_graph()
    looping = {name for name, node in compiled.nodes.items() if getattr(node, "is_looping", False)}
    assert looping == _EXPECTED_LOOPING_NODES
