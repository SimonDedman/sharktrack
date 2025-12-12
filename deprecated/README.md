# Deprecated Scripts

**Last Updated:** October 6, 2025
**Status:** Archived for reference, scheduled for deletion on project completion

---

## Purpose

This folder contains scripts that were developed during the SharkTrack batch processing pipeline evolution but have been superseded by more efficient implementations. These scripts are kept for:

1. **Code reference** - Useful algorithms and patterns may be extracted
2. **Historical context** - Understanding the evolution of the pipeline
3. **Temporary backup** - Safety net during transition to new pipeline

**⚠️ These scripts should NOT be used in production.**

---

## Deprecated Scripts

### **Batch Processors (Superseded)**

#### `enhanced_batch_processor.py`
- **Status:** ❌ Deprecated (Sept 26, 2025)
- **Reason:** Overcomplicated with missing dependencies (`utils.resumable_processor`, `utils.dynamic_load_balancer`)
- **Replaced by:** `simple_batch_processor_v2.py`
- **Useful code:** Dynamic load balancing concepts, resumption logic

#### `simple_batch_processor.py`
- **Status:** ❌ Deprecated (Sept 28, 2025)
- **Reason:** First iteration, lacking preset modes
- **Replaced by:** `simple_batch_processor_v2.py`
- **Useful code:** Deletion policy integration, disk space monitoring

#### `process_all_bruv_data.py`
- **Status:** ❌ Deprecated (Sept 26, 2025)
- **Reason:** Early prototype, superseded by batch processors
- **Replaced by:** `simple_batch_processor_v2.py`
- **Useful code:** Basic batch iteration patterns

---

### **Parallel Analysis (Superseded)**

#### `parallel_sharktrack_simple.py`
- **Status:** ❌ Deprecated (Sept 28, 2025)
- **Reason:** Early parallel analysis prototype
- **Replaced by:** `parallel_sharktrack_analysis.py`
- **Useful code:** Basic ThreadPoolExecutor patterns

#### `test_parallel_simple.py`
- **Status:** ❌ Deprecated (Sept 28, 2025)
- **Reason:** Test script, no longer needed
- **Replaced by:** N/A (testing code)
- **Useful code:** Testing patterns for parallel processing

---

### **Cleanup Utilities (One-Time Use)**

#### `restore_converted_videos.py`
- **Status:** ⚠️ Deprecated (Sept 29, 2025)
- **Reason:** Created to fix corrupted drive workflow, not needed with clean `--convert-replace` workflow
- **Use case:** Drive recovery only
- **Useful code:**
  - File restoration logic
  - Dry-run mode for read-only filesystems
  - I/O error handling with directory workarounds

#### `reorganize_analysis_results.py`
- **Status:** ⚠️ Deprecated (Sept 28, 2025)
- **Reason:** Fixed worker-based folder issue, modern pipeline places results correctly from start
- **Use case:** Legacy cleanup only
- **Useful code:**
  - Directory mapping logic
  - Video-to-BRUV directory matching

#### `restore_videos_simple.sh`
- **Status:** ❌ Deprecated (Sept 28, 2025)
- **Reason:** Shell wrapper for `restore_converted_videos.py`
- **Replaced by:** Direct Python script execution
- **Useful code:** Shell script patterns

#### `process_bruv_data.sh`
- **Status:** ❌ Deprecated (Sept 16, 2025)
- **Reason:** Early shell-based approach
- **Replaced by:** Python batch processors
- **Useful code:** Basic shell automation patterns

---

### **Demo/Example Code**

#### `demo_deletion_policy.py`
- **Status:** ❌ Deprecated (Sept 26, 2025)
- **Reason:** Demonstration code, integrated into main batch processors
- **Replaced by:** Deletion policy in `simple_batch_processor_v2.py`
- **Useful code:**
  - Deletion policy logic
  - Interactive prompting patterns

---

## Lessons Learned

### **What Worked:**
1. **Parallel processing** - ThreadPoolExecutor with auto-balancing workers
2. **Subprocess isolation** - Prevents ML worker crashes from affecting main process
3. **Preset modes** - Simplified UX (--convert-replace, --convert-only, --analyze-only)
4. **Direct directory placement** - Analysis results go to BRUV folders, not worker folders

### **What Didn't Work:**
1. **Complex dependencies** - `utils.*` modules that didn't exist
2. **Worker-based folders** - Created artificial organization that needed cleanup
3. **Overly complex progress monitoring** - Initial versions had blocking issues
4. **13-parameter interfaces** - Confusing, reduced to 3 preset modes

### **Issues from Corrupted Drive:**
1. **Read-only filesystems** - Created need for dry-run modes and restoration scripts
2. **I/O errors** - Required workarounds to access partial directories
3. **Incomplete restoration** - Led to sophisticated backup/restore logic
4. **File integrity concerns** - Ultra-high compression ratios (400-800:1) indicated corruption

---

## Migration Path

### **From Old Scripts → New Scripts:**

| Old Script | New Script | Migration Notes |
|-----------|-----------|----------------|
| `enhanced_batch_processor.py` | `simple_batch_processor_v2.py` | Use `--convert-replace` preset |
| `simple_batch_processor.py` | `simple_batch_processor_v2.py` | Switch to preset modes |
| `parallel_sharktrack_simple.py` | `parallel_sharktrack_analysis.py` | No changes needed |
| `process_all_bruv_data.py` | `simple_batch_processor_v2.py` | Use `--analyze-only` preset |
| `restore_converted_videos.py` | N/A | Not needed with clean workflow |
| `reorganize_analysis_results.py` | N/A | Results placed correctly from start |

---

## Deletion Schedule

**Phase 1 (Current):** Scripts moved to `deprecated/` folder
**Phase 2 (After verification):** Confirm new pipeline works with new SSD
**Phase 3 (Project completion):** Delete `deprecated/` folder entirely

**Deletion criteria:**
- ✅ New pipeline successfully processes all 386 videos
- ✅ Analysis results validated and consolidated
- ✅ No issues found requiring old script reference
- ✅ Project considered "complete"

---

## Notes

- **Do not import** from these scripts in new code
- **Do not modify** these scripts (they are archived)
- **Do extract** useful code patterns if needed, with comments noting the source
- **Do delete** this entire folder once project is complete

---

## Active Pipeline Reference

**Current production scripts:**
1. `../parallel_sharktrack_analysis.py` - Primary ML analysis
2. `../simple_batch_processor_v2.py` - Simplified batch wrapper

**Documentation:**
- `../docs/01-core-system/PIPELINE_DOCUMENTATION.md` - Complete pipeline guide
- `../docs/01-core-system/SETUP_AND_USAGE.md` - Setup and usage instructions
