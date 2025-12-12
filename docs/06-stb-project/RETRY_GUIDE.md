# Final Retry Guide - All Improvements Applied

## What's Fixed

### 1. ✅ No Timeout
Videos run until natural completion - no more premature failures

### 2. ✅ Optimal Workers  
Auto-detection now accounts for multi-core per video:
- **Formula:** (12 cores - 2 overhead) / 2 cores per video = **5 workers**
- Each video gets ~2 cores for PyTorch inference
- System gets 2 cores for overhead
- Result: 5 videos processing simultaneously with optimal resources

### 3. ✅ Integrated Monitor
Real-time progress tracking with `--monitor` flag shows:
- Progress bar per video
- CPU and memory usage
- Elapsed time and ETA
- Auto-refresh every 10 seconds

### 4. ✅ Resume Capability
Automatically skips already-completed videos

## Quick Start

### Option A: With Integrated Monitor (Recommended)
```bash
cd /home/simon/Installers/sharktrack-1.5

# BRUV 1-45 with monitor
python3 parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" \
    "/media/simon/Extreme SSD/analysis_results" \
    --monitor

# BRUV 46-62 with monitor  
python3 parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
    "/media/simon/Extreme SSD/analysis_results" \
    --monitor
```

### Option B: Background with Separate Monitor
```bash
# Start both in background
./resume_both.sh

# Then run monitor separately
python3 monitor_current_videos.py
```

### Option C: All-in-One Script
```bash
./retry_with_monitor.sh
```

## What to Expect

**Current Status:**
- BRUV 1-45: 249/257 complete, **8 videos** need retry
- BRUV 46-62: 90/102 complete, **12 videos** need retry  
- **Total: 20 videos** to process

**With 5 Workers:**
- 5 videos process simultaneously
- Each uses ~2 cores + 4GB RAM
- Remaining 15 videos queue automatically

**Estimated Time:**
- Each video: 10-15 hours (they're 17+ minutes of footage)
- With 5 workers: ~30-45 hours total (processing 4 batches of 5)
- Run overnight recommended

## Monitor Features

The monitor shows live updates like:
```
📹 GH019977.MP4                          (BRUV 48)
   ├─ Progress: [████████░░░░░░░░░░░░░░░░░░░░] 28.5%
   ├─ Elapsed:  3:45:22    | ETA: 09:12:33    | CPU: 205.3% | MEM: 3.8%
   └─ Status:   Processing (142 images)
```

Press Ctrl+C to exit monitor - videos continue in background

## Troubleshooting

### If processes seem stuck
Check actual CPU usage: `top` or `htop`
- Should see 200%+ CPU per app.py process
- If 0% CPU for >30 min, something is wrong

### Check logs
```bash
tail -f bruv_1_45_final.log
tail -f bruv_46_62_final.log
```

### Manual kill if needed
```bash
ps aux | grep app.py | grep -v grep | awk '{print $2}' | xargs kill
```

## After Completion

Check consolidated results:
```bash
cat "/media/simon/Extreme SSD/analysis_results/consolidated/summary_report.txt"
```

Expected final totals:
- Winter: 27 videos, 2 tracks
- BRUV 1-45: 257 videos
- BRUV 46-62: 102 videos
- **Total: 386 videos processed**
