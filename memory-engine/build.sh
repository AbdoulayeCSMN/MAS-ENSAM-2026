#!/usr/bin/env bash
# Build the memory-engine binary in release mode
set -e

echo "🦀 Building memory-engine..."
cargo build --release

echo ""
echo "✅ Binary ready at:"
echo "   $(pwd)/target/release/memory-engine"
echo ""
echo "Usage:"
echo "   ./target/release/memory-engine --json /path/to/repo"
echo "   ./target/release/memory-engine --json --verbose /path/to/repo"
echo "   ./target/release/memory-engine --json --min-severity high /path/to/repo"
