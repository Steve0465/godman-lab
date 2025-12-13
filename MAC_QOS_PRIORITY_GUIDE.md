# Mac Upload Traffic Priority Guide (QoS Setup)

## Step 1: Find Your Mac's MAC Address

**macOS 13+ (Ventura/Sonoma/Sequoia):**
1. Open **System Settings** (Apple menu → System Settings)
2. Click **Network** (left sidebar)
3. Select your active connection (Wi-Fi or Ethernet with green dot)
4. Click **Details** button
5. Click **Hardware** tab
6. **MAC Address** (or "Wi-Fi Address"/"Ethernet ID") is shown - format: `XX:XX:XX:XX:XX:XX`

**macOS 12 and earlier:**
- System Preferences → Network → Advanced → Hardware

**Quick Terminal method:**
```bash
# Ethernet
ifconfig en0 | grep ether
# Wi-Fi
ifconfig en1 | grep ether
```

Write down this MAC address - you'll need it for router configuration.

---

## Step 2: Access Router QoS Settings

### Common Router UI Locations

**ISP Gateway (AT&T, Xfinity, Spectrum, Verizon):**
- Login: Usually `192.168.1.1` or `10.0.0.1` (check sticker on router)
- Navigate to: **Advanced** → **Quality of Service (QoS)** or **Traffic Management**
- Some gateways have limited QoS - consider bridge mode + dedicated router

**Netgear (Nighthawk, Orbi):**
- Navigate: **Advanced** → **Setup** → **QoS Setup** or **Smart Queue Management**
- Or: **Advanced** → **Traffic Meter** → **QoS**

**TP-Link (Archer, Deco):**
- Navigate: **Advanced** → **QoS** → **Application Priority** or **Device Priority**
- Or: **HomeCare** → **QoS** (on newer models)

**Asus (RT-series, ZenWiFi):**
- Navigate: **QoS** → **Adaptive QoS** or **Traditional QoS**
- Or: **Traffic Manager** → **QoS**

**Eero (app-based):**
- Eero app → Settings → **eero Labs** → **Optimize for Conferencing and Gaming**
- Or: Network Settings → **Device Details** → (select Mac) → **Prioritize**
- Note: Eero uses simplified automatic QoS

**Google WiFi/Nest WiFi (app-based):**
- Google Home app → WiFi → Settings → **Advanced Networking** → **Device Priority**

---

## Step 3: Enable & Configure QoS

### A. Enable QoS (if disabled)
1. Toggle **QoS** or **Smart Queue** to **ON/Enabled**
2. If prompted for bandwidth speeds:
   - **Upload speed**: Enter 85-95% of your actual upload speed (run speedtest.net first)
   - **Download speed**: Enter 85-95% of actual download speed
   - *Why 85-95%?: Leaves headroom for QoS to manage traffic effectively*

### B. Add Device Priority Rule

**Method 1: By MAC Address (Most Reliable)**
1. Look for **Add Device** or **Device Priority** section
2. Select **Add by MAC Address** or **Manual Entry**
3. Enter your Mac's MAC address from Step 1
4. Give it a friendly name (e.g., "MacBook Pro")
5. Set priority to **High** or **Highest** (or similar: Priority 1, Critical, etc.)
6. **Important**: Look for separate Upload/Download priority - set **Upload** to highest
7. Save/Apply changes

**Method 2: From Connected Devices List**
1. Find **Connected Devices** or **Client List** section
2. Locate your Mac by name or MAC address
3. Click device → **Edit** or **Priority**
4. Set to **High/Highest** priority
5. Save/Apply

**Priority Naming Variations:**
- Netgear: Highest → High → Normal → Low
- TP-Link: High Priority → Normal → Low
- Asus: 0 (highest) → 1 → 2 → 3 (lowest), or Gaming/Streaming/Default
- Eero: Prioritize for X hours (automatically expires)

---

## Step 4: Adjust Smart Queue Bandwidth Caps

**Goal**: Let QoS prioritize, but don't artificially throttle your connection

**Option A: Set to Near-Maximum (Recommended)**
1. Find **Bandwidth Limit** or **Upload/Download Speed** settings within QoS
2. Set Upload: **90-95%** of your actual speed (e.g., 950 Mbps if you have 1 Gbps)
3. Set Download: **90-95%** of actual speed
4. This allows QoS to work without severe throttling

**Option B: Disable Bandwidth Caps (if available)**
1. Some routers allow **Automatic** or **Unlimited** mode
2. Look for: "Auto-detect bandwidth" or "No limit" option
3. QoS will still prioritize your Mac without hard caps

**Don't do**: Completely disable QoS - you'll lose device prioritization

**Netgear Smart Queue specific:**
- Can toggle "Bandwidth Control" to OFF while keeping device priority
- Or set very high caps (e.g., 10 Gbps if unrealistic for your plan)

---

## Step 5: Physical Connection Optimization

### Ethernet Connection Best Practices

**A. Connect to Main Router (Not Mesh Node)**
- Mesh satellites/nodes add latency and reduce bandwidth
- Run Ethernet directly to the primary router/gateway
- If using mesh: Disable Wi-Fi on Mac, use Ethernet to main unit

**B. Use Fastest Available Port**
1. Identify router ports (check back panel or manual):
   - **2.5G port** (if available): Best choice - usually labeled "2.5G WAN/LAN"
   - **Gigabit port** (1G): Standard on most modern routers
   - Avoid 100 Mbps (Fast Ethernet) ports - usually yellow/older routers
   
2. Common port layouts:
   - **WAN/Internet port**: Don't use this (connects to modem)
   - **LAN ports 1-4**: Use any LAN port
   - **Gaming/Fastest port**: Some routers label one port for gaming (use this)
   - **2.5G Multi-Gig port**: Often can function as LAN (check manual)

3. Check Mac's Ethernet adapter speed:
   - System Settings → Network → Ethernet → Details → Hardware
   - Should show "1000baseT" (1G) or "2.5GbaseT" (2.5G)
   - If showing "100baseTX", check cable quality (use Cat5e or better)

**C. Cable Quality**
- Use **Cat6 or Cat6a** cable (supports 10G short distances)
- Cat5e minimum for 1G speeds
- Keep cable length under 100m (330ft)

---

## Step 6: Verification & Testing

### A. Pre-Test Upload Speed (Baseline)
1. Visit **speedtest.net** or **fast.com**
2. Run test, note **Upload speed** (e.g., 35 Mbps)
3. Take screenshot or write it down

### B. Apply QoS Settings
- Save all router changes
- Reboot router if prompted (some require this)
- Wait 2-3 minutes for settings to apply

### C. Re-Test Upload Speed
1. Run speedtest again
2. Upload should be similar (within 10-15% of baseline)
3. If drastically lower (>30% drop), increase bandwidth cap in QoS

### D. Real-World Upload Test
**Stress test while monitoring:**

1. **Start a large upload** (pick one):
   - Upload 500MB+ file to Google Drive/Dropbox
   - Start iCloud Photo Library sync (if you have large library)
   - Zoom/FaceTime call while screen sharing

2. **Monitor real-time throughput:**
   ```bash
   # Terminal command - check upload activity
   nettop -n -c -l 1 -P
   # Press 'q' to quit
   ```

3. **Router-side monitoring:**
   - Some routers have **Traffic Monitor** or **Bandwidth Monitor**
   - Check if your Mac shows high priority traffic lanes

4. **Expected behavior with QoS:**
   - Your Mac uploads should maintain speed during congestion
   - Other devices' uploads may slow if you're maxing the connection
   - Latency/ping should stay stable during uploads

---

## Troubleshooting

**Upload speed heavily throttled after enabling QoS:**
- Increase bandwidth cap to 95% or disable cap
- Check if "Download QoS" is affecting upload (some routers confuse bidirectional settings)

**Mac not appearing in device list:**
- Ensure Mac is actively connected (send some traffic)
- Use MAC address manual entry method
- Check if MAC randomization is enabled (Wi-Fi only): Settings → Network → Wi-Fi → Details → Limit IP Address Tracking (turn OFF)

**QoS not prioritizing:**
- Verify QoS is enabled globally (not just device added)
- Reboot router after changes
- Check firmware update available
- Some ISP gateways have neutered QoS - consider bridge mode

**Ethernet negotiating at 100 Mbps instead of 1000 Mbps:**
- Replace Ethernet cable (needs Cat5e minimum)
- Try different LAN port on router
- Check Mac's Ethernet adapter settings: System Settings → Network → Ethernet → Details → Hardware → Configure: Automatic

**Eero priority expires:**
- Eero auto-disables priority after set hours
- Re-enable through app, or use Eero Secure subscription for persistent rules

---

## Summary Checklist

- [ ] Found Mac's MAC address (System Settings → Network → Details → Hardware)
- [ ] Logged into router admin panel
- [ ] Enabled QoS/Smart Queue
- [ ] Added Mac by MAC address with **High/Highest** priority
- [ ] Set Upload priority specifically (if separate from download)
- [ ] Set bandwidth caps to 90-95% of actual speeds (or disabled caps)
- [ ] Connected Ethernet to **main router** (not mesh node)
- [ ] Used **fastest available LAN port** (2.5G > 1G)
- [ ] Verified Ethernet negotiated at 1000baseT or higher
- [ ] Ran upload speed test (before/after)
- [ ] Tested real upload with monitoring

---

## Safety Notes

✅ **Safe to do:**
- Enable/disable QoS
- Add device priorities
- Adjust bandwidth caps
- Change Ethernet ports

❌ **Avoid unless necessary:**
- Factory reset router
- Firmware updates (unless solving specific issue)
- Changing WAN settings
- Disabling firewall/security features

---

**Need to revert?** Simply disable QoS or remove device priority rule - no permanent changes made.
