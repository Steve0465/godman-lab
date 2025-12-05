/**
 * Google Drive Cleanup Tools
 * 
 * Functions for cleaning up your Drive:
 * - Find and remove duplicate files
 * - Delete old/unused files
 * - Find large files eating up storage
 * - Clean up empty folders
 * 
 * ⚠️ WARNING: These functions can delete files! Test carefully.
 */

// ============================================================================
// CONFIGURATION
// ============================================================================

const CLEANUP_CONFIG = {
  // Days before a file is considered "old"
  OLD_FILE_DAYS: 365,
  
  // Minimum file size (MB) to report as "large"
  LARGE_FILE_MB: 100,
  
  // Trash old files instead of permanent delete
  USE_TRASH: true,
  
  // Dry run mode (don't actually delete anything)
  DRY_RUN: true
};

// ============================================================================
// DUPLICATE FINDER
// ============================================================================

/**
 * Find duplicate files by name and size
 * Returns a report of duplicates
 */
function findDuplicates() {
  Logger.log('Searching for duplicate files...');
  Logger.log('This may take a while for large Drives...');
  
  const fileMap = {};
  const duplicates = [];
  const files = DriveApp.getFiles();
  
  // Build file map
  while (files.hasNext()) {
    const file = files.next();
    const key = `${file.getName()}_${file.getSize()}`;
    
    if (!fileMap[key]) {
      fileMap[key] = [];
    }
    
    fileMap[key].push({
      id: file.getId(),
      name: file.getName(),
      size: file.getSize(),
      created: file.getDateCreated(),
      modified: file.getLastUpdated(),
      url: file.getUrl()
    });
  }
  
  // Find duplicates
  for (const [key, fileList] of Object.entries(fileMap)) {
    if (fileList.length > 1) {
      duplicates.push({
        name: fileList[0].name,
        size: fileList[0].size,
        count: fileList.length,
        files: fileList
      });
    }
  }
  
  // Report
  Logger.log('='.repeat(60));
  Logger.log(`Found ${duplicates.length} sets of duplicates`);
  Logger.log('='.repeat(60));
  
  let totalWasted = 0;
  
  duplicates.forEach(dup => {
    const wastedSpace = dup.size * (dup.count - 1);
    totalWasted += wastedSpace;
    
    Logger.log('');
    Logger.log(`File: ${dup.name}`);
    Logger.log(`Size: ${formatBytes(dup.size)}`);
    Logger.log(`Copies: ${dup.count}`);
    Logger.log(`Wasted space: ${formatBytes(wastedSpace)}`);
    
    dup.files.forEach((file, i) => {
      Logger.log(`  Copy ${i + 1}:`);
      Logger.log(`    Created: ${file.created}`);
      Logger.log(`    Modified: ${file.modified}`);
      Logger.log(`    URL: ${file.url}`);
    });
  });
  
  Logger.log('');
  Logger.log('='.repeat(60));
  Logger.log(`Total wasted space: ${formatBytes(totalWasted)}`);
  Logger.log('='.repeat(60));
  
  return duplicates;
}

/**
 * Remove duplicate files (keeps the newest version)
 * ⚠️ Use with caution!
 */
function removeDuplicates() {
  if (!CLEANUP_CONFIG.DRY_RUN) {
    const confirm = Browser.msgBox(
      'Remove Duplicates',
      'This will delete duplicate files. Are you sure?',
      Browser.Buttons.YES_NO
    );
    
    if (confirm !== 'yes') {
      Logger.log('Cancelled by user');
      return;
    }
  }
  
  const duplicates = findDuplicates();
  let removed = 0;
  
  Logger.log('');
  Logger.log('Removing duplicates...');
  
  duplicates.forEach(dup => {
    // Sort by modification date (newest first)
    dup.files.sort((a, b) => b.modified - a.modified);
    
    // Keep the first (newest), delete the rest
    for (let i = 1; i < dup.files.length; i++) {
      const file = dup.files[i];
      
      if (CLEANUP_CONFIG.DRY_RUN) {
        Logger.log(`[DRY RUN] Would delete: ${file.name} (${file.id})`);
      } else {
        try {
          const driveFile = DriveApp.getFileById(file.id);
          if (CLEANUP_CONFIG.USE_TRASH) {
            driveFile.setTrashed(true);
            Logger.log(`✓ Trashed: ${file.name}`);
          } else {
            DriveApp.getFileById(file.id).setTrashed(true);
            Logger.log(`✓ Deleted: ${file.name}`);
          }
          removed++;
        } catch (e) {
          Logger.log(`✗ Error deleting ${file.name}: ${e.message}`);
        }
      }
    }
  });
  
  Logger.log('');
  Logger.log(`${CLEANUP_CONFIG.DRY_RUN ? '[DRY RUN] Would remove' : 'Removed'} ${removed} duplicate files`);
}

// ============================================================================
// OLD FILE CLEANUP
// ============================================================================

/**
 * Find files older than configured days
 */
function findOldFiles() {
  Logger.log(`Finding files older than ${CLEANUP_CONFIG.OLD_FILE_DAYS} days...`);
  
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - CLEANUP_CONFIG.OLD_FILE_DAYS);
  
  const oldFiles = [];
  const files = DriveApp.getFiles();
  
  while (files.hasNext()) {
    const file = files.next();
    
    if (file.getLastUpdated() < cutoffDate) {
      oldFiles.push({
        name: file.getName(),
        id: file.getId(),
        size: file.getSize(),
        modified: file.getLastUpdated(),
        url: file.getUrl()
      });
    }
  }
  
  Logger.log('='.repeat(60));
  Logger.log(`Found ${oldFiles.length} old files`);
  Logger.log('='.repeat(60));
  
  let totalSize = 0;
  
  oldFiles.forEach(file => {
    totalSize += file.size;
    Logger.log('');
    Logger.log(`File: ${file.name}`);
    Logger.log(`Size: ${formatBytes(file.size)}`);
    Logger.log(`Last modified: ${file.modified}`);
    Logger.log(`URL: ${file.url}`);
  });
  
  Logger.log('');
  Logger.log(`Total size: ${formatBytes(totalSize)}`);
  
  return oldFiles;
}

/**
 * Delete old files
 * ⚠️ Use with caution!
 */
function deleteOldFiles() {
  if (!CLEANUP_CONFIG.DRY_RUN) {
    const confirm = Browser.msgBox(
      'Delete Old Files',
      `This will delete files older than ${CLEANUP_CONFIG.OLD_FILE_DAYS} days. Continue?`,
      Browser.Buttons.YES_NO
    );
    
    if (confirm !== 'yes') {
      Logger.log('Cancelled');
      return;
    }
  }
  
  const oldFiles = findOldFiles();
  let deleted = 0;
  
  oldFiles.forEach(file => {
    if (CLEANUP_CONFIG.DRY_RUN) {
      Logger.log(`[DRY RUN] Would delete: ${file.name}`);
    } else {
      try {
        const driveFile = DriveApp.getFileById(file.id);
        driveFile.setTrashed(true);
        Logger.log(`✓ Deleted: ${file.name}`);
        deleted++;
      } catch (e) {
        Logger.log(`✗ Error: ${e.message}`);
      }
    }
  });
  
  Logger.log(`${CLEANUP_CONFIG.DRY_RUN ? '[DRY RUN] Would delete' : 'Deleted'} ${deleted} files`);
}

// ============================================================================
// LARGE FILE FINDER
// ============================================================================

/**
 * Find files larger than configured size
 */
function findLargeFiles() {
  Logger.log(`Finding files larger than ${CLEANUP_CONFIG.LARGE_FILE_MB}MB...`);
  
  const minSize = CLEANUP_CONFIG.LARGE_FILE_MB * 1024 * 1024;
  const largeFiles = [];
  const files = DriveApp.getFiles();
  
  while (files.hasNext()) {
    const file = files.next();
    const size = file.getSize();
    
    if (size > minSize) {
      largeFiles.push({
        name: file.getName(),
        size: size,
        url: file.getUrl()
      });
    }
  }
  
  // Sort by size
  largeFiles.sort((a, b) => b.size - a.size);
  
  Logger.log('='.repeat(60));
  Logger.log(`Found ${largeFiles.length} large files`);
  Logger.log('='.repeat(60));
  
  let totalSize = 0;
  
  largeFiles.forEach((file, i) => {
    totalSize += file.size;
    Logger.log(`${i + 1}. ${file.name}`);
    Logger.log(`   Size: ${formatBytes(file.size)}`);
    Logger.log(`   URL: ${file.url}`);
    Logger.log('');
  });
  
  Logger.log(`Total size of large files: ${formatBytes(totalSize)}`);
  
  return largeFiles;
}

// ============================================================================
// EMPTY FOLDER CLEANUP
// ============================================================================

/**
 * Find and optionally remove empty folders
 */
function cleanupEmptyFolders() {
  Logger.log('Finding empty folders...');
  
  const emptyFolders = [];
  const folders = DriveApp.getFolders();
  
  while (folders.hasNext()) {
    const folder = folders.next();
    
    // Check if folder is empty (no files or subfolders)
    const hasFiles = folder.getFiles().hasNext();
    const hasFolders = folder.getFolders().hasNext();
    
    if (!hasFiles && !hasFolders) {
      emptyFolders.push({
        name: folder.getName(),
        id: folder.getId(),
        url: folder.getUrl()
      });
    }
  }
  
  Logger.log('='.repeat(60));
  Logger.log(`Found ${emptyFolders.length} empty folders`);
  Logger.log('='.repeat(60));
  
  emptyFolders.forEach(folder => {
    Logger.log(`Folder: ${folder.name}`);
    Logger.log(`URL: ${folder.url}`);
    Logger.log('');
    
    if (CLEANUP_CONFIG.DRY_RUN) {
      Logger.log(`[DRY RUN] Would delete this folder`);
    } else {
      try {
        DriveApp.getFolderById(folder.id).setTrashed(true);
        Logger.log(`✓ Deleted`);
      } catch (e) {
        Logger.log(`✗ Error: ${e.message}`);
      }
    }
    Logger.log('');
  });
  
  return emptyFolders;
}

// ============================================================================
// UTILITIES
// ============================================================================

/**
 * Format bytes to human-readable string
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get total Drive storage usage
 */
function getStorageInfo() {
  const user = Session.getActiveUser().getEmail();
  Logger.log('='.repeat(60));
  Logger.log(`Storage info for: ${user}`);
  Logger.log('='.repeat(60));
  
  // Note: Apps Script can't directly access quota info
  // This counts file sizes instead
  
  let totalSize = 0;
  let fileCount = 0;
  const files = DriveApp.getFiles();
  
  while (files.hasNext()) {
    const file = files.next();
    totalSize += file.getSize();
    fileCount++;
  }
  
  Logger.log(`Total files: ${fileCount}`);
  Logger.log(`Total size: ${formatBytes(totalSize)}`);
  Logger.log('');
  Logger.log('Note: This only counts files you own.');
  Logger.log('Check drive.google.com/settings/storage for official quota.');
}
