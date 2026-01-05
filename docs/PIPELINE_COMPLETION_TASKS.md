# Pipeline Completion Tasks

## Current Status

### ✅ **Implemented**
1. Project selection with codeword naming
2. Import from ingest pool (no duplicates)
3. Audio normalization
4. Transcription (SRT + JSON)
5. Audio marker detection
6. Segment extraction
7. Rough cut generation
8. Resolve project setup
9. Udev script integration

### ⚠️ **Issues Found**

#### 1. **Proxy Generation Bug** (Line 271)
**Problem:** `import_result` is undefined when `from_ingest=True`
- Line 271: `proxy_count = import_result.get("proxies_created", 0)`
- But `import_result` only exists when importing from SD card (line 249)
- When `from_ingest=True`, `import_result` doesn't exist

**Fix Needed:** Track proxy count separately or generate proxies after import

#### 2. **Config Path Issue** (AutoImportService)
**Problem:** `/mnt/render/Proxies` doesn't exist or has permission issues
- AutoImportService tries to create proxy_dir at init
- Should use project-specific proxy directory instead

**Fix Needed:** Use project path for proxies, not global render directory

#### 3. **Camera Detection for Ingest Pool**
**Problem:** Hardcoded to "FX30" when `from_ingest=True`
- Should detect from file patterns or metadata

**Fix Needed:** Better camera detection from files

#### 4. **Rough Cut Generation**
**Problem:** May not work correctly if clips don't have markers
- Should handle cases with/without markers gracefully

**Fix Needed:** Verify rough cut works with and without markers

#### 5. **Resolve Setup**
**Problem:** May fail silently if Resolve not running
- Should provide clear feedback

**Fix Needed:** Better error handling and user feedback

---

## Tasks to Complete

### **Priority 1: Critical Bugs**

#### Task 1: Fix Proxy Generation Bug
**File:** `studioflow/core/unified_import.py` (line 271)

**Issue:** `import_result` undefined when `from_ingest=True`

**Fix:**
```python
# After importing files, generate proxies
if from_ingest:
    # Generate proxies after import
    proxy_count = self._generate_proxies(imported_files, project.path, profile)
else:
    proxy_count = import_result.get("proxies_created", 0)
```

#### Task 2: Fix Config Path Issues
**File:** `studioflow/core/auto_import.py` (line 77)

**Issue:** Tries to create `/mnt/render/Proxies` which may not exist

**Fix:** Use project-specific proxy directory, don't create at init

#### Task 3: Add Proxy Generation Method
**File:** `studioflow/core/unified_import.py`

**Issue:** No `_generate_proxies` method when `from_ingest=True`

**Fix:** Add method to generate proxies from imported files

---

### **Priority 2: Enhancements**

#### Task 4: Better Camera Detection
**File:** `studioflow/core/unified_import.py` (line 218)

**Issue:** Hardcoded "FX30" for ingest pool

**Fix:** Detect camera from file patterns or metadata

#### Task 5: Improve Error Handling
**File:** `studioflow/core/unified_import.py`

**Issue:** Errors may be swallowed

**Fix:** Better logging and user feedback

#### Task 6: Verify Rough Cut Integration
**File:** `studioflow/core/unified_import.py` (line 290)

**Issue:** May not work correctly

**Fix:** Test and verify rough cut generation

---

### **Priority 3: Testing & Validation**

#### Task 7: End-to-End Test
**Test:** Full pipeline with real SD card

**Steps:**
1. Insert SD card with codeword label
2. Verify udev triggers
3. Verify project created
4. Verify all steps complete
5. Verify project ready for editing

#### Task 8: Error Scenario Testing
**Test:** Various failure modes

**Scenarios:**
- SD card with no label
- SD card with no video files
- Resolve not running
- Transcription fails
- No markers detected

---

## Implementation Order

1. **Fix proxy generation bug** (Critical - breaks pipeline)
2. **Fix config path issues** (Critical - breaks initialization)
3. **Add proxy generation method** (Required for from_ingest)
4. **Test end-to-end** (Verify everything works)
5. **Enhancements** (Nice to have)

---

## Estimated Time

- **Critical fixes:** 30 minutes
- **Testing:** 1 hour
- **Enhancements:** 1 hour
- **Total:** ~2.5 hours

---

## Next Steps

1. Fix proxy generation bug
2. Fix config path issues
3. Add missing proxy generation
4. Test with real SD card
5. Document any remaining issues

