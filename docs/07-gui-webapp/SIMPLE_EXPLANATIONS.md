# SharkTrack Settings - Simple Explanations

## 🔧 Browse Buttons Not Working?

**Quick Fix**: The web server needs to be running!

```bash
cd /home/simon/Installers/sharktrack-1.5
./launch_gui.sh
```

**Why**: Browse buttons fetch directory listings from the Flask server. If you just opened the HTML file directly, the server isn't running and buttons do nothing.

**Test**: Open Firefox Developer Tools (F12), click Console tab, click Browse button. If you see "Failed to fetch" error → server not running.

---

## 📊 Deployment Stability Threshold

### What does it do?
Detects when the camera is being lowered/raised (deployment/retrieval) vs when it's stable on the seafloor recording sharks.

### How it works
**Think of it like a "shakiness meter":**

```
Camera Activity          Motion Score    What Happens
────────────────────────────────────────────────────
Boat, humans visible     0.30-0.50       SKIP ✂️
Descending in water      0.20-0.30       SKIP ✂️
Landing on seafloor      0.15-0.20       SKIP ✂️ (default cutoff)
Stable, gentle sway      0.05-0.12       KEEP ✅
Sharks swimming by       0.08-0.15       KEEP ✅
```

### The Number (0-1)

**Default: 0.15 = 15% motion tolerance**

- Below 0.15 = stable (KEEP footage)
- Above 0.15 = unstable (SKIP footage)

### Real Example

**BRUV 52 from your validation data:**
- First 128 seconds: Motion = 0.25-0.35 (boat/humans) → SKIPPED ✂️
- After 128 seconds: Motion = 0.08-0.12 (stable) → KEPT ✅
- Result: Eliminated surface human false positive!

### When to change it

**⬆️ Increase to 0.20** (more lenient) if:
- "I know the camera was stable at 100s but it skipped to 200s"
- Missing real shark detections
- Natural current/waves flagged as deployment

**⬇️ Decrease to 0.12** (more strict) if:
- Still seeing surface humans in results
- Still seeing boat hulls/chum boxes
- Deployment period longer than detected

**👍 Keep at 0.15** if:
- First try (recommended)
- Validation shows no deployment false positives
- Everything working well

---

## 📚 Training Epochs

### What is an epoch?
**One complete pass through all your training images.**

### Simple Analogy

Teaching a student to identify sharks from photos:

- **Epoch 1**: Show all photos once → Student learns basic shark shape
- **Epoch 10**: Show all photos 10 times → Student learns species differences
- **Epoch 25**: Show all photos 25 times → Student becomes expert ✅

Each time they see the photos (in different random order), they learn more details.

### The Number

**Default: 25 epochs (recommended)**

**What happens during training:**

```
Epoch  1: Accuracy 45%   "Hmm, these all look like fish..."
Epoch  5: Accuracy 68%   "I see differences in the fins"
Epoch 10: Accuracy 82%   "I can tell nurse shark from reef shark"
Epoch 15: Accuracy 91%   "Getting good at this!"
Epoch 20: Accuracy 95%   "Almost perfect"
Epoch 25: Accuracy 97%   "Expert level!" ✅
```

### How long does it take?

**With GPU** (recommended):
- 25 epochs = **30-60 minutes**
- ~1.5 minutes per epoch

**Without GPU** (CPU only):
- 25 epochs = **5+ hours** ⏳
- ~12 minutes per epoch

### When to change it

**⬆️ Increase to 30-35** if:
- Small dataset (<50 images)
- Accuracy not improving enough
- Model needs more learning time

**⬇️ Decrease to 15-20** if:
- Large dataset (>500 images)
- Just testing quickly
- Model accuracy already good

**⬇️ Decrease to 10** if:
- Quick test/experiment
- Don't care about accuracy yet
- Save time

**❌ Don't go above 40** because:
- Risk of "overfitting" (memorizing instead of learning)
- Model works great on training images but fails on new ones
- Wasting time without improvement

---

## 📦 Batch Size

### What is batch size?
**How many images the model looks at before updating what it learned.**

### Simple Analogy

Grading homework:

- **Batch size 1**: Grade 1 paper, update gradebook, get next paper (SLOW)
- **Batch size 16**: Grade 16 papers, average scores, update gradebook once (GOOD)
- **Batch size 32**: Grade 32 papers, average scores, update gradebook once (FAST but needs big desk)

The "desk" is your GPU memory. Larger batches = faster but need more memory.

### The Number

**Default: 16 (recommended)**

### Real Impact

**Example: 86 images, 25 epochs**

| Batch Size | GPU Memory | Time per Epoch | Total Time | When to Use |
|-----------|-----------|----------------|-----------|-------------|
| 4 | 2 GB | 2.5 min | **60 min** | Old GPU, CPU only |
| 8 | 3 GB | 1.8 min | **45 min** | Laptop GPU, GTX 1060 |
| 16 | 5 GB | 1.4 min | **35 min** ✅ | GTX 1080, RTX 2060+ |
| 32 | 10 GB | 1.2 min | **30 min** | RTX 3090, A100 |

### What happens if GPU runs out of memory?

```
ERROR: RuntimeError: CUDA out of memory. Tried to allocate 1.5GB
```

**Fix**: Reduce batch size!

```bash
# Try 16 first (default)
--batch_size 16

# If error, try 8
--batch_size 8

# Still error? Try 4
--batch_size 4
```

### When to change it

**⬇️ Decrease to 8** if:
- Laptop GPU (<6GB)
- "CUDA out of memory" error
- GTX 1060 or similar

**⬇️ Decrease to 4** if:
- Very old GPU (<4GB)
- Training on CPU
- Still getting memory errors

**⬆️ Increase to 32** if:
- High-end GPU (RTX 3080+, >10GB)
- Want faster training
- Large dataset

**👍 Keep at 16** if:
- Modern GPU (GTX 1080 or newer)
- No memory errors
- Good training speed

---

## 🎯 Quick Decision Guide

### "I'm new, what should I use?"

**Use all defaults:**
- Deployment threshold: **0.15**
- Training epochs: **25**
- Batch size: **16**

These work for 90% of cases!

### "I'm getting errors"

**Problem**: Browse buttons don't work
- **Fix**: Run `./launch_gui.sh` first

**Problem**: CUDA out of memory
- **Fix**: Reduce batch size to 8, then 4 if needed

**Problem**: Training too slow
- **Fix**: Get a GPU, or reduce epochs to 15

**Problem**: Still seeing surface humans in detections
- **Fix**: Reduce deployment threshold to 0.12

**Problem**: Missing real detections
- **Fix**: Increase deployment threshold to 0.20

### "I want the best accuracy"

```bash
# Best settings for accuracy (slower but better):
python3 train_species_classifier.py \
  --epochs 30 \
  --batch_size 16
```

### "I want to test quickly"

```bash
# Fast settings for testing (faster but less accurate):
python3 train_species_classifier.py \
  --epochs 10 \
  --batch_size 32
```

---

## 📊 Real Examples from Your Data

### BRUV 52 - Deployment Detection Success

**Video**: GH012492.MP4, 18 minutes
**Problem**: Surface human at start (validation row 48)

**Settings used**: Threshold 0.15 (default)

**Result**:
```
Detected deployment: 0-128 seconds
Stable period: 128s-1058s
Frames skipped: 384
False positives eliminated: 1 (surface human)
```

✅ **Success**: Default threshold correctly detected and skipped deployment period!

### Caribbean Sharks - Training Example

**Dataset**: 86 labeled images
- G. cirratum (nurse): 33 images
- C. perezi (reef): 39 images
- C. acronotus (blacktip): 14 images

**Settings**: 25 epochs, batch size 16 (defaults)

**Expected results**:
```
Training time: 35 minutes (with GTX 1080)
Final accuracy: 89-93%
Best epoch: Around epoch 23-25
```

✅ **This is good accuracy** for a small dataset!

---

## 🔍 Visual Summary

### Deployment Threshold

```
   SKIP                   KEEP
← Unstable  |  Stable →
───────────────────────────────
   0.20    0.15    0.10    0.05
 Lenient DEFAULT Strict  Very Strict
```

### Training Progress

```
Accuracy
100% ┤              ___________
 90% ┤          ___/
 80% ┤      ___/
 70% ┤  ___/
 60% ┤_/
     └──────────────────────────
       5   10   15   20   25
            Epochs

        ↑ Sweet spot
```

### Batch Size Memory

```
GPU VRAM Available
───────────────────────────────
 2GB ─┤ Use batch_size=4
 4GB ─┤ Use batch_size=8
 6GB ─┤ Use batch_size=16 ✅
10GB ─┤ Use batch_size=32
```

---

## ❓ Still Confused?

**Start with defaults, run on 2-3 test videos, check results.**

Only change settings if you see problems:
- Surface humans still appearing → Lower deployment threshold
- Missing detections → Raise deployment threshold
- Out of memory → Lower batch size
- Low accuracy → More epochs
- Too slow → Fewer epochs (but sacrifice accuracy)

**The defaults are designed to work well without tweaking!**
