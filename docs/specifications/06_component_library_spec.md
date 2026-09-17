# 06 — Component Library and Domain Knowledge Injection

**Status:** Baseline · **Decision:** ADR-006 · **Module:** `src/spec_forge/library/`
**Implements:** SF-EXT-08 · **Answers:** PRD §10 *"How is domain knowledge injected?"*

---

## 1. The question this answers

The PRD lists four ways to inject domain knowledge: prompting, retrieval over a component library, fine-tuning,
or a typed schema that constrains what can be generated. We use **two of them together**, which is the strongest
defensible combination at hackathon scale:

- a **versioned, typed component library**, retrieved at extraction time and bound at emission time;
- a **schema-constrained IR** that cannot represent a part which is not bound to a library archetype.

Fine-tuning is out (no data, no time, unfalsifiable at judging). Prompt-only is out — it produces knowledge that
is invisible, unversioned, untestable, and different on every call, and it cannot guarantee the SysML and
Modelica views of one part agree.

## 2. What an archetype is

An **archetype** is a reusable engineering concept with a fixed contract:

- a stable key (`fluid.tank.vertical`);
- a declared port set with types, media and causality;
- declared attributes with quantities, units and defaults;
- a **SysML v2 binding** — the `part def` it emits;
- a **Modelica binding** — the MSL (or local) component it instantiates, with parameter mapping;
- the standard assumptions it carries;
- recognition hints for retrieval.

One archetype produces **both** target bindings. This is the mechanism that makes divergence structurally
impossible: the SysML `part def` and the Modelica component for a given part are two projections of one record,
not two independent generations.

## 3. Format

Versioned YAML under `src/spec_forge/library/archetypes/`, one file per domain.

```yaml
key: fluid.tank.vertical
version: 1
label: Vertical liquid tank
domain: fluid
description: An open vertical vessel holding liquid, with level as its state.

ports:
  - name: inlet
    port_type: fluid
    direction: acausal
    medium: liquid
    required: true
  - name: outlet
    port_type: fluid
    direction: acausal
    medium: liquid
    required: true
    assumption: SA-FLUID-002      # implied when unstated
  - name: level
    port_type: signal_real
    direction: out
    quantity: Length
    unit: m
    required: false

attributes:
  - name: area
    quantity: Area
    unit: m2
    required: true
  - name: height
    quantity: Length
    unit: m
    required: false
  - name: level_init
    quantity: Length
    unit: m
    default: 0.0
    assumption: SA-FLUID-003

sysml:
  part_def: Tank
  imports: [ISQ::LengthValue, ISQ::AreaValue]

modelica:
  component: Modelica.Fluid.Vessels.OpenTank
  msl_version: ">=4.0.0"
  parameter_map:
    area: crossArea
    height: height
    level_init: level_start
  port_map:
    inlet: ports[1]
    outlet: ports[2]
  requires:
    - inner Modelica.Fluid.System system
  notes: nPorts must equal the number of connected fluid ports.

standard_assumptions: [SA-FLUID-001, SA-FLUID-002]

recognition:
  keywords: [tank, vessel, reservoir, basin, bin, receiver]
  tag_patterns: ["^TK-\\d+", "^B\\d+$", "^V-\\d+"]
  puml_stereotypes: [tank, vessel]
```

`modelica.requires` is the kind of detail that decides whether the compile gate is green. `OpenTank` needs an
`inner System` in the enclosing model and an `nPorts` consistent with its connections; omitting either produces
a model that looks correct and does not compile. Encoding it once in the library is how we stop rediscovering it
per-case.

## 4. Coverage

Scoped to the reasoning patterns the four levels test. **Deliberately not** a general MSL wrapper.

| Domain | Archetypes | Serves |
|---|---|---|
| `fluid` | tank.vertical, valve.onoff, valve.control, pump, source.flow, sink.boundary, pipe, junction.volume, heat_exchanger, evaporator, condenser | L1, L4 |
| `air` | zone.wellmixed, duct, source.massflow, boundary.pressure, source.trace | L2 |
| `control` | statemachine.sequential, controller.pid, controller.p, gain, limiter, comparator, schedule.piecewise, edge_trigger, timer, interlock | L1, L2, L4 |
| `sensor` | level, concentration, flow, temperature, flux | all |
| `magnetic` | fluxtube.leakage, fluxtube.iron, airgap, coil.exciting, coil.measuring, ground.magnetic, source.current | L3 |
| `electrical` | ground, resistor, source.current, source.voltage | L3 |
| `thermal` | heater, cooler, heat_port | L3, L4 |

Adding an archetype is the normal way to extend SpecForge to a new domain. Adding a branch in `src/` is not
(SF-SCP-01).

## 5. Retrieval

`library/retrieval.py`, called during extraction.

1. **Deterministic first** — match formal tags against `recognition.tag_patterns` and exact keywords. `TK-101`
   binds to `fluid.tank.vertical` with no model call. Most benchmark parts resolve here, which is both cheaper
   and more repeatable (SF-ACC-05).
2. **Lexical** — BM25 over labels, descriptions and keywords for the remainder.
3. **Semantic** — embeddings over archetype descriptions, for prose that uses none of our vocabulary.
4. Top-`k` (default 5) candidates are supplied to the extraction agent **as a closed set**. The agent selects or
   returns `unbound` with a reason. **It may not invent a key.**

Step 4 is the constraint that matters. An unconstrained model will happily emit
`Modelica.Fluid.Vessels.MagicTank`, and it will look plausible. Closed-set selection makes that unrepresentable.

## 6. Unbound parts

`archetype: null` is a **hard validation error** (`V-LIB-001`), never a silent pass-through. On encountering one:

1. Record an `OpenQuestion`: *"No archetype matched 'flash drum'. Nearest: evaporator (0.62), tank (0.55)."*
2. Emit a `library_gap` diagnostic naming the missing archetype.
3. Degrade per ADR-007 — emit everything else, mark this part unmodelled in `summary.md`, do not fabricate it.

This is the honest failure mode. *"I do not have a model for a flash drum"* is a good answer; a guessed MSL
component that compiles and is physically wrong is the worst possible one, because it passes the gate while
being exactly the silent fabrication SF-IN-03 prohibits.

## 7. Reuse across runs (SF-EXT-08)

When a part binds to an archetype, the binding — canonical name, tag, alias set, parameter mapping and any user
corrections — is persisted to the `component_binding` table (`13_data_model_spec.md`). On a later run in the same
project, an identical tag or a high-confidence alias match reuses the prior binding and its **tier-0 user
corrections**, so a component modelled once is recognised again and a correction made once is not re-litigated.

## 8. Extension libraries

Project-local archetypes may be supplied in `library/local/` and override core entries by key with a higher
`version`. This is how a real customer would inject house conventions without forking, and it is what makes the
library a **product feature** rather than an internal lookup table.

## 9. Testing

| Test | Assertion |
|---|---|
| `test_archetype_schema.py` | Every YAML validates against the archetype schema |
| `test_modelica_bindings.py` | **Every `modelica.component` resolves in the installed MSL** via `omc` `getClassInformation` |
| `test_sysml_bindings.py` | Every `sysml.part_def` parses in the SysML v2 toolchain |
| `test_port_map_arity.py` | Declared `port_map` entries exist on the target MSL component |
| `test_retrieval_precision.py` | Known tags from all four bundles bind to the expected archetype |

`test_modelica_bindings.py` runs in CI and catches invented components **before** they reach generation — the
failure mode the briefing names explicitly under what scores well in `AI-LOG.md`: *"Invented library components
you caught and replaced."* We expect to have entries for that log from this test, and they should be recorded
when they happen rather than reconstructed later.
