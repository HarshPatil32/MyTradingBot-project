#!/bin/bash
# Build script for Render

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install all requirements except TA-Lib first
pip install -r requirements.txt

# Try to install TA-Lib using multiple approaches
echo "Installing TA-Lib..."

# Method 1: Try TA-Lib-binary (pre-compiled wheel)
if pip install TA-Lib-binary==0.4.28; then
    echo "✅ TA-Lib-binary installed successfully"
elif pip install TA-Lib-binary; then
    echo "✅ TA-Lib-binary (latest) installed successfully"
# Method 2: Try from conda-forge wheel repository  
elif pip install --index-url https://pypi.anaconda.org/conda-forge/simple/ TA-Lib; then
    echo "✅ TA-Lib from conda-forge installed successfully"
# Method 3: Try from alternative wheel source
elif pip install https://github.com/TA-Lib/ta-lib-python/archive/refs/heads/master.zip; then
    echo "✅ TA-Lib from GitHub installed successfully"
# Method 4: Last resort - standard TA-Lib (might fail without C libraries)
elif pip install TA-Lib; then
    echo "✅ TA-Lib standard package installed successfully"
else
    echo "❌ All TA-Lib installation methods failed"
    echo "ℹ️  The app will need to use pandas-based indicators instead"
fi

echo "Build completed!"
