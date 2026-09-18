# Purpose: one state-machine emission strategy per pattern (e.g. interlocked start/stop
# sequencing), selected deterministically from the IR's state_machine elements — logic, not data,
# which is why this subpackage (unlike templates/) is Python rather than YAML/Jinja.
