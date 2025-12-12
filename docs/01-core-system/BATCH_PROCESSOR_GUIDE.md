# SharkTrack Batch Processor Guide

## Quick Start (3 Simple Commands)

### **Most Common: Convert & Replace Originals**
```bash
python3 simple_batch_processor_v2.py --convert-replace ./BRUV_videos
```
- ✅ **76% space savings** (279GB → 88GB in your case)
- ✅ **Files stay where you put them** (maintains BRUV directory structure)
- ✅ **One simple command** - no complex parameters

### **Safest: Convert & Keep Originals**
```bash
python3 simple_batch_processor_v2.py --convert-only ./BRUV_videos ./output
```
- ✅ **Originals preserved** in case you need them later
- ✅ **Converted videos** saved to separate output directory
- ❌ **Double storage** required (563GB total: 367GB + 196GB)

### **Analysis Only: Skip Conversion**
```bash
python3 simple_batch_processor_v2.py --analyze-only ./converted_videos ./results
```
- ✅ **Fast** - skips 4+ hour conversion process
- ✅ **Use this** when videos are already converted
- ✅ **Just runs SharkTrack ML analysis**

---

## Parameter Comparison

### **New Simplified Interface (RECOMMENDED)**
| Command | Parameters | Use Case |
|---------|------------|----------|
| `--convert-replace` | **1 required** | Most users: save space, maintain organization |
| `--convert-only` | **2 required** | Safety-first: keep originals as backup |
| `--analyze-only` | **2 required** | Already have converted videos |

### **Old Complex Interface (13 parameters!)**
| Parameter | Purpose | Conflicts With | Often Confusing |
|-----------|---------|----------------|------------------|
| `--input` | Input directory | - | ✅ Clear |
| `--output` | Output directory | `--in-place` | ⚠️ Redundant with in-place |
| `--workers` | CPU workers | `--optimize-workers` | ⚠️ Overlapping |
| `--skip-conversion` | Skip conversion | All conversion opts | ⚠️ Contradictory |
| `--delete-originals` | Delete policy | `--in-place` | ❌ Conflicting |
| `--in-place` | Replace originals | `--delete-originals` | ❌ Conflicting |
| `--plan-only` | Show plan only | - | ✅ Useful |
| `--optimize-workers` | Auto-optimize workers | `--workers` | ⚠️ Overlapping |
| `--performance-check` | Check system | - | ⚠️ Advanced only |
| `--auto-optimize` | Auto performance | - | ⚠️ Advanced only |
| `--gpu-accelerated` | Use GPU | - | ⚠️ Requires NVIDIA |
| `--gpu-workers` | GPU worker count | - | ⚠️ Advanced only |
| `--progress-monitoring` | Detailed progress | - | ✅ Useful |
| `--yes` | Skip prompts | - | ✅ Useful |

---

## Real-World Examples

### **Your Recent Processing (What Should Have Been Used)**

**What you used:**
```bash
python3 simple_batch_processor.py \
  --input "/media/simon/SSK SSD1/BRUV_Summer_2022_46_62" \
  --output "/media/simon/SSK SSD1/converted_output_final" \
  --workers 4 \
  --progress-monitoring \
  --delete-originals no \
  --yes
```

**What would have been simpler:**
```bash
python3 simple_batch_processor_v2.py --convert-replace \
  "/media/simon/SSK SSD1/BRUV_Summer_2022_46_62" \
  --monitoring --yes
```

**Results would be:**
- ✅ **Same 76% space savings** (367GB → 88GB)
- ✅ **Videos stay in familiar locations** (BRUV 46/, BRUV 47/, etc.)
- ✅ **No duplicate files** scattered around
- ✅ **No manual cleanup needed**

### **For Different User Scenarios**

**Graduate Student (Limited Storage):**
```bash
python3 simple_batch_processor_v2.py --convert-replace ./my_bruv_videos --yes
```

**Research Institution (Safety First):**
```bash
python3 simple_batch_processor_v2.py --convert-only ./raw_videos ./processed_videos
```

**Quick Analysis (Videos Already Converted):**
```bash
python3 simple_batch_processor_v2.py --analyze-only ./converted_videos ./analysis_output
```

---

## Advanced Options (Optional)

### **Workers (CPU Parallel Processing)**
```bash
--workers 8    # Use 8 CPU cores (default: auto-detect)
```

### **Detailed Progress Monitoring**
```bash
--monitoring   # Shows real-time progress, time estimates, ETA
```

### **Batch/Script Mode**
```bash
--yes         # Skip all confirmation prompts
```

---

## Common Mistakes to Avoid

### **❌ Using Old Complex Interface**
```bash
# DON'T: Too many confusing parameters
python3 simple_batch_processor.py --input ./videos --output ./out --delete-originals delete-all --in-place --progress-monitoring --workers 4 --yes
```

### **✅ Use Simple Presets Instead**
```bash
# DO: One clear preset
python3 simple_batch_processor_v2.py --convert-replace ./videos --monitoring --yes
```

### **❌ Conflicting Parameters**
```bash
# DON'T: These conflict with each other
--delete-originals delete-all --in-place
--skip-conversion --gpu-accelerated
--workers 4 --optimize-workers
```

### **✅ Clear Intent**
```bash
# DO: One preset = one clear intention
--convert-replace  # Replace originals, save space
--convert-only     # Keep originals, use more space
--analyze-only     # Already have converted videos
```

---

## Migration Guide

**If you have existing scripts using the old interface:**

| Old Command | New Simplified Command |
|-------------|------------------------|
| `--in-place --delete-originals delete-all` | `--convert-replace` |
| `--delete-originals no` | `--convert-only` |
| `--skip-conversion` | `--analyze-only` |
| `--progress-monitoring` | `--monitoring` |

**The new interface eliminates:**
- ❌ **Parameter conflicts** (in-place vs delete-originals)
- ❌ **Redundant options** (output dir with in-place)
- ❌ **Advanced-only switches** (GPU workers, performance checks)
- ❌ **Overlapping functionality** (workers vs optimize-workers)

**Future users get:**
- ✅ **3 clear presets** instead of 13 confusing parameters
- ✅ **Logical defaults** (auto-detect workers, basic monitoring)
- ✅ **Clear examples** for every use case
- ✅ **Impossible to create conflicting commands**