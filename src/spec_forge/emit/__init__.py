# Purpose: owns the two deterministic template emitters (sysml/, modelica/) plus report
# generation. No LLM call is permitted anywhere under this package (rule A3); every value comes
# from the validated IR, never inferred (rule A2).
