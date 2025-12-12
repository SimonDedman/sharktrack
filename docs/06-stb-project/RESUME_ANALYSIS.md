# Resume Analysis Guide

The pipeline now has **intelligent resume capability** - it automatically skips videos that already have results.

## How It Works

When you run the analysis command, the script:
1. Scans all video files in the input directory
2. Checks if each video has an `overview.csv` result file
3. Skips videos that are already processed
4. Only processes remaining videos

This means you can **safely re-run the same command** and it will automatically resume from where it left off.

## Resume Commands

Simply re-run the original analysis commands:

### BRUV 1-45 (Resume)
```bash
cd /home/simon/Installers/sharktrack-1.5

nohup sharktrack-env/bin/python3 -u parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" \
    "/media/simon/Extreme SSD/analysis_results" \
    > bruv_1_45_resume.log 2>&1 &

echo "BRUV 1-45 resume started. Monitor with: tail -f bruv_1_45_resume.log"
```

### BRUV 46-62 (Resume)
```bash
cd /home/simon/Installers/sharktrack-1.5

nohup sharktrack-env/bin/python3 -u parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
    "/media/simon/Extreme SSD/analysis_results" \
    > bruv_46_62_resume.log 2>&1 &

echo "BRUV 46-62 resume started. Monitor with: tail -f bruv_46_62_resume.log"
```

### Run Both in Parallel
```bash
cd /home/simon/Installers/sharktrack-1.5

# Start BRUV 1-45
nohup sharktrack-env/bin/python3 -u parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" \
    "/media/simon/Extreme SSD/analysis_results" \
    > bruv_1_45_resume.log 2>&1 &
PID_1_45=$!

# Start BRUV 46-62
nohup sharktrack-env/bin/python3 -u parallel_sharktrack_analysis.py \
    "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" \
    "/media/simon/Extreme SSD/analysis_results" \
    > bruv_46_62_resume.log 2>&1 &
PID_46_62=$!

echo "✅ Both analyses started in parallel"
echo "   BRUV 1-45: PID $PID_1_45 (log: bruv_1_45_resume.log)"
echo "   BRUV 46-62: PID $PID_46_62 (log: bruv_46_62_resume.log)"
echo ""
echo "Monitor progress:"
echo "   tail -f bruv_1_45_resume.log"
echo "   tail -f bruv_46_62_resume.log"
```

## What You'll See

When resuming, the output will show:
```
⏭️  Skipping 249 already-processed videos (resume mode)
📹 Found 8 video files for analysis (257 total)
```

This tells you:
- 249 videos already have results
- Only 8 videos need processing
- 257 total videos in the collection

## Key Features

### ✅ Intelligent Timeout
Each video now gets a custom timeout based on its duration:
- Short videos (2 min): ~23 min timeout
- Medium videos (10 min): ~113 min timeout
- Long videos (17 min): ~198 min timeout

The formula: `(duration_seconds * 3fps * 2.5s/frame * 1.5 safety margin)`

### ✅ Safe to Interrupt
You can safely stop the analysis at any time (Ctrl+C or system reboot). When you re-run, it will pick up where it left off.

### ✅ No Duplicate Processing
Already-processed videos are completely skipped - no wasted computation.

## Monitoring Progress

### Real-time log monitoring
```bash
tail -f bruv_1_45_resume.log
tail -f bruv_46_62_resume.log
```

### Check running processes
```bash
ps aux | grep parallel_sharktrack_analysis
```

### Count remaining videos
```bash
# BRUV 1-45
find "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" -name "*.MP4" | wc -l
find "/media/simon/Extreme SSD/BRUV_Summer_2022_1_45" -path "*/analysis_results/*/internal_results/overview.csv" | wc -l

# BRUV 46-62
find "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" -name "*.MP4" | wc -l
find "/media/simon/Extreme SSD/BRUV_Summer_2022_46_62" -path "*/analysis_results/*/internal_results/overview.csv" | wc -l
```

## Expected Results

### BRUV 1-45
- Total videos: 257
- Already processed: ~249
- **Need to process: ~8 videos**
- Estimated time: 2-3 hours (long videos)

### BRUV 46-62
- Total videos: 102
- Already processed: ~90
- **Need to process: ~12 videos**
- Estimated time: 3-4 hours (very long videos)

### Total
- **~20 videos to process**
- **5-7 hours total** (if run in parallel: ~3-4 hours)

## Troubleshooting

### If video times out again
The new intelligent timeout should handle most videos, but if a video exceeds even the calculated timeout:
1. Note which video failed
2. Process it separately with peek mode (faster, keyframe-only):
   ```bash
   sharktrack-env/bin/python3 parallel_sharktrack_analysis.py \
       "/path/to/specific/BRUV/folder" \
       "/media/simon/Extreme SSD/analysis_results" \
       --peek
   ```

### If process hangs
1. Check if app.py processes are still running: `ps aux | grep app.py`
2. Check system resources: `top` or `htop`
3. If truly hung, kill and restart - resume will skip completed videos

## After Completion

Once both analyses complete, consolidate all results:
```bash
cat "/media/simon/Extreme SSD/analysis_results/consolidated/summary_report.txt"
```

This will show:
- Total videos processed across all collections
- Total tracks/detections found
- Processing statistics

---

**Quick Start:** Just copy and paste the "Run Both in Parallel" command above!
