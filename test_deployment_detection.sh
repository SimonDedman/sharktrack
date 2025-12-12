#!/bin/bash
#
# Test deployment detection integration
#

echo "=========================================="
echo "Testing Deployment Detection Integration"
echo "=========================================="
echo ""

# Test video with known false positives at start
TEST_VIDEO="/media/simon/Extreme SSD/BRUV_Summer_2022_46_62/BRUV 52/GH012492.MP4"
TEST_OUTPUT="/tmp/sharktrack_deployment_test"

# Clean previous test
rm -rf "$TEST_OUTPUT"
mkdir -p "$TEST_OUTPUT"

echo "Test video: $TEST_VIDEO"
echo "Output: $TEST_OUTPUT"
echo ""

# Run with deployment detection enabled
echo "Running SharkTrack with --auto_skip_deployment..."
echo ""

python3 app.py \
  --input "$TEST_VIDEO" \
  --output "$TEST_OUTPUT" \
  --auto_skip_deployment \
  --limit 1

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
echo ""
echo "Check output at: $TEST_OUTPUT"
echo ""

# Show results
if [ -f "$TEST_OUTPUT/output.csv" ]; then
  echo "Detections found:"
  wc -l "$TEST_OUTPUT/output.csv"
  echo ""
  echo "First few detections:"
  head -5 "$TEST_OUTPUT/output.csv"
else
  echo "No output.csv found - check for errors"
fi
