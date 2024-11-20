#!/bin/bash
set -x  # Enable debug output

# Check if we have the right number of arguments
if [ "$#" -ne 2 ]; then
    echo "Error: Need exactly 2 arguments (project_dir and output_file)" >&2
    exit 1
fi

PROJECT_DIR="$1"
OUTPUT_FILE="$2"

echo "Starting test run at $(date)" > "$OUTPUT_FILE"
echo "Project directory: $PROJECT_DIR" >> "$OUTPUT_FILE"
echo "Output file: $OUTPUT_FILE" >> "$OUTPUT_FILE"
echo "-------------------" >> "$OUTPUT_FILE"

# Change to project directory and run npm test
cd "$PROJECT_DIR" && npm run test >> "$OUTPUT_FILE" 2>&1
TEST_EXIT=$?

echo "-------------------" >> "$OUTPUT_FILE"
echo "Test completed at $(date) with exit code $TEST_EXIT" >> "$OUTPUT_FILE"

# Write exit code to separate file
echo "$TEST_EXIT" > "${OUTPUT_FILE}.exit"
