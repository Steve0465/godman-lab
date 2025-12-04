# scripts/google

This folder contains Google Apps Script utilities used in this repository.

Files
- `drive-cleanup.gs` — Scans a Drive folder and writes a CleanupReport sheet with:
  - duplicate file names
  - files larger than a threshold
  - files older than a threshold
  This version is read-only by default (DRY_RUN), uses Script Properties for config, and batches sheet writes.

- `sheets-receipt-cleaner.gs` — (small helper) template to normalize sheet data (update as needed).

Quick start
1. Make test copies of any target Drive folder and the Google Sheet before running anything on production data.
2. Configure:
   - Use the included `setConfig(folderId, sheetId, dryRun, sizeThresholdMB, daysOld)` from the Apps Script editor to set properties,
     or set Script Properties in the Apps Script UI.
   - Example in the editor's console: `setConfig('yourFolderId', 'yourSheetId', true, 50, 180)`
3. Run:
   - Open the Apps Script project containing these files and run `driveCleanup`.
   - The script will create/replace a sheet named `CleanupReport` in the target spreadsheet.
4. Review results in the spreadsheet. Keep `dryRun=true` until you're ready to add deletion/move operations.
5. For development: use clasp (below) to manage the project locally.

clasp quickstart
1. `npm i -g @google/clasp`
2. `clasp login`
3. Create a `.clasp.json` in this folder (example below) with your scriptId.
4. `clasp push` to push files.

.clasp.json example
{
  "scriptId": "<YOUR_SCRIPT_ID>",
  "rootDir": "."
}

Safety notes
- The script is read-only by default. If you add destructive actions (trash/delete/move), gate them with DRY_RUN checks and test thoroughly.
- Do not commit OAuth client secrets or personal tokens to the repo.