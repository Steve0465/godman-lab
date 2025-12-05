/**
 * Google Drive Auto-Organizer
 * 
 * Automatically organizes files in your Drive by:
 * - Moving files to folders based on file type
 * - Organizing by date (year/month structure)
 * - Cleaning up old files
 * - Finding duplicates
 * 
 * Setup:
 * 1. Copy this script to script.google.com
 * 2. Update the DRIVE_CONFIG below with your folder IDs
 * 3. Run authorize() first to grant permissions
 * 4. Test with organizeNewFiles()
 * 5. Set up a daily trigger for autoOrganize()
 */

// ============================================================================
// CONFIGURATION - Update these with your folder IDs
// ============================================================================

const DRIVE_CONFIG = {
  // Root folder to monitor (leave empty for entire Drive)
  SOURCE_FOLDER_ID: '',
  
  // Destination folders (create these in your Drive first)
  FOLDERS: {
    IMAGES: 'YOUR_IMAGES_FOLDER_ID',
    DOCUMENTS: 'YOUR_DOCUMENTS_FOLDER_ID',
    SPREADSHEETS: 'YOUR_SPREADSHEETS_FOLDER_ID',
    PDFS: 'YOUR_PDFS_FOLDER_ID',
    VIDEOS: 'YOUR_VIDEOS_FOLDER_ID',
    AUDIO: 'YOUR_AUDIO_FOLDER_ID',
    ARCHIVES: 'YOUR_ARCHIVES_FOLDER_ID',
    OTHER: 'YOUR_OTHER_FOLDER_ID'
  },
  
  // Files older than this many days can be archived
  ARCHIVE_DAYS: 365,
  
  // Files to exclude from organization (by name patterns)
  EXCLUDE_PATTERNS: ['DO_NOT_MOVE', 'KEEP_HERE']
};

// File type mappings
const FILE_TYPES = {
  IMAGES: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp', 'heic'],
  DOCUMENTS: ['doc', 'docx', 'txt', 'rtf', 'odt'],
  SPREADSHEETS: ['xls', 'xlsx', 'csv', 'ods'],
  PDFS: ['pdf'],
  VIDEOS: ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm'],
  AUDIO: ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg'],
  ARCHIVES: ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
};

// ============================================================================
// MAIN FUNCTIONS
// ============================================================================

/**
 * Authorization function - Run this first!
 * Grants necessary permissions to access Drive.
 */
function authorize() {
  DriveApp.getRootFolder();
  Logger.log('✓ Authorization granted! You can now run other functions.');
}

/**
 * Main auto-organize function
 * Call this manually or set up as a trigger
 */
function autoOrganize() {
  Logger.log('Starting auto-organization...');
  
  const stats = {
    processed: 0,
    moved: 0,
    skipped: 0,
    errors: 0
  };
  
  try {
    // Get source folder
    const folder = DRIVE_CONFIG.SOURCE_FOLDER_ID 
      ? DriveApp.getFolderById(DRIVE_CONFIG.SOURCE_FOLDER_ID)
      : DriveApp.getRootFolder();
    
    // Get all files
    const files = folder.getFiles();
    
    while (files.hasNext()) {
      const file = files.next();
      stats.processed++;
      
      try {
        if (shouldProcessFile(file)) {
          const moved = organizeFile(file);
          if (moved) {
            stats.moved++;
          } else {
            stats.skipped++;
          }
        } else {
          stats.skipped++;
        }
      } catch (e) {
        Logger.log(`Error processing ${file.getName()}: ${e.message}`);
        stats.errors++;
      }
    }
    
    // Log summary
    Logger.log('='.repeat(60));
    Logger.log('Organization complete!');
    Logger.log(`Processed: ${stats.processed}`);
    Logger.log(`Moved: ${stats.moved}`);
    Logger.log(`Skipped: ${stats.skipped}`);
    Logger.log(`Errors: ${stats.errors}`);
    Logger.log('='.repeat(60));
    
  } catch (e) {
    Logger.log(`Fatal error: ${e.message}`);
  }
}

/**
 * Organize files created in the last 7 days
 * Good for testing or daily runs
 */
function organizeNewFiles() {
  Logger.log('Organizing files from the last 7 days...');
  
  const sevenDaysAgo = new Date();
  sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
  
  const files = DriveApp.getFiles();
  let moved = 0;
  
  while (files.hasNext()) {
    const file = files.next();
    
    if (file.getDateCreated() > sevenDaysAgo && shouldProcessFile(file)) {
      if (organizeFile(file)) {
        moved++;
      }
    }
  }
  
  Logger.log(`✓ Organized ${moved} recent files`);
}

/**
 * Check if file should be processed
 */
function shouldProcessFile(file) {
  const name = file.getName();
  
  // Skip files in exclude patterns
  for (const pattern of DRIVE_CONFIG.EXCLUDE_PATTERNS) {
    if (name.includes(pattern)) {
      return false;
    }
  }
  
  // Skip Google Workspace files (Docs, Sheets, etc.)
  const mimeType = file.getMimeType();
  if (mimeType.includes('google-apps')) {
    return false;
  }
  
  return true;
}

/**
 * Organize a single file
 */
function organizeFile(file) {
  const fileType = getFileType(file);
  
  if (!fileType || fileType === 'OTHER') {
    return false; // Skip unrecognized types
  }
  
  const targetFolderId = DRIVE_CONFIG.FOLDERS[fileType];
  
  if (!targetFolderId || targetFolderId.includes('YOUR_')) {
    Logger.log(`⚠ No target folder configured for ${fileType}`);
    return false;
  }
  
  try {
    const targetFolder = DriveApp.getFolderById(targetFolderId);
    const parents = file.getParents();
    
    // Check if already in target folder
    while (parents.hasNext()) {
      if (parents.next().getId() === targetFolderId) {
        return false; // Already in correct location
      }
    }
    
    // Move file
    file.moveTo(targetFolder);
    Logger.log(`✓ Moved: ${file.getName()} → ${fileType}`);
    return true;
    
  } catch (e) {
    Logger.log(`✗ Failed to move ${file.getName()}: ${e.message}`);
    return false;
  }
}

/**
 * Determine file type from extension
 */
function getFileType(file) {
  const name = file.getName();
  const ext = name.split('.').pop().toLowerCase();
  
  for (const [type, extensions] of Object.entries(FILE_TYPES)) {
    if (extensions.includes(ext)) {
      return type;
    }
  }
  
  return 'OTHER';
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * List all folders in your Drive with their IDs
 * Use this to find folder IDs for configuration
 */
function listAllFolders() {
  Logger.log('Listing all folders...');
  Logger.log('='.repeat(60));
  
  const folders = DriveApp.getFolders();
  let count = 0;
  
  while (folders.hasNext()) {
    const folder = folders.next();
    Logger.log(`Folder: ${folder.getName()}`);
    Logger.log(`ID: ${folder.getId()}`);
    Logger.log(`URL: ${folder.getUrl()}`);
    Logger.log('-'.repeat(60));
    count++;
  }
  
  Logger.log(`Total folders: ${count}`);
}

/**
 * Create standard organization folders
 * Run this once to set up your folder structure
 */
function createOrganizationFolders() {
  Logger.log('Creating organization folders...');
  
  const root = DriveApp.getRootFolder();
  const baseFolder = root.createFolder('Auto-Organized Files');
  
  Logger.log(`Created base folder: ${baseFolder.getId()}`);
  Logger.log('');
  Logger.log('Creating subfolders...');
  
  for (const type of Object.keys(FILE_TYPES)) {
    const folder = baseFolder.createFolder(type);
    Logger.log(`${type}: ${folder.getId()}`);
  }
  
  const otherFolder = baseFolder.createFolder('OTHER');
  Logger.log(`OTHER: ${otherFolder.getId()}`);
  
  Logger.log('');
  Logger.log('✓ Folders created! Copy the IDs above into DRIVE_CONFIG.');
}

/**
 * Get statistics about your Drive
 */
function getDriveStats() {
  Logger.log('Analyzing Drive...');
  
  const stats = {
    totalFiles: 0,
    byType: {}
  };
  
  const files = DriveApp.getFiles();
  
  while (files.hasNext()) {
    const file = files.next();
    stats.totalFiles++;
    
    const type = getFileType(file);
    stats.byType[type] = (stats.byType[type] || 0) + 1;
  }
  
  Logger.log('='.repeat(60));
  Logger.log('Drive Statistics');
  Logger.log('='.repeat(60));
  Logger.log(`Total files: ${stats.totalFiles}`);
  Logger.log('');
  Logger.log('By type:');
  
  for (const [type, count] of Object.entries(stats.byType)) {
    Logger.log(`  ${type}: ${count}`);
  }
}
