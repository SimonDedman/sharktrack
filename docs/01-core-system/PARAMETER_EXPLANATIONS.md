# SharkTrack Parameter Explanations

## Deployment Stability Threshold

### What It Is
A motion detection threshold that determines how "stable" a video period needs to be before it's considered the "deployed" phase (camera on seafloor, ready to record).

### How It Works

The deployment detector:

1. **Samples frames** every 2 seconds throughout the video
2. **Compares consecutive frames** to detect motion:
   - Measures pixel changes
   - Calculates intensity differences
   - Detects edge movement
3. **Calculates motion score** (0-1):
   - 0 = completely still (stable)
   - 1 = high motion (unstable)
4. **Finds stable period**: Longest continuous sequence where motion < threshold

### The Threshold Value (0-1)

**Default: 0.15** (recommended for most cases)

**What the number means**:
- **0.15 = 15% motion tolerance**
- Frames with >15% motion are considered "unstable" (deployment/retrieval)
- Frames with <15% motion are considered "stable" (deployed on seafloor)

### When to Adjust

#### Increase Threshold (0.20-0.25) - More Lenient

**Symptoms**:
- Too many stable underwater frames are being skipped
- Detection says "skipped 0-300s" but you know camera was stable at 100s
- Missing real shark detections in early video

**What happens**:
- Allows more motion before flagging as "deployment"
- Keeps more potentially useful frames
- Risk: May keep some deployment frames

**Example**: Natural current movement causing camera sway might be incorrectly flagged as deployment

#### Decrease Threshold (0.10-0.12) - More Strict

**Symptoms**:
- Still getting surface humans/boat hulls in detections
- Detection says "skipped 0-30s" but you see deployment goes to 120s
- Validation shows false positives from deployment period

**What happens**:
- Flags more frames as "deployment"
- More aggressive filtering
- Risk: May skip some stable frames

**Example**: Slow, smooth deployment might not be detected at 0.15

### Practical Examples

**BRUV 52 (from validation data)**:
```
Deployment: 0-128 seconds
Default threshold (0.15): Detected correctly ✅
Motion during deployment: 0.20-0.35 (high)
Motion after deployed: 0.05-0.12 (low)
Result: Skipped first 128s, eliminated surface human FP
```

**Typical Motion Scores**:
- **Surface deployment**: 0.25-0.50 (boat visible, human arms, chum box)
- **Descending through water**: 0.15-0.30 (moving, bubbles)
- **Landing/settling**: 0.10-0.20 (camera adjusting)
- **Stable on seafloor**: 0.02-0.12 (gentle current sway)
- **Retrieval starting**: 0.15-0.35 (lifting off bottom)

### Visual Analogy

Think of it like a "shakiness detector":

```
|-------|------------|------------|
0     0.10        0.15         0.25         1.0
Still  Gentle    DEFAULT    Moderate    Shaking
      sway     threshold    movement    violently
```

**Threshold at 0.15**:
- Everything LEFT of line = KEEP (stable seafloor footage)
- Everything RIGHT of line = SKIP (deployment/retrieval)

### Technical Details

The motion score combines:
- **60%**: Percentage of pixels that changed
- **30%**: Average intensity change across frame
- **10%**: Maximum intensity change (bright spots moving)

**Smoothing**: Moving average over 5 samples to reduce noise

**Minimum duration**: Stable period must be ≥10 seconds to count

### Recommendation

**Start with default (0.15)** and only adjust if:
1. You see false positives from deployment in validation results → **decrease to 0.12**
2. You see "skipped too many frames" and miss real detections → **increase to 0.20**
3. Run on 2-3 test videos first to check before batch processing

### Command Line Usage

```bash
# Default (recommended)
python3 app.py --input "/path" --auto_skip_deployment

# More strict (eliminate more deployment frames)
python3 app.py --input "/path" --auto_skip_deployment --deployment_stability_threshold 0.12

# More lenient (keep more potentially stable frames)
python3 app.py --input "/path" --auto_skip_deployment --deployment_stability_threshold 0.20
```

---

## Training Epochs

### What It Is
One **epoch** = one complete pass through the entire training dataset.

### Simple Analogy

Imagine teaching a student to identify sharks from photos:

- **1 epoch** = Show them all 100 training photos once
- **25 epochs** = Show them all 100 photos 25 times (in different order each time)

The student (model) learns a bit more each time they see the photos.

### How It Works

**Example with 86 training images, batch size 16**:

```
Epoch 1:
  Batch 1: Show images 1-16   → Calculate error, adjust model
  Batch 2: Show images 17-32  → Calculate error, adjust model
  Batch 3: Show images 33-48  → Calculate error, adjust model
  Batch 4: Show images 49-64  → Calculate error, adjust model
  Batch 5: Show images 65-80  → Calculate error, adjust model
  Batch 6: Show images 81-86  → Calculate error, adjust model

  Result: Model has seen all 86 images once

Epoch 2:
  (Shuffle images into new random order)
  Repeat the same process...
  Result: Model has now seen all images twice

...continue for 25 epochs
```

### Why Multiple Epochs?

**Learning happens gradually**:

- **Epoch 1-5**: Model learns basic features (edges, colors, general shapes)
- **Epoch 6-15**: Model learns species-specific patterns (spots, fin shapes)
- **Epoch 16-25**: Model fine-tunes and improves accuracy on difficult cases

**Learning curve typically looks like**:
```
Accuracy
  100%|                      ___________
      |                  ___/
   75%|             ____/
      |        ____/
   50%|   ____/
      |__/________________________
        0    5    10   15   20   25
                 Epochs
```

### How Many Epochs?

**Default: 25 epochs** (recommended for transfer learning)

#### Too Few Epochs (10-15)

**Symptoms**:
- Model hasn't learned enough
- Low accuracy on validation set
- Can't distinguish between similar species

**When to use**: Quick testing, very large datasets (>10,000 images)

#### Just Right (20-30)

**Sweet spot for most cases**:
- ✅ Small to medium datasets (50-500 images)
- ✅ Transfer learning from pretrained model
- ✅ Good balance of learning vs overfitting risk

#### Too Many Epochs (50+)

**Symptoms**:
- **Overfitting**: Model memorizes training images instead of learning patterns
- High accuracy on training set, LOW accuracy on new images
- Model becomes "too specific" to training examples

**When to use**: Very large datasets with data augmentation

### Time Considerations

**Approximate training time (DenseNet121, 86 images)**:

| Epochs | Time (GPU) | Time (CPU) |
|--------|-----------|-----------|
| 10     | 15 min    | 2 hours   |
| 25     | 35 min    | 5 hours   |
| 50     | 70 min    | 10 hours  |

**Calculation**: ~1.5 minutes per epoch (GPU) or ~12 minutes per epoch (CPU)

### Real Example

**Training Caribbean shark classifier**:

```
Starting: 86 images (G.cirratum, C.perezi, C.acronotus, non_elasmobranch)

Epoch 1:  Train Acc: 45%  Val Acc: 40%  (Learning basic shapes)
Epoch 5:  Train Acc: 68%  Val Acc: 62%  (Learning species features)
Epoch 10: Train Acc: 82%  Val Acc: 76%  (Getting good)
Epoch 15: Train Acc: 91%  Val Acc: 84%  (Refining)
Epoch 20: Train Acc: 95%  Val Acc: 88%  (Nearly optimal)
Epoch 25: Train Acc: 97%  Val Acc: 89%  (Done!) ✅

Best model saved at Epoch 25 with 89% validation accuracy
```

### Recommendation

**Start with 25 epochs** (default) unless:
- Small dataset (<50 images) → Try 30-35 epochs
- Large dataset (>500 images) → Try 20 epochs
- Very large dataset (>5000 images) → Try 15 epochs
- Testing quickly → Try 10 epochs (but expect lower accuracy)

---

## Batch Size

### What It Is
Number of images processed **together** in one forward/backward pass through the model.

### Simple Analogy

Imagine grading student homework:

- **Batch Size 1**: Grade one paper, update gradebook, get next paper
- **Batch Size 16**: Grade 16 papers, average the scores, update gradebook once
- **Batch Size 32**: Grade 32 papers, average the scores, update gradebook once

Larger batches = fewer gradebook updates = faster, but need more desk space (memory).

### How It Works

**Example: 86 images, different batch sizes**

#### Batch Size 8 (Small)
```
Epoch has: 86 images ÷ 8 per batch = 11 batches

Batch 1:  Load 8 images → Process → Update model
Batch 2:  Load 8 images → Process → Update model
...
Batch 11: Load 6 images → Process → Update model

Total: 11 model updates per epoch
Memory: 8 images in GPU at once
```

#### Batch Size 16 (Default)
```
Epoch has: 86 images ÷ 16 per batch = 6 batches

Batch 1: Load 16 images → Process → Update model
...
Batch 6: Load 6 images → Process → Update model

Total: 6 model updates per epoch
Memory: 16 images in GPU at once
```

#### Batch Size 32 (Large)
```
Epoch has: 86 images ÷ 32 per batch = 3 batches

Batch 1: Load 32 images → Process → Update model
Batch 2: Load 32 images → Process → Update model
Batch 3: Load 22 images → Process → Update model

Total: 3 model updates per epoch
Memory: 32 images in GPU at once
```

### Why It Matters

#### 1. Memory Usage

**GPU VRAM required** (approximate for DenseNet121):

| Batch Size | VRAM Needed | Works On |
|-----------|-------------|----------|
| 4         | ~2 GB       | Old GPUs, CPU |
| 8         | ~3 GB       | GTX 1060, laptop |
| 16        | ~5 GB       | GTX 1080, RTX 2060 |
| 32        | ~10 GB      | RTX 3090, A100 |

**If you get "CUDA out of memory" error** → Reduce batch size!

#### 2. Training Speed

**Time per epoch** (86 images, GPU):

| Batch Size | Time | Speed |
|-----------|------|-------|
| 4         | 2.5 min | Slowest |
| 8         | 1.8 min | Slow |
| 16        | 1.4 min | ✅ Good |
| 32        | 1.2 min | Fast |

Larger batches = fewer model updates = faster training

#### 3. Learning Quality

**Small batches (4-8)**:
- ✅ More frequent model updates → Better learning
- ✅ Less memory needed
- ❌ Slower training
- ❌ Noisier gradients (more variation)

**Medium batches (16-32)**:
- ✅ Good balance of speed and learning
- ✅ Stable training
- ❌ Need more GPU memory

**Large batches (64+)**:
- ✅ Very fast training
- ❌ Can get stuck in local minima
- ❌ Need lots of GPU memory
- ❌ May generalize worse

### Choosing Batch Size

#### Start with 16 (Recommended)

Works well for:
- ✅ Most modern GPUs (GTX 1080+, RTX series)
- ✅ Transfer learning from pretrained models
- ✅ Datasets of any size
- ✅ Good speed/memory tradeoff

#### Reduce to 8 if:

- GPU has <6GB VRAM (GTX 1060, laptop GPUs)
- You get "CUDA out of memory" error
- Running on CPU only (but training will be SLOW)

#### Reduce to 4 if:

- GPU has <4GB VRAM
- Still getting out of memory with batch size 8
- Training on CPU and want to save RAM

#### Increase to 32 if:

- GPU has >10GB VRAM (RTX 3080+, A100)
- Large dataset (>500 images)
- Want faster training
- Accuracy is already good at batch size 16

### Real Example

**Training on GTX 1080 Ti (11GB VRAM)**:

```bash
# Try default first
python3 train_species_classifier.py \
  --training_images /path/to/images \
  --class_mapping "G.cirratum,C.perezi,C.acronotus" \
  --output_model models/test \
  --batch_size 16

# If you get "CUDA out of memory":
ERROR: RuntimeError: CUDA out of memory. Tried to allocate 1.5GB

# Reduce to 8 and try again
python3 train_species_classifier.py \
  ... same args ... \
  --batch_size 8

# Still out of memory? Reduce to 4
  --batch_size 4
```

### Memory Calculation

**Rule of thumb**: Batch size 16 needs ~5GB GPU VRAM for DenseNet121

**Formula** (approximate):
```
VRAM needed = (model size) + (batch_size × image_size × 4 bytes)

DenseNet121:
  Model: ~8MB
  Images: 16 × (200×400×3 channels) × 4 bytes = ~15MB per image
  Total: 8MB + (16 × 15MB) = ~250MB for model + data

  But training needs:
  - Forward pass activations: ~2GB
  - Backward pass gradients: ~2GB
  - Optimizer states: ~1GB

  Total: ~5GB for batch size 16
```

### Recommendations

| Your GPU | Recommended Batch Size | Training Time (25 epochs) |
|----------|----------------------|--------------------------|
| CPU only | 4 | ~5 hours |
| Laptop GPU (<4GB) | 4 | ~2 hours |
| GTX 1060 (6GB) | 8 | ~50 min |
| GTX 1080 (8GB) | 16 | ✅ **35 min** |
| RTX 3070 (8GB) | 16-24 | ~30 min |
| RTX 3090 (24GB) | 32 | ~25 min |

---

## Quick Reference

### When to Adjust Parameters

| Problem | Solution |
|---------|----------|
| Too many deployment frames kept | **Decrease** deployment threshold to 0.12 |
| Too many stable frames skipped | **Increase** deployment threshold to 0.20 |
| Model accuracy too low | **Increase** epochs to 30-35 |
| Training too slow | **Decrease** epochs to 15-20 (test only) |
| CUDA out of memory | **Decrease** batch size: 16→8→4 |
| Training takes forever | **Increase** batch size (if you have VRAM) |
| Model overfitting training data | **Decrease** epochs to 20 |

### Default Settings (Recommended Starting Point)

```bash
python3 app.py \
  --input "/path/to/videos" \
  --auto_skip_deployment \
  --deployment_stability_threshold 0.15 \
  --conf 0.25

python3 train_species_classifier.py \
  --training_images "/path/to/images" \
  --class_mapping "species1,species2,species3" \
  --output_model "models/my_classifier" \
  --epochs 25 \
  --batch_size 16
```

These defaults work for 90% of use cases. Only adjust if you encounter specific issues!
