/**
 * Drive Folder Cleanup Utility (improved)
 *
 * - Uses PropertiesService for configuration
 * - Supports DRY_RUN mode (no destructive changes)
 * - Writes results to the report sheet in a single batch
 *
 * Required OAuth scopes (Apps Script will prompt when you run):
 *  - https://www.googleapis.com/auth/drive.readonly  (if only reading)
 *  - https://www.googleapis.com/auth/spreadsheets
 *  - If you add deletion: https://www.googleapis.com/auth/drive
 *
 * Safety: Start with DRY_RUN = true and test on a copy of the target folder/sheet.
 */

function getConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    FOLDER_ID: props.getProperty('FOLDER_ID') || 'PUT_FOLDER_ID_HERE',
    SHEET_ID: props.getProperty('SHEET_ID') || 'PUT_SHEET_ID_HERE',
    SIZE_THRESHOLD_MB: Number(props.getProperty('SIZE_THRESHOLD_MB') || '50'),
    DAYS_OLD: Number(props.getProperty('DAYS_OLD') || '180'),
    DRY_RUN: (props.getProperty('DRY_RUN') || 'true') === 'true'
  };
}

/**
 * Utility to set the script properties from code/tests.
 * Example: setConfig('folderId', 'sheetId', true, 100, 365);
 */
function setConfig(folderId, sheetId, dryRun, sizeThresholdMB, daysOld) {
  const props = PropertiesService.getScriptProperties();
  props.setProperties({
    FOLDER_ID: folderId,
    SHEET_ID: sheetId,
    DRY_RUN: String(!!dryRun),
    SIZE_THRESHOLD_MB: String(sizeThresholdMB),
    DAYS_OLD: String(daysOld)
  });
  Logger.log('Config saved to ScriptProperties.');
}

/**
 * Main entrypoint.
 * Scans the folder and writes a report to the sheet.
 */
function driveCleanup() {
  const cfg = getConfig();
  Logger.log('Config: ' + JSON.stringify(cfg));
  if (cfg.FOLDER_ID === 'PUT_FOLDER_ID_HERE' || cfg.SHEET_ID === 'PUT_SHEET_ID_HERE') {
    throw new Error('FOLDER_ID or SHEET_ID not configured. Use setConfig(...) or set Script Properties.');
  }

  try {
    const folder = DriveApp.getFolderById(cfg.FOLDER_ID);
    const filesIter = folder.getFiles();
    const now = new Date();

    const ss = SpreadsheetApp.openById(cfg.SHEET_ID);
    let sheet = ss.getSheetByName('CleanupReport');
    if (!sheet) {
      sheet = ss.insertSheet('CleanupReport');
    }

    // Prepare header
    sheet.clear();
    const HEADER = ['Name', 'File ID', 'Mime Type', 'Size (MB)', 'Last Updated', 'Age (days)', 'Duplicate?', 'Large?', 'Old?'];
    sheet.appendRow(HEADER);

    // Collect rows (avoid many calls to appendRow)
    const rows = [];
    const seenNames = new Set();

    while (filesIter.hasNext()) {
      const file = filesIter.next();
      const name = file.getName();
      const id = file.getId();
      const mime = file.getMimeType();
      const rawSize = file.getSize ? file.getSize() : 0; // for Google Docs this may be zero
      const sizeMB = rawSize ? (rawSize / (1024 * 1024)) : 0;
      const updated = file.getLastUpdated();
      const ageDays = Math.floor((now - updated) / (1000 * 60 * 60 * 24));

      const isDuplicate = seenNames.has(name) ? 'YES' : 'NO';
      const isLarge = sizeMB > cfg.SIZE_THRESHOLD_MB ? 'YES' : 'NO';
      const isOld = ageDays > cfg.DAYS_OLD ? 'YES' : 'NO';

      seenNames.add(name);

      rows.push([
        name,
        id,
        mime,
        sizeMB ? sizeMB.toFixed(2) : '0',
        updated,
        ageDays,
        isDuplicate,
        isLarge,
        isOld
      ]);
    }

    if (rows.length > 0) {
      // write rows in a single batch (starting at row 2 because header row is 1)
      sheet.getRange(2, 1, rows.length, HEADER.length).setValues(rows);
    }

    SpreadsheetApp.flush();
    Logger.log('Drive cleanup report written. Rows: ' + rows.length);

    // Note: This script currently only reports. If you want to delete or move files,
    // add explicit operations with DRY_RUN guard here. Example:
    // if (!cfg.DRY_RUN) { DriveApp.getFileById(id).setTrashed(true); }
  } catch (err) {
    Logger.log('ERROR in driveCleanup: ' + err);
    throw err;
  }
}