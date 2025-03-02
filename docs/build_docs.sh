#!/bin/bash
# Simple script to build the documentation

# Clean previous build
rm -rf build

# Build the HTML documentation
sphinx-build -b html source build/html

# Open the documentation in the default browser (macOS)
open build/html/index.html

echo "Documentation built successfully!"
