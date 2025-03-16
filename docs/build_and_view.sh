#!/bin/bash
# Build and open the documentation in one step

# Change to the docs directory
cd "$(dirname "$0")"

# Build the documentation
make html

# Open the documentation in the default browser
open build/html/index.html
