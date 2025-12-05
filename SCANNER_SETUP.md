# Scanner Auto-Save Setup

## 📱 Configure Your Printer/Scanner to Save to Your Repo

### Option 1: macOS Default Scanner Location

1. **Set Default Save Location:**
   ```bash
   # The scans folder in your repo
   ~/godman-lab/scans/
   ```

2. **macOS Image Capture Settings:**
   - Open **Image Capture** app
   - Select your scanner/printer
   - Click "Scan To:" dropdown
   - Choose "Other..." 
   - Navigate to: `/Users/stephengodman/godman-lab/scans`
   - Save

3. **Format Settings:**
   - Format: PDF or JPEG
   - Name: Use date/time stamp
   - Auto-save enabled

---

### Option 2: Create Symlink (Easiest!)

Make any folder point to your repo:

```bash
# Remove default scan location (if exists)
rm -rf ~/Documents/Scanned\ Documents

# Create symlink to your repo
ln -s ~/godman-lab/scans ~/Documents/Scanned\ Documents

# Now all scans go directly to your repo!
```

---

### Option 3: Folder Action (Auto-Move)

Create an Automator script that automatically moves scanned files:

1. **Create Folder Action:**
   - Open **Automator**
   - New Document → Folder Action
   - Choose folder: (default scan location)
   - Add action: "Move Finder Items"
   - Destination: `~/godman-lab/scans`
   - Save as: "Auto-Move Scans"

2. **Attach to Folder:**
   - Right-click your scan folder
   - Services → Folder Actions Setup
   - Enable folder actions
   - Add your script

---

### Option 4: Specific Printer Setup

#### HP Printers:
1. Open **HP Smart** or **HP Easy Scan**
2. Settings → Save Location
3. Set to: `/Users/stephengodman/godman-lab/scans`

#### Canon Printers:
1. Open **Canon IJ Scan Utility**
2. Settings → Save Settings
3. Set to: `/Users/stephengodman/godman-lab/scans`

#### Epson Printers:
1. Open **Epson Scan 2**
2. Settings → File Save Settings
3. Set to: `/Users/stephengodman/godman-lab/scans`

#### Brother Printers:
1. Open **ControlCenter**
2. Scan Settings
3. Destination: `/Users/stephengodman/godman-lab/scans`

---

### 🔄 Auto-Processing Workflow

Once files land in `~/godman-lab/scans`, they'll be automatically:

1. **Picked up by receipt processor:**
   ```bash
   python process_receipts.py
   ```

2. **Or processed by document organizer:**
   ```bash
   python organize_documents.py scans/
   ```

3. **Set up automatic processing** (optional):
   ```bash
   # Add to crontab (run every hour)
   0 * * * * cd ~/godman-lab && python process_receipts.py
   ```

---

### 📁 Recommended Folder Structure

```
~/godman-lab/
├── scans/                    ← Scanner saves here
│   ├── (auto-processed)
│
├── receipts/                 ← Processed receipts go here
│   └── 2024/12/VENDOR/
│
├── organized_documents/      ← Organized docs go here
│   ├── BILLS/
│   ├── TAXES/
│   └── RECEIPTS/
```

---

### ⚡ Quick Setup (Recommended)

Run this one command:

```bash
# Create symlink for easy scanning
ln -sf ~/godman-lab/scans ~/Documents/Scanned\ Documents

# Set it as default in System Settings
echo "Now set your scanner to save to: Documents/Scanned Documents"
```

Then in your **System Settings → Printers & Scanners:**
- Select your printer/scanner
- Set default save location to: `Documents/Scanned Documents`

All scans will now automatically go to your repo! 🎉

---

### 🧪 Test It

1. Scan a test document
2. Check if it appears in `~/godman-lab/scans/`
3. Run: `python process_receipts.py`
4. Verify it gets organized

---

### 🔧 Troubleshooting

**Scans not appearing?**
- Check scanner software settings
- Verify folder permissions: `ls -la ~/godman-lab/scans`
- Try creating a test file: `touch ~/godman-lab/scans/test.pdf`

**Permission denied?**
```bash
chmod 755 ~/godman-lab/scans
```

**Want to use different location?**
Update `.env` file:
```bash
INPUT_DIR=scans  # or your custom path
```

