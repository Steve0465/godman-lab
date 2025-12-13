# Critic Tools

Critics provide lightweight evaluations to guide self-correction.

- **Quality critic** (`evaluate_quality`): checks for presence/clarity of output.
- **Structural validator** (`validate_structure`): ensures required keys/fields exist.
- **Safety critic** (`check_safety`): flags obvious unsafe patterns (no external calls).
- **Factuality critic** (`evaluate_factuality`): heuristic check for contradictions or missing content.

Critics return `CriticResult(score, labels, reasons)`; AgentLoop aggregates scores and decisions via policies.
