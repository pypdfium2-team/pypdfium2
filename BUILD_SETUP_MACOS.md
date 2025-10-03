# pypdfium2 Local Development Build Setup for macOS

This guide provides step-by-step instructions for setting up a local development environment to build pypdfium2 from source on macOS.

## Prerequisites

### System Requirements
- macOS 11.0+ (Big Sur or later)
- Xcode Command Line Tools (already installed)
- Homebrew (already installed)
- At least 8GB free disk space
- 16GB+ RAM recommended for compilation

### Quick Check
```bash
# Verify your tools
xcode-select --version  # Should show version 2410+
brew --version          # Should show Homebrew 4.x
```

## Build Options Overview

pypdfium2 offers two build approaches on macOS:

1. **Toolchained Build** (Recommended): Uses Google's build system, more reliable but larger
2. **Native Build**: Uses macOS system tools, more experimental

## Option 1: Toolchained Build (Recommended)

### Step 1: Install Required Dependencies

```bash
# Install Python dependencies
brew install python@3.11

# Install system dependencies for PDFium
brew install ninja git

# Install depot_tools (Google's build tools)
# Create a directory for depot_tools
mkdir -p ~/development
cd ~/development
git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git

# Add to PATH (add to your ~/.zshrc or ~/.bash_profile)
export PATH="$HOME/development/depot_tools:$PATH"
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install pypdfium2 build dependencies
pip install -e .
```

### Step 3: Run Toolchained Build

```bash
# Navigate to pypdfium2 directory
cd /path/to/pypdfium2

# Run the toolchained build script
python setupsrc/pypdfium2_setup/build_toolchained.py

# For custom build options
python setupsrc/pypdfium2_setup/build_toolchained.py --help
```

### Step 4: Install from Source Build

```bash
# Install using the source build
PDFIUM_PLATFORM="sourcebuild" python -m pip install -v .
```

## Option 2: Native Build (Experimental)

The native build is tailored for Linux but can work on macOS with modifications.

### Step 1: Install Native Build Dependencies

```bash
# Install system libraries
brew install freetype lcms2 jpeg-turbo openjpeg libpng zlib libtiff icu4c glib

# Install build tools
brew install ninja gn
```

### Step 2: Set Up Environment Variables

```bash
# Set library paths
export LDFLAGS="-L$(brew --prefix icu4c)/lib"
export CPPFLAGS="-I$(brew --prefix icu4c)/include"

# For freetype
export LDFLAGS="$LDFLAGS -L$(brew --prefix freetype)/lib"
export CPPFLAGS="$CPPFLAGS -I$(brew --prefix freetype)/include"
```

### Step 3: Run Native Build

```bash
# Run native build script
python setupsrc/pypdfium2_setup/build_native.py --compiler clang

# Note: Native build on macOS is experimental and may require patching
```

## Option 3: Development Installation (Easiest)

For most development work, you don't need to build PDFium from source:

```bash
# Install in development mode with prebuilt binaries
pip install -e .

# Or with verbose output to see the setup process
pip install -e . -v
```

## Environment Variables for Custom Builds

### PDFIUM_PLATFORM Options
```bash
# Auto-detect platform and download latest binaries
PDFIUM_PLATFORM="auto" pip install -e .

# Use specific version
PDFIUM_PLATFORM="auto:7269" pip install -e .

# Use V8/XFA enabled binaries
PDFIUM_PLATFORM="auto-v8" pip install -e .

# Build from source
PDFIUM_PLATFORM="sourcebuild" pip install -e .

# Use system PDFium (requires manual setup)
PDFIUM_PLATFORM="system-search" pip install -e .
```

### Module Selection
```bash
# Install only helpers module
PYPDFIUM_MODULES="helpers" pip install -e .

# Install only raw bindings
PYPDFIUM_MODULES="raw" pip install -e .

# Install both modules (default)
PYPDFIUM_MODULES="raw,helpers" pip install -e .
```

## Development Workflow

### Testing Your Build
```bash
# Run tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_page.py

# Run with coverage
just coverage
```

### Common Development Commands
```bash
# Update PDFium binaries to latest version
just update

# Clean build artifacts
just clean

# Build documentation
just docs-build

# Run code quality checks
just check
```

### Troubleshooting Common Issues

#### Issue: Build fails with "ninja not found"
```bash
# Install ninja
brew install ninja

# Or ensure depot_tools is in PATH
export PATH="$HOME/development/depot_tools:$PATH"
```

#### Issue: "xcrun: error: invalid active developer path"
```bash
# Reinstall Xcode command line tools
sudo xcode-select --install
sudo xcode-select --reset
```

#### Issue: "ctypesgen not found"
```bash
# Install ctypesgen (pypdfium2-team fork)
pip install git+https://github.com/pypdfium2-team/ctypesgen@pypdfium2
```

#### Issue: Library linking problems
```bash
# Check library paths
otool -L src/pypdfium2_raw/libpdfium.dylib

# Fix install names if needed
install_name_tool -change @rpath/libpdfium.dylib /path/to/libpdfium.dylib src/pypdfium2_raw/libpdfium.dylib
```

## Advanced Configuration

### Custom Build Parameters
```bash
# For cross-compilation or custom flags
export BUILD_PARAMS="--target-cpu arm64"
python setupsrc/pypdfium2_setup/build_toolchained.py
```

### Debug Build
```bash
# Enable debug symbols
export CFLAGS="-g -O0"
export CXXFLAGS="-g -O0"
python setupsrc/pypdfium2_setup/build_toolchained.py
```

### Clean Rebuild
```bash
# Complete clean rebuild
just clean
rm -rf sbuild/ data/sourcebuild/
python setupsrc/pypdfium2_setup/build_toolchained.py
PDFIUM_PLATFORM="sourcebuild" python -m pip install -v .
```

## Performance Tips

1. **Use SSD storage** for the build directory
2. **Close other applications** during compilation
3. **Use `--jobs` flag** for parallel compilation when available
4. **Clear ccache** if build times increase unexpectedly

## Getting Help

- Check the main README.md for general information
- Look at GitHub Issues for platform-specific problems
- Use `--help` flags on build scripts to see options
- Check build logs in `build.log` for error details

## Verification

To verify your build works correctly:

```bash
# Test basic functionality
python -c "import pypdfium2; print(pypdfium2.__version__)"

# Test PDF processing
python -c "
import pypdfium2
pdf = pypdfium2.PdfDocument.new()
page = pdf.new_page(100, 100)
print('PDF creation works!')
"

# Run full test suite
python -m pytest tests/ -v
```