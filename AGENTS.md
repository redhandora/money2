# AGENTS Guidance

## Machine Constraints

- This development machine has only **2 CPU cores**.
- Do **not** over-parallelize subagents.
- Prefer low concurrency (typically **1-2 subagents max** at a time).
- Batch or sequence tasks when possible to avoid CPU/memory pressure.
