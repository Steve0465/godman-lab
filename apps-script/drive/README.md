# Google Drive Automation Scripts

Powerful Apps Script tools for automatically organizing and cleaning up your Google Drive.

## 📁 What's Included

### 1. **autoOrganizer.gs** - Automatic File Organization
- Auto-sorts files by type (images, documents, PDFs, etc.)
- Organizes into folder structure
- Runs on a schedule or on-demand
- Skips Google Workspace files
- Configurable file type mappings

### 2. **cleanupTools.gs** - Drive Cleanup & Optimization
- Find and remove duplicate files
- Delete old/unused files
- Identify large files eating storage
- Clean up empty folders
- Storage analysis tools

## 🚀 Quick Start

### Step 1: Create Organization Folders

1. Go to https://script.google.com
2. Click "New Project"
3. Copy `autoOrganizer.gs` into the editor
4. Run `createOrganizationFolders()`
5. Check "Execution log" - copy the folder IDs

### Step 2: Configure

Update `DRIVE_CONFIG` in `autoOrganizer.gs`:

```javascript
const DRIVE_CONFIG = {
  SOURCE_FOLDER_ID: '',  // Leave empty for entire Drive
  
  FOLDERS: {
    IMAGES: 'paste-folder-id-here',
    DOCUMENTS: 'paste-folder-id-here',
    // ... etc
  }
};
```

### Step 3: Test

Run `organizeNewFiles()` to test on recent files (last 7 days)

### Step 4: Automate

Set up a daily trigger:
1. Click ⏰ "Triggers" in left sidebar
2. Click "+ Add Trigger"
3. Choose `autoOrganize`
4. Select "Time-driven" → "Day timer"
5. Set time (e.g., 2:00 AM)
6. Save

## 📋 Available Functions

### Auto-Organizer Functions

| Function | Description |
|----------|-------------|
| `authorize()` | Grant permissions (run first!) |
| `createOrganizationFolders()` | Set up folder structure |
| `autoOrganize()` | Organize all files |
| `organizeNewFiles()` | Organize files from last 7 days |
| `listAllFolders()` | List folders with IDs |
| `getDriveStats()` | Get file type statistics |

### Cleanup Functions

| Function | Description |
|----------|-------------|
| `findDuplicates()` | Find duplicate files |
| `removeDuplicates()` | Delete duplicates (keeps newest) |
| `findOldFiles()` | Find files older than X days |
| `deleteOldFiles()` | Delete old files |
| `findLargeFiles()` | Find files > X MB |
| `cleanupEmptyFolders()` | Remove empty folders |
| `getStorageInfo()` | Get storage usage stats |

## ⚙️ Configuration Options

### autoOrganizer.gs

```javascript
const DRIVE_CONFIG = {
  // Monitor specific folder or entire Drive
  SOURCE_FOLDER_ID: '',
  
  // Destination folders for each file type
  FOLDERS: { ... },
  
  // Days before archiving (future feature)
  ARCHIVE_DAYS: 365,
  
  // Exclude files with these patterns
  EXCLUDE_PATTERNS: ['DO_NOT_MOVE', 'KEEP_HERE']
};
```

### cleanupTools.gs

```javascript
const CLEANUP_CONFIG = {
  // Days before file is "old"
  OLD_FILE_DAYS: 365,
  
  // Minimum size for "large" file (MB)
  LARGE_FILE_MB: 100,
  
  // Use trash vs permanent delete
  USE_TRASH: true,
  
  // Test mode (doesn't actually delete)
  DRY_RUN: true  // Set to false to actually delete
};
```

## 🔒 Safety Features

- **Dry Run Mode**: Test cleanup without deleting (enabled by default)
- **Trash Instead of Delete**: Files go to trash, not permanently deleted
- **Confirmation Prompts**: Asks before deleting files
- **Exclude Patterns**: Protect specific files from moving
- **Skips Google Workspace**: Won't move Docs, Sheets, etc.

## 📊 Example Usage

### Organize Your Drive

```javascript
// Run once to set up folders
createOrganizationFolders();

// Get folder IDs and update DRIVE_CONFIG

// Test with recent files
organizeNewFiles();

// Organize everything
autoOrganize();
```

### Clean Up Storage

```javascript
// Find what's taking up space
findLargeFiles();
getStorageInfo();

// Find duplicates
findDuplicates();

// Remove duplicates (DRY_RUN = false to actually delete)
removeDuplicates();

// Clean up old files
findOldFiles();
deleteOldFiles();  // Careful!

// Remove empty folders
cleanupEmptyFolders();
```

## 🎯 Pro Tips

1. **Start Small**: Test with `organizeNewFiles()` before `autoOrganize()`
2. **Use Dry Run**: Always test cleanup functions with `DRY_RUN: true` first
3. **Check Logs**: Use `View → Logs` (Ctrl+Enter) to see results
4. **Schedule Off-Peak**: Run daily organizer at night (2-4 AM)
5. **Backup Important Files**: Before bulk deletes, backup critical files
6. **Review Duplicates**: Check duplicate list before removing
7. **Adjust Thresholds**: Tune `OLD_FILE_DAYS` and `LARGE_FILE_MB` for your needs

## ⚠️ Important Notes

- **Permissions**: Grant Drive access when prompted
- **Execution Time**: Large Drives may take time (Apps Script has 6-min limit per run)
- **Quota**: Script has daily quota limits (check quotas in Apps Script dashboard)
- **Google Files**: Google Docs/Sheets/Slides are skipped (can't organize by extension)
- **Shared Files**: Be careful with shared files - only owner can move them

## 🐛 Troubleshooting

**"Authorization required"**
- Run `authorize()` function first

**"Execution time exceeded"**
- Process files in smaller batches
- Run organizer more frequently (weekly instead of monthly)

**"Cannot find folder"**
- Check folder IDs in `DRIVE_CONFIG`
- Ensure folders exist and you have access

**Files not moving**
- Check `EXCLUDE_PATTERNS`
- Verify file isn't a Google Workspace file
- Check execution logs for errors

## 📈 What's Next?

- Add date-based organization (Year/Month folders)
- Smart categorization using file content
- Integration with other Google services
- Backup automation
- Sharing and permission management

## 🔗 Resources

- [Apps Script Documentation](https://developers.google.com/apps-script)
- [DriveApp Reference](https://developers.google.com/apps-script/reference/drive)
- [Apps Script Dashboard](https://script.google.com)
- [Google Drive API](https://developers.google.com/drive)

---

**Ready to organize your Drive?** Copy the scripts to script.google.com and get started!
