/**
 * Template for a small sheet-cleaning helper.
 * Customize ranges and normalization logic for your receipts sheet.
 *
 * Example usage:
 * - Update RECEIPT_SHEET_ID and SHEET_NAME in properties or call setReceiptConfig.
 * - Run `cleanReceipts()` in the Apps Script editor.
 */

function getReceiptConfig() {
  const props = PropertiesService.getScriptProperties();
  return {
    SHEET_ID: props.getProperty('RECEIPT_SHEET_ID') || 'PUT_SHEET_ID_HERE',
    SHEET_NAME: props.getProperty('RECEIPT_SHEET_NAME') || 'Receipts'
  };
}

function cleanReceipts() {
  const cfg = getReceiptConfig();
  if (cfg.SHEET_ID === 'PUT_SHEET_ID_HERE') {
    throw new Error('RECEIPT_SHEET_ID not configured.');
  }
  const ss = SpreadsheetApp.openById(cfg.SHEET_ID);
  const sheet = ss.getSheetByName(cfg.SHEET_NAME);
  if (!sheet) {
    throw new Error('Sheet not found: ' + cfg.SHEET_NAME);
  }

  // Example: Trim whitespace in column A for all rows with data
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) {
    Logger.log('No data to clean.');
    return;
  }
  const range = sheet.getRange(2, 1, lastRow - 1, 1);
  const values = range.getValues();
  const out = values.map(r => [typeof r[0] === 'string' ? r[0].trim() : r[0]]);
  range.setValues(out);
  Logger.log('Receipt cleanup completed for ' + (lastRow - 1) + ' rows.');
}