# Document Organizer - Advanced Features

## 🎉 New Features Added

### 1. 📅 Calendar Integration (`docs_calendar_sync.py`)

Automatically syncs bill due dates to Google Calendar.

**Features:**
- Creates calendar events for all bills with due dates
- Sets reminders (3 days before + 1 day before)
- Color-codes bills in red
- Includes amount and action details
- Email + popup notifications

**Usage:**
```bash
# Dry run first
python docs_calendar_sync.py organized_documents/document_analysis.csv --dry-run

# Actually sync to calendar
python docs_calendar_sync.py organized_documents/document_analysis.csv \
  --credentials ~/google-credentials.json
```

**Setup:**
1. Create Google Cloud project
2. Enable Google Calendar API
3. Create service account
4. Download JSON credentials
5. Run sync command

---

### 2. 📊 Visual Dashboard (`docs_dashboard.py`)

Interactive web dashboard for managing documents.

**Features:**
- 📋 Overview with pie charts and bar graphs
- ⚠️ Urgent items page with countdown timers
- 📊 Analytics with spending breakdowns
- 🔍 Full-text search across documents
- 📅 Timeline view of due dates
- Real-time metrics and KPIs

**Usage:**
```bash
streamlit run docs_dashboard.py
```

Opens at: http://localhost:8501

**Dashboard Tabs:**
1. **Overview** - Stats, charts, recent documents
2. **Urgent Items** - Bills needing attention with countdown
3. **Analytics** - Spending trends, category breakdowns
4. **Search** - Find documents by any field
5. **Timeline** - Visual calendar of due dates

---

## 🚀 Complete Workflow

### Step 1: Analyze Documents
```bash
python organize_documents.py "/path/to/scans" --output organized_documents
```

### Step 2: View Dashboard
```bash
streamlit run docs_dashboard.py
```

### Step 3: Sync to Calendar
```bash
python docs_calendar_sync.py organized_documents/document_analysis.csv
```

### Step 4: Get Reminders
- Calendar sends email alerts 3 days before due date
- Popup reminders 1 day before
- Dashboard shows countdown timers

---

## 📊 What You Get

### Organized Folder Structure
```
organized_documents/
├── BILLS/
│   ├── NEEDS_ACTION/              ← Urgent bills
│   └── (other bills)
├── TAXES/
├── RECEIPTS/
├── document_analysis.csv          ← Full report
└── dashboard screenshots/
```

### CSV Report Fields
- filename
- category
- action (URGENT/ACTION/REVIEW/ARCHIVE)
- summary
- due_date
- amount
- key_info (account numbers, etc.)
- action_required
- dest_folder

### Calendar Events
- Event title with amount
- Due date as all-day event
- Reminders at 3 days and 1 day
- Full description with file details
- Color-coded (red for bills)

---

## 💡 Pro Tips

1. **Run Weekly**: Process new documents weekly
2. **Check Dashboard**: Review urgent items daily
3. **Calendar Sync**: Sync once after processing
4. **Search Feature**: Use dashboard search for quick lookups
5. **Analytics**: Track spending trends monthly

---

## 🔜 Future Enhancements (Ready to Build)

- [ ] Auto-payment detection (match bank statements)
- [ ] Recurring bill tracking (compare month-to-month)
- [ ] Email alerts (weekly digest)
- [ ] Bank integration (auto-reconciliation)
- [ ] Tax preparation reports
- [ ] Document relationships (link invoices to payments)
- [ ] Predictive analytics
- [ ] Mobile app integration

---

## 📈 System Capabilities

**Document Types:**
✓ Bills & Invoices
✓ Tax Documents
✓ Receipts
✓ Contracts
✓ Insurance Documents
✓ Medical Records
✓ Bank Statements
✓ Legal Documents

**AI Analysis:**
✓ Document classification
✓ Due date extraction
✓ Amount extraction
✓ Action priority
✓ Key information
✓ Smart summaries

**Automation:**
✓ Auto-organization
✓ Calendar sync
✓ Reminder notifications
✓ Visual dashboard
✓ Search & filter
✓ Analytics & trends

---

## 🎯 Cost Estimate

- Document analysis: ~$0.02 per document
- Calendar API: Free
- Dashboard: Free (runs locally)
- 100 documents/month: ~$2/month

Very affordable for complete automation!

