# Purpose: owns the bounded repair loop — diagnose a compiler error, localise it in the IR, apply
# one of the known repair actions, re-emit and re-validate. Repairs patch the IR, never the
# emitted text (rule A5).
