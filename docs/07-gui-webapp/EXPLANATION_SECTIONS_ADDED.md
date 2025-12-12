# Parameter Explanations Added to GUI

## Summary

All three parameter explanations have been successfully added to the HTML GUI as expandable `<details>` sections. Users can now click "📖 What does this do?" or similar text to reveal detailed explanations with analogies, visual diagrams, and practical guidance.

---

## ✅ Completed Additions

### 1. Deployment Stability Threshold Explanation
**Location**: Analysis tab, after deployment threshold slider (lines 591-617)

**Content includes**:
- "Shakiness meter" concept
- Visual ASCII table showing motion scores for different camera activities:
  - Boat/humans: 0.30-0.50 → SKIP
  - Descending: 0.20-0.30 → SKIP
  - Landing: 0.15-0.20 → SKIP
  - Stable on seafloor: 0.05-0.12 → KEEP
- Real example from BRUV 52 (128 seconds deployment detected)
- When to adjust:
  - Increase to 0.20 if skipping too many stable frames
  - Decrease to 0.12 if still seeing surface humans
  - Keep at 0.15 (default) for first try

---

### 2. Training Epochs Explanation
**Location**: Classifier Training tab, after epochs input (lines 719-746)

**Content includes**:
- Definition: "One epoch = one complete pass through all training images"
- "Teaching a student" analogy:
  - Epoch 1: Show photos once → learns basic shapes
  - Epoch 10: Show 10 times → learns species differences
  - Epoch 25: Show 25 times → becomes expert
- Learning progression visualization (ASCII chart):
  ```
  Accuracy
   100%|              ___________
    90%|          ___/
    80%|      ___/
    70%|  ___/
    60%|_/
       └──────────────────────────
         5   10   15   20   25
              Epochs
  ```
- Training time estimates:
  - GPU: ~1.5 min/epoch (35 min total for 25 epochs)
  - CPU: ~12 min/epoch (5 hours total for 25 epochs)
- When to adjust:
  - Increase to 30-35: Small dataset (<50 images)
  - Keep at 25: Recommended default
  - Decrease to 15-20: Large dataset (>500 images), testing
  - Decrease to 10: Quick experiment

---

### 3. Batch Size Explanation
**Location**: Classifier Training tab, after batch size input (lines 758-801)

**Content includes**:
- Definition: "How many images the model processes together before updating"
- "Grading homework" analogy:
  - Batch 1: Grade 1 paper at a time (SLOW)
  - Batch 16: Grade 16 papers, then update gradebook (GOOD)
  - Batch 32: Grade 32 papers, then update gradebook (FAST, needs big desk)
- GPU memory requirements table:
  ```
  Batch Size    GPU Memory    Time/Epoch    Works On
  ─────────────────────────────────────────────────
      4           2 GB         2.5 min      Old GPUs, CPU
      8           3 GB         1.8 min      GTX 1060, laptops
     16           5 GB         1.4 min      GTX 1080, RTX 2060+ ✅
     32          10 GB         1.2 min      RTX 3090, A100
  ```
- CUDA out of memory troubleshooting:
  1. Try 16 first (default)
  2. If error, reduce to 8
  3. Still error? Try 4
- When to adjust:
  - Decrease to 8: Laptop GPU, "CUDA out of memory" error
  - Decrease to 4: Old GPU, CPU training
  - Increase to 32: High-end GPU (>10GB VRAM)
  - Keep at 16: Modern GPU, no errors
- Example calculation with 86 images:
  - Batch 16: 6 batches/epoch → 35 min (25 epochs)
  - Batch 8: 11 batches/epoch → 50 min (25 epochs)
  - Batch 4: 22 batches/epoch → 75 min (25 epochs)

---

## Implementation Details

### HTML Structure
All three explanations use the same pattern:

```html
<details style="margin-top: 10px;">
    <summary style="cursor: pointer; color: #4299e1; font-weight: 500;">
        📖 [Title/Question]
    </summary>
    <div style="padding: 15px; background: #f7fafc; border-radius: 6px; margin-top: 10px; font-size: 0.9em;">
        <!-- Explanation content -->
        <!-- Analogies, examples, ASCII diagrams, practical guidance -->
    </div>
</details>
```

### Visual Design
- **Blue clickable summary** (#4299e1) with book emoji 📖
- **Light gray background** (#f7fafc) for content area
- **Rounded corners** (6px border-radius) for modern look
- **Monospace `<pre>` blocks** for tables and diagrams
- **Nested lists** for step-by-step guidance
- **Bold keywords** for important concepts
- **Checkmark ✅** for recommended options

### User Experience
1. **Collapsed by default** - doesn't clutter interface
2. **Click to expand** - reveals detailed explanation on demand
3. **Self-contained** - each explanation includes all needed context
4. **Progressive disclosure** - basic info in tooltip (ℹ️), detailed info in details section
5. **Actionable guidance** - specific values and when to use them

---

## Content Sources

All explanations draw from the comprehensive documentation files:

1. **SIMPLE_EXPLANATIONS.md** - User-friendly analogies and examples
2. **PARAMETER_EXPLANATIONS.md** - Technical details and algorithms
3. **User's validation data** - Real examples (BRUV 52, Caribbean species dataset)

---

## Testing

To verify the additions work correctly:

1. **Start the web server**:
   ```bash
   cd /home/simon/Installers/sharktrack-1.5
   ./launch_gui.sh
   ```

2. **Open GUI** in Firefox: http://localhost:5000

3. **Test deployment threshold explanation**:
   - Go to Analysis tab
   - Scroll to "Advanced Features" section
   - Look for "Deployment Stability Threshold" slider
   - Click "📖 What does this do?" below the slider
   - Should expand to show motion score table and guidance

4. **Test epochs explanation**:
   - Go to Classifier Training tab
   - Scroll to "Training Epochs" input
   - Click "📖 What is an epoch?" below the input
   - Should expand to show learning analogy and progression chart

5. **Test batch size explanation**:
   - Still in Classifier Training tab
   - Scroll to "Batch Size" input
   - Click "📖 What is batch size?" below the input
   - Should expand to show grading analogy and GPU memory table

6. **Test multiple expansions**:
   - All three can be expanded simultaneously
   - Clicking summary again collapses the section
   - Sections don't interfere with each other

---

## Benefits

### For New Users
- **Learn by doing**: Explanations right where they need them
- **No context switching**: Don't need to leave GUI to read docs
- **Visual learning**: ASCII diagrams help understand concepts
- **Practical guidance**: Specific values and when to use them

### For Experienced Users
- **Quick reference**: Expand when needed, collapse when not
- **Troubleshooting help**: CUDA out of memory steps right there
- **No clutter**: Collapsed by default, interface stays clean

### For Documentation
- **Single source of truth**: GUI reflects documentation files
- **Always up to date**: Easy to update both docs and GUI together
- **Consistent messaging**: Same analogies used everywhere

---

## Alignment with Original Request

Original user request (message 3):
> "Deployment Stability Threshold Explained & Epochs and batch sizes explained: please add these to the relevant sections of the html"

**Delivered**:
- ✅ Deployment Stability Threshold: Added to Analysis tab, Advanced Features section
- ✅ Epochs: Added to Classifier Training tab, after epochs input
- ✅ Batch sizes: Added to Classifier Training tab, after batch size input

All three explanations are now integrated into the HTML interface as expandable sections that users can click to reveal detailed, user-friendly explanations with analogies, visual diagrams, and practical guidance.

---

## Files Modified

- **templates/index.html**:
  - Lines 591-617: Deployment threshold explanation
  - Lines 719-746: Epochs explanation
  - Lines 758-801: Batch size explanation

---

## Next Steps

The GUI is now complete with all requested features:
1. ✅ File browser functionality (6 locations)
2. ✅ Proper defaults (auto_skip_deployment ON, chapters ON)
3. ✅ Fixed image size ordering
4. ✅ Fixed `process.env.USER` JavaScript bug
5. ✅ Deployment detection integrated into Analysis tab
6. ✅ Parameter explanations in HTML

**Ready for user testing!**
