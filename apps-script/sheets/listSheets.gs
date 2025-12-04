/**
 * Lists the names of all sheets in a given spreadsheet.
 * 
 * Usage:
 * - Replace SPREADSHEET_ID with the ID from your Google Sheets URL.
 * - Run from the Apps Script editor and check the Logs.
 */
function listSheets() {
  var SPREADSHEET_ID = 'PUT_YOUR_SPREADSHEET_ID_HERE';

  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheets = ss.getSheets();

  sheets.forEach(function(sheet) {
    Logger.log('Sheet name: ' + sheet.getName());
  });
}
