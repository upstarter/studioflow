# Udev Service vs Unified Import Pipeline

## Current Setup

### ✅ **Existing Udev Service** (Already Installed)
**Location:** `/etc/udev/rules.d/99-studioflow-import.rules`

**What It Does:**
1. Detects SD card insertion (USB or built-in slot)
2. Triggers `studioflow-card-import.sh` automatically
3. Script copies files to ingest pool: `/mnt/nas/Scratch/Ingest/{date}/`
4. Then calls `sf import unified` to run full pipeline

**Status:** ✅ Already installed and working

---

## Comparison

### **Option 1: Keep Udev Service (RECOMMENDED)**

**Pros:**
- ✅ **Automatic** - No manual command needed
- ✅ **Already installed** - Just works when you insert card
- ✅ **Backup** - Files copied to ingest pool first (safety net)
- ✅ **Integrated** - Already calls unified pipeline
- ✅ **Notifications** - Desktop notifications on completion

**Cons:**
- ⚠️ Double copy (ingest pool + project) - but this is actually good for backup
- ⚠️ Requires root for udev rules

**Current Flow:**
```
SD Card Inserted
  ↓
Udev Rule Triggers
  ↓
studioflow-card-import.sh runs
  ↓
1. Copy to /mnt/nas/Scratch/Ingest/{date}/ (backup)
  ↓
2. Run: sf import unified /mount/point (full pipeline)
  ↓
Complete: Project ready in /mnt/studio/PROJECTS/
```

---

### **Option 2: Manual Unified Import Only**

**Pros:**
- ✅ Single copy (no duplicate)
- ✅ More control
- ✅ No root required

**Cons:**
- ❌ Not automatic - must run command manually
- ❌ No backup to ingest pool
- ❌ No desktop notifications

**Flow:**
```
SD Card Inserted
  ↓
Manually run: sf import unified /media/user/SDCARD
  ↓
Complete: Project ready
```

---

## Recommendation: **Keep Udev Service + Unified Pipeline**

### Why This Is Best:

1. **Automatic** - Insert card, everything happens
2. **Safe** - Ingest pool is backup before processing
3. **Complete** - Full pipeline runs automatically
4. **Already Working** - No changes needed

### Current Integration Status:

✅ **Already Integrated!** The script at line 181-205 already calls:
```bash
sf import unified "$MOUNT_POINT" --codeword "$CODENAME"
```

So when you insert an SD card:
1. Udev detects it
2. Script copies to ingest pool (backup)
3. Script runs unified pipeline (full automation)
4. Project ready in `/mnt/studio/PROJECTS/`

---

## Optimization Opportunity

**Current:** Script copies to ingest, then unified import copies again from mount point

**Optimization:** Unified import could use ingest pool if files already copied

**Recommendation:** Keep current approach (double copy is fine for safety)

---

## What You Have Now

### ✅ **Automatic Workflow (When SD Card Inserted):**

1. **Udev detects** card insertion
2. **Script copies** to ingest pool (backup)
3. **Unified pipeline runs:**
   - Detects camera
   - Creates project (codeword-YYYYMMDD_Import)
   - Imports media
   - Normalizes audio
   - Generates proxies
   - Transcribes
   - Detects markers
   - Generates rough cut
   - Sets up Resolve
4. **Project ready** in `/mnt/studio/PROJECTS/`
5. **Notification** shows completion

### ✅ **Manual Workflow (If Needed):**

```bash
# Run unified import manually
sf import unified /media/user/SDCARD

# Or with explicit codeword
sf import unified /media/user/SDCARD --codeword compliant_ape
```

---

## Conclusion

**Best Approach: Keep Udev Service**

- ✅ Already installed and working
- ✅ Automatic - no manual steps
- ✅ Safe - backup to ingest pool
- ✅ Complete - full pipeline runs
- ✅ Integrated - already calls unified import

**No changes needed** - your current setup is optimal!

The udev service is the **trigger**, and the unified pipeline is the **engine**. They work together perfectly.


