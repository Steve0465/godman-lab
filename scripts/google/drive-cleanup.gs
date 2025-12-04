/**
 * Drive Folder Cleanup Utility
 * ----------------------------------------------
 * Scans a Google Drive folder and reports:
 *  - Duplicate file names
 *  - Files over a size threshold
 *  - Files older than a given number of days
 * 
 * Output is written to a Google Sheet.
 */

function driveCleanup() {
  try {
    const FOLDER_ID = "PUT_FOLDER_ID_HERE";     // Folder to scan
    const SHEET_ID  = "PUT_SHEET_ID_HERE";      // Google Sheet for output
    const SIZE_THRESHOLD_MB = 50;               // Flag files > 50MB
    const DAYS_OLD = 180;                       // Flag files older than 6 months

    const folder = DriveApp.getFolderById(FOLDER_ID);
    const files = folder.getFiles();

    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName("CleanupReport") 
                 || SpreadsheetApp.openById(SHEET_ID).insertSheet("CleanupReport");

    sheet.clear();
    sheet.appendRow(["Name", "File ID", "Size (MB)", "Last Updated", "Duplicate?", "Large?", "Old?"]);

    const seen = {};
    const now = new Date();

    while (files.hasNext()) {
      const file = files.next();
      const name = file.getName();
      const id = file.getId();
      const sizeMB = file.getSize() / (1024 * 1024);
      const updated = file.getLastUpdated();
      const ageDays = Math.floor((now - updated) / (1000 * 60 * 60 * 24));

      const isDuplicate = seen[name] ? "YES" : "NO";
      const isLarge = sizeMB > SIZE_THRESHOLD_MB ? "YES" : "NO";
      const isOld = ageDays > DAYS_OLD ? "YES" : "NO";

      seen[name] = true;

      sheet.appendRow([
        name,
        id,
        sizeMB.toFixed(2),
        updated,
        isDuplicate,
        isLarge,
        isOld
      ]);
    }

    SpreadsheetApp.flush();
    Logger.log("Drive cleanup complete.");
  } catch (err) {
    Logger.log("ERROR: " + err);
  }
}
