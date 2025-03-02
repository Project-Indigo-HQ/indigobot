#!/bin/bash
# Simple script to build the documentation

# Clean previous build
rm -rf build

# Build the HTML documentation
sphinx-build -b html source build/html

# Open the documentation in the default browser (macOS)
open build/html/index.html

echo "Documentation built successfully!"
#!/bin/bash
# Simple script to build the documentation

# Get the absolute path to the docs directory
DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DOCS_DIR"

echo "Building documentation from $DOCS_DIR"

# Clean previous build
rm -rf build

# Make sure _static directory exists
mkdir -p source/_static

# Build the HTML documentation
sphinx-build -b html source build/html

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Documentation built successfully at $DOCS_DIR/build/html/index.html"
    # Open the documentation in the default browser (macOS)
    open build/html/index.html
else
    echo "Documentation build failed"
fi
