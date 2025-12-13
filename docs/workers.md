# Workers

Workers poll the checkpoint store for pending steps and execute them using the existing tool/workflow machinery.

## Starting a Worker
```bash
godman worker start --poll-interval 0.5
```

## Responsibilities
- Poll for workflows in `PENDING`/`RUNNING`.
- Mark steps as `RUNNING` → `COMPLETED` (or `FAILED`).
- Report outputs/errors and metrics back to the checkpoint store.

## Health and Shutdown
- `Worker.run_forever()` loops with a configurable poll interval.
- `Worker.stop()` stops the loop cleanly (used for signals in production).
