#!/bin/bash
# Build script for Render

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install basic dependencies first
pip install -r requirements.txt

# Try to install TA-Lib with different approaches
echo "Installing TA-Lib..."
pip install TA-Lib-binary==0.4.28 || {
    echo "TA-Lib-binary failed, trying TA-Lib..."
    pip install TA-Lib==0.4.25 || {
        echo "TA-Lib installation failed, trying alternative..."
        pip install https://github.com/TA-Lib/ta-lib-python/archive/TA_Lib-0.4.25.tar.gz
    }
}
