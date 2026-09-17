# 09 — Validation, Repair and Failure Behaviour

**Status:** Baseline · **Decisions:** ADR-007, ADR-001 · **Modules:** `src/spec_forge/validate/`, `src/spec_forge/repair/`
**Answers:** PRD §10 *"How do you validate before showing the user?"* and *"What happens on failure?"*

---

## 1. The validation ladder

Four gates, in order. Each has a defined severity and a defined failure behaviour. **A stage never runs on input
that failed a blocking gate upstream.**

| # | Gate | Checks | Blocking? |
|---:|---|---|---|
| 1 | **Schema** | JSON Schema `sfir/1.0`; id resolution; provenance invariant | Yes |
| 2 | **Semantic** | Units, port compatibility, topology, state reachability, library binding | Yes for `error` |
| 3 | **Compile** | `omc checkModel`; SysML v2 parse | **Yes — the hard gate** |
| 4 | **Simulate** | Model runs; trajectories plausible; reference-trace comparison | No — `warn` |

Gate 4 is deliberately non-blocking. A model that compiles but will not converge is still a useful deliverable
for a systems engineer if its limitation is stated; suppressing it would trade an honest partial result for
nothing. This follows the PRD's own ordering — compilability is a *hard gate*, simulatability is an
*expectation*.

## 2. Rule catalogue

`validate/rules/`, one module per family. Every rule has a stable id, a severity, a human-readable message and a
**suggested repair action**, which is what makes automated repair possible rather than guesswork.

### 2.1 Traceability and honesty — `V-TRACE-*`

| ID | Rule | Severity |
|---|---|---|
| `V-TRACE-001` | Every entity has non-empty `fragment_ids`, `assumption_id` or `derived_from` | **error** |
| `V-TRACE-002` | No `Part` exists whose sole justification is an assumption (no assumed components) | **error** |
| `V-TRACE-003` | Every `Assumption` references a catalogue entry or a library default | **error** |
| `V-TRACE-004` | Every `Conflict` retains all positions and names the rule applied | error |
| `V-TRACE-005` | Elements with `confidence < 0.7` are reported in the summary | info |

`V-TRACE-001` and `V-TRACE-002` together are the mechanical form of SF-IN-03. They are the reason "no
fabrication" is a property of the build rather than an instruction a model may ignore.

### 2.2 Units and quantities — `V-UNIT-*`

Backed by **pint** with an SI registry.

| ID | Rule | Severity |
|---|---|---|
| `V-UNIT-001` | Every valued attribute has a unit or `dimensionless: true` | **error** |
| `V-UNIT-002` | Unit is dimensionally consistent with its declared `quantity` | **error** |
| `V-UNIT-003` | Both sides of a constraint or equation are dimensionally equal | **error** |
| `V-UNIT-004` | Connected ports agree in quantity and unit, or a conversion is explicit | **error** |
| `V-UNIT-005` | A value's magnitude is plausible for its quantity and unit | warn |

`V-UNIT-004` is the L2 trap in rule form. The sensor produces kg/kg, the controller setpoint is normalised
`1.0`, the limit is stated in ppm, and the actuator command is in ACH. **Every one of those conversions must be
an explicit `gain` part with a stated factor** — `gainSensor = 1/1.519e-3` — not an implicit coercion. A pipeline
that silently unifies them produces a model that compiles and is numerically wrong by a factor of 658.

`V-UNIT-005` catches the class of error where a number is right and its unit is not: a 1.58 **mm** gap recorded
as 1.58 m, or 8.18e-6 kg/s read as kg/h.

### 2.3 Topology — `V-TOPO-*`

| ID | Rule | Severity |
|---|---|---|
| `V-TOPO-001` | Every connection joins two existing ports | **error** |
| `V-TOPO-002` | Port types are compatible (fluid↔fluid, signal↔signal) | **error** |
| `V-TOPO-003` | Causality is consistent: no two `out` signals connected | **error** |
| `V-TOPO-004` | No unresolved `proto_connection` remains (part-level edges from diagrams) | **error** |
| `V-TOPO-005` | No orphan part — every part has at least one connection or is a declared boundary | warn |
| `V-TOPO-006` | Fluid network is connected; no isolated subgraph | warn |
| `V-TOPO-007` | Exactly one ground per electrical and per magnetic network | **error** |

### 2.4 Behaviour — `V-BEH-*`

| ID | Rule | Severity |
|---|---|---|
| `V-BEH-001` | Initial state exists and is reachable | **error** |
| `V-BEH-002` | No unreachable state | **error** |
| `V-BEH-003` | Every interlock exception cites evidence | **error** |
| `V-BEH-004` | Forbidden output combinations are prevented in every reachable state | **error** |
| `V-BEH-005` | Transition priorities are total where triggers can coincide | **error** |
| `V-BEH-006` | Every state is exitable (no unintended terminal state) | warn |
| `V-BEH-007` | Timer suspend semantics declared where a timer can be interrupted | warn |

`V-BEH-004` is SF-ACC-04 (*"required states are reachable and forbidden combinations are prevented"*) made
executable: the checker enumerates reachable states and asserts that each interlock holds in all of them, minus
its scoped exceptions. For L1 this proves V1+V2 never co-open anywhere, and that V2+V3 co-open **only** in
SHUTDOWN.

### 2.5 Physics plausibility — `V-PHYS-*`

| ID | Rule | Severity |
|---|---|---|
| `V-PHYS-001` | Every storage element has an inflow and an outflow path | warn |
| `V-PHYS-002` | Conserved quantities balance across each junction | warn |
| `V-PHYS-003` | Parallel branches share the same effort difference | **error** |
| `V-PHYS-004` | Loss paths are represented where the documents state one | warn |
| `V-PHYS-005` | Sign conventions are declared where a port convention differs from physical direction | **error** |

`V-PHYS-003` and `V-PHYS-005` are L3 and L2 respectively. L3's leakage and air-gap branches are parallel and
must share magnetic potential difference while carrying different flux — the scratch note warns *"Do not put
total Phi_core into gap B calculation."* L2's fresh-air source takes a **negative** `m_flow` for flow **into**
the zone, and the design review requires SysML to distinguish that software convention from physical airflow
direction. A model that reports negative physical ventilation has failed `V-PHYS-005`.

### 2.6 Library and Modelica — `V-LIB-*`, `V-MOD-*`

`V-LIB-001` unbound archetype (**error**, `06_component_library_spec.md` §6). `V-MOD-001`–`009` per
`08_modelica_emission_spec.md` §8. `V-VIS-001` — a numeric attribute may not rest on vision evidence alone
(**error**, `04_ingestion_spec.md` §4.9).

## 3. Severities

| Severity | Meaning | Effect |
|---|---|---|
| `error` | The model is wrong or unemittable | Blocks the stage; enters repair |
| `warn` | The model may be incomplete or implausible | Reported in summary and UI; proceeds |
| `info` | Worth knowing | Reported only |

## 4. Failure behaviour — the degradation ladder

The PRD asks: *retry, repair loop, degrade gracefully, or ask the user?* **All four, in this order.** ADR-007.

```
  attempt
     │ transient (network, rate limit, timeout)
     ├──▶ 1. RETRY        exponential backoff, max 3
     │ deterministic failure with a known repair action
     ├──▶ 2. REPAIR       bounded loop, §5
     │ repair exhausted or no action available
     ├──▶ 3. DEGRADE      emit best artifact reached + explicit gap report
     │ ambiguity only a human can resolve
     └──▶ 4. ASK          OpenQuestion → clarifying dialogue
```

**Degradation guarantee:** every run produces output. A run that fails at the Modelica gate still delivers the
IR, the SysML, the evidence ledger and the summary, with the failure stated at the top. The user is never shown
a stack trace and nothing else (SF-UX-04), and never shown a green result that is not green.

## 5. The repair loop

`repair/loop.py`. Applies to both compile failures and semantic-validation errors.

```
repair(artifact, diagnostics, max_attempts=3):
  for attempt in 1..max_attempts:
      1. PARSE      omc / validator output → structured Diagnostic
                    (rule id or error class, location, message, offending element)
      2. LOCALISE   map the diagnostic back to the IR element via the emitter element map
      3. DIAGNOSE   classify: missing_declaration | type_mismatch | arity_mismatch
                    | missing_ground | undefined_state | unit_mismatch | unknown
      4. PLAN       select a repair action:
                      - known class  → deterministic fix (preferred)
                      - unknown      → LLM proposes an IR patch, schema-validated before apply
      5. APPLY      JSON Patch to the IR — never to the emitted text
      6. RE-EMIT + RE-VALIDATE from the top
  else: degrade, and report every attempt
```

Three properties matter and are non-negotiable:

- **Repairs are applied to the IR, never to the generated file.** Patching the `.mo` directly would desynchronise
  it from the SysML and from the IR, reintroducing precisely the divergence ADR-001 exists to prevent. It would
  also make the next run reproduce the same defect.
- **Every attempt is recorded** — diagnostic, action, outcome — into `runs/<run_id>/repair.log` and the summary.
  This is Test-and-Iterate evidence and it is also the honest record of what the generator got wrong.
- **Bounded.** Three attempts, then degrade. An unbounded loop against a live compiler is how a 10-minute demo
  slot disappears.

### 5.1 Known repair actions

| Diagnostic class | Deterministic action |
|---|---|
| Missing `inner System` | Insert from `archetype.requires` |
| `nPorts` arity mismatch | Recompute from connection count |
| Missing ground | Add ground part via `SA-ELEC-001` / `SA-MAG-001` |
| Medium not declared / inconsistent | Propagate the dominant medium across the fluid subgraph |
| Unknown class / component | Rebind archetype; if impossible → `V-LIB-001` → open question |
| Undefined variable in equation | Resolve against IR attributes; else escalate |
| Unit mismatch | Insert an explicit conversion gain, recorded as an assumption |
| Initial condition missing | Apply library default, recorded as an assumption |

Note that four of these actions create **assumptions** rather than silently fixing the model. A repair is itself
an inference, and it inherits the same honesty obligation as any other.

## 6. Round-trip consistency check

`validate/consistency.py`. Runs after both emitters succeed, using their element maps.

| Check | Severity |
|---|---|
| Part set in SysML ≡ part set in Modelica | **error** |
| Port set per part matches | **error** |
| Connection set matches (as an undirected port-pair set) | **error** |
| Parameter names and values match | **error** |
| State and transition sets match where both express them | warn |

This is the explicit answer to the PRD's warning that independent generation causes silent divergence, and it is
one of the named stretch-bonus items. It is cheap to implement — both emitters already produce element maps —
and it converts "they come from the same IR, so they agree" from an argument into a test.

## 7. Reference-trace comparison

Where the input bundle contains a recorded run (tier 7 evidence), compare simulation output against it:

1. Align on the time column; resample to common timestamps.
2. Per shared signal, compute max absolute deviation, RMS deviation and event-time differences.
3. For discrete signals (valve states, controller state), compare **transition times** with a tolerance.
4. Report a per-signal table. **Deviations are reported, not hidden.**

Tolerances are per case in `manifest.yaml` (`acceptance.tolerances`), because what counts as agreement is a
property of the case, not of the code.

This gives an objective accuracy number for SF-ACC-01/03 rather than an impression, and it is the strongest
evidence we can offer for *"physically plausible behaviour"*. For L1 the reference trace also encodes the
command schedule (events at 20/220/280/650/700 s) and the observed 0.80 m high limit — so the comparison
independently confirms the precedence engine picked the right value.

## 8. Testing

| Test | Assertion |
|---|---|
| `test_rules_have_ids.py` | Every rule has a unique id, severity and message |
| `test_blocking_rules_block.py` | Each blocking rule actually halts the pipeline on a crafted bad IR |
| `test_repair_bounded.py` | Repair never exceeds `max_attempts` |
| `test_repair_patches_ir.py` | No repair writes to an emitted artifact |
| `test_degradation.py` | A forced failure at each stage still produces partial output and a gap report |
| `test_consistency_detects_divergence.py` | A deliberately desynchronised emitter pair is caught |
| `test_reference_trace_l1.py` | L1 simulation matches the 900 s reference within tolerance |
