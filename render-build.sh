#!/bin/bash

# Render Build Script for Zyana Backend
# Installs system dependencies and Python packages

echo "🔧 Installing system dependencies..."

# Update package lists
apt-get update

# Install ffmpeg (required for faster-whisper audio processing)
apt-get install -y ffmpeg

echo "✅ System dependencies installed"

echo "📦 Installing Python dependencies..."

# Install Python packages
pip install -r backend/requirements.txt

echo "✅ Python dependencies installed"

echo "🚀 Build complete!"

