#!/bin/bash

# Mac Studio M2 Optimized Setup Script for Vulnhuntr
# This script sets up vulnhuntr with optimizations for Apple Silicon (ARM64)

set -e

echo "🚀 Setting up Vulnhuntr for Mac Studio M2..."
echo "================================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ This script is designed for macOS. Exiting.${NC}"
    exit 1
fi

# Check if running on Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo -e "${YELLOW}⚠️  Warning: This script is optimized for Apple Silicon (ARM64). Current architecture: $ARCH${NC}"
fi

echo -e "${BLUE}ℹ️  System Information:${NC}"
echo "   Architecture: $ARCH"
echo "   macOS Version: $(sw_vers -productVersion)"
echo "   Hardware: $(system_profiler SPHardwareDataType | grep "Model Name" | cut -d: -f2 | xargs)"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Homebrew and install if needed
if ! command_exists brew; then
    echo -e "${YELLOW}📦 Installing Homebrew...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for Apple Silicon
    if [[ "$ARCH" == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
else
    echo -e "${GREEN}✅ Homebrew is already installed${NC}"
fi

# Update Homebrew
echo -e "${BLUE}📦 Updating Homebrew...${NC}"
brew update

# Install Python 3.10 (required for vulnhuntr)
if ! command_exists python3.10; then
    echo -e "${YELLOW}🐍 Installing Python 3.10...${NC}"
    brew install python@3.10
    
    # Create symlink for python3.10 command
    if [[ "$ARCH" == "arm64" ]]; then
        ln -sf /opt/homebrew/bin/python3.10 /opt/homebrew/bin/python3.10
    else
        ln -sf /usr/local/bin/python3.10 /usr/local/bin/python3.10
    fi
else
    echo -e "${GREEN}✅ Python 3.10 is already installed${NC}"
fi

# Verify Python version
PYTHON_VERSION=$(python3.10 --version 2>&1 | grep -o '3\.10\.[0-9]*' || echo "")
if [[ -z "$PYTHON_VERSION" ]]; then
    echo -e "${RED}❌ Python 3.10 is required but not found. Please install Python 3.10.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python version: $PYTHON_VERSION${NC}"

# Install system dependencies optimized for ARM64
echo -e "${BLUE}📦 Installing system dependencies...${NC}"

# Install ARM64 optimized packages
PACKAGES=(
    "libffi"           # Required for cryptographic libraries
    "openssl"          # SSL/TLS support
    "sqlite"           # Database support
    "zlib"             # Compression library
    "libyaml"          # YAML parsing
    "cmake"            # Build tool for native extensions
    "rust"             # Some Python packages require Rust
    "pkg-config"       # Package configuration
)

for package in "${PACKAGES[@]}"; do
    if brew list "$package" &>/dev/null; then
        echo -e "${GREEN}✅ $package is already installed${NC}"
    else
        echo -e "${YELLOW}📦 Installing $package...${NC}"
        brew install "$package"
    fi
done

# Install pipx for isolated Python package installation
if ! command_exists pipx; then
    echo -e "${YELLOW}📦 Installing pipx...${NC}"
    brew install pipx
    pipx ensurepath
else
    echo -e "${GREEN}✅ pipx is already installed${NC}"
fi

# Set up environment variables for ARM64 optimization
echo -e "${BLUE}⚙️  Setting up environment variables...${NC}"

# Create environment setup file
ENV_FILE="$HOME/.vulnhuntr_env"
cat > "$ENV_FILE" << 'EOF'
# Vulnhuntr Environment Configuration for Mac Studio M2

# Python path configuration
export PYTHON_BIN=$(which python3.10)

# ARM64 optimizations
export ARCHFLAGS="-arch arm64"
export CMAKE_OSX_ARCHITECTURES="arm64"

# Homebrew paths for ARM64
if [[ $(uname -m) == "arm64" ]]; then
    export HOMEBREW_PREFIX="/opt/homebrew"
    export PATH="/opt/homebrew/bin:$PATH"
    export PKG_CONFIG_PATH="/opt/homebrew/lib/pkgconfig:$PKG_CONFIG_PATH"
    export LDFLAGS="-L/opt/homebrew/lib"
    export CPPFLAGS="-I/opt/homebrew/include"
else
    export HOMEBREW_PREFIX="/usr/local"
    export PATH="/usr/local/bin:$PATH"
    export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
    export LDFLAGS="-L/usr/local/lib"
    export CPPFLAGS="-I/usr/local/include"
fi

# SSL/TLS configuration
export SSL_CERT_FILE="$HOMEBREW_PREFIX/etc/openssl@3/cert.pem"
export REQUESTS_CA_BUNDLE="$HOMEBREW_PREFIX/etc/openssl@3/cert.pem"

# Python package compilation optimizations
export CFLAGS="-I$HOMEBREW_PREFIX/include -O2"
export LDFLAGS="$LDFLAGS -L$HOMEBREW_PREFIX/lib"

# Metal Performance Shaders (for AI acceleration if available)
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Disable Python bytecode generation for faster startup
export PYTHONDONTWRITEBYTECODE=1

# Memory optimization for large AI models
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0

EOF

# Source the environment file
source "$ENV_FILE"

# Add to shell profiles
for profile in ~/.zshrc ~/.bash_profile ~/.bashrc; do
    if [[ -f "$profile" ]]; then
        if ! grep -q "source $ENV_FILE" "$profile"; then
            echo "source $ENV_FILE" >> "$profile"
            echo -e "${GREEN}✅ Added environment setup to $profile${NC}"
        fi
    fi
done

# Install vulnhuntr with ARM64 optimizations
echo -e "${BLUE}🔧 Installing vulnhuntr...${NC}"

# Set compilation flags for ARM64
export ARCHFLAGS="-arch arm64"
export CMAKE_OSX_ARCHITECTURES="arm64"

# Use Python 3.10 specifically
if pipx list | grep -q vulnhuntr; then
    echo -e "${YELLOW}🔄 Upgrading existing vulnhuntr installation...${NC}"
    pipx reinstall vulnhuntr --python python3.10
else
    echo -e "${YELLOW}📦 Installing vulnhuntr with pipx...${NC}"
    pipx install git+https://github.com/protectai/vulnhuntr.git --python python3.10
fi

# Install additional dependencies for demo
echo -e "${BLUE}🎭 Installing demo dependencies...${NC}"

DEMO_PACKAGES=(
    "flask"
    "fastapi"
    "uvicorn"
    "gradio"
    "aiohttp"
    "django"
    "psutil"
    "jinja2"
    "markdown"
    "pyyaml"
)

for package in "${DEMO_PACKAGES[@]}"; do
    echo -e "${YELLOW}📦 Installing $package...${NC}"
    python3.10 -m pip install --user "$package"
done

# Create vulnhuntr configuration directory
VULNHUNTR_CONFIG_DIR="$HOME/.config/vulnhuntr"
mkdir -p "$VULNHUNTR_CONFIG_DIR"

# Create performance configuration file
cat > "$VULNHUNTR_CONFIG_DIR/config.json" << 'EOF'
{
    "performance": {
        "max_workers": 8,
        "memory_limit_mb": 4096,
        "use_metal_acceleration": true,
        "optimize_for_arm64": true
    },
    "llm_settings": {
        "default_provider": "claude",
        "timeout_seconds": 120,
        "max_retries": 3,
        "parallel_analysis": true
    },
    "analysis_settings": {
        "max_file_size_mb": 10,
        "max_context_length": 32000,
        "aggressive_optimization": true
    }
}
EOF

# Create demo launcher script
DEMO_SCRIPT="$HOME/.local/bin/vulnhuntr-demo"
mkdir -p "$(dirname "$DEMO_SCRIPT")"

cat > "$DEMO_SCRIPT" << 'EOF'
#!/bin/bash

# Vulnhuntr Demo Launcher for Mac Studio M2

# Load environment
if [[ -f "$HOME/.vulnhuntr_env" ]]; then
    source "$HOME/.vulnhuntr_env"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEMO_DIR="$(dirname "$SCRIPT_DIR")/demo"

echo "🎭 Vulnhuntr Demo Suite"
echo "======================="
echo ""
echo "Available demos:"
echo "1. Flask LFI Demo"
echo "2. FastAPI RCE Demo"
echo "3. Gradio XSS Demo"
echo "4. Run all vulnerability scans"
echo "5. Generate demo report"
echo ""

read -p "Select demo (1-5): " choice

case $choice in
    1)
        echo "🌶️  Starting Flask LFI Demo..."
        cd "$DEMO_DIR/flask_lfi_demo" && python3.10 app.py
        ;;
    2)
        echo "💥 Starting FastAPI RCE Demo..."
        cd "$DEMO_DIR/fastapi_rce_demo" && python3.10 app.py
        ;;
    3)
        echo "🎨 Starting Gradio XSS Demo..."
        cd "$DEMO_DIR/gradio_xss_demo" && python3.10 app.py
        ;;
    4)
        echo "🔍 Running vulnerability scans on all demos..."
        vulnhuntr -r "$DEMO_DIR" -l claude -v
        ;;
    5)
        echo "📊 Generating demo report..."
        python3.10 "$DEMO_DIR/generate_demo_report.py"
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac
EOF

chmod +x "$DEMO_SCRIPT"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
fi

# Performance tuning for Mac Studio M2
echo -e "${BLUE}⚡ Applying Mac Studio M2 performance optimizations...${NC}"

# Set memory and CPU optimizations
cat > "$VULNHUNTR_CONFIG_DIR/performance.sh" << 'EOF'
#!/bin/bash

# Mac Studio M2 Performance Optimizations for Vulnhuntr

# Optimize Python garbage collection
export PYTHONGC=1

# Use all CPU cores efficiently
export OMP_NUM_THREADS=$(sysctl -n hw.ncpu)

# Optimize memory allocation
export MALLOC_ARENA_MAX=4

# Enable Metal Performance Shaders if available
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Optimize for ARM64 NEON instructions
export OPENBLAS_NUM_THREADS=$(sysctl -n hw.ncpu)

echo "🚀 Applied Mac Studio M2 optimizations:"
echo "   CPU cores: $OMP_NUM_THREADS"
echo "   Memory arenas: $MALLOC_ARENA_MAX"
echo "   Metal acceleration: enabled"
EOF

chmod +x "$VULNHUNTR_CONFIG_DIR/performance.sh"

# Create uninstall script
cat > "$VULNHUNTR_CONFIG_DIR/uninstall.sh" << 'EOF'
#!/bin/bash

echo "🗑️  Uninstalling vulnhuntr..."

# Remove pipx installation
pipx uninstall vulnhuntr

# Remove configuration
rm -rf "$HOME/.config/vulnhuntr"

# Remove environment file
rm -f "$HOME/.vulnhuntr_env"

# Remove demo launcher
rm -f "$HOME/.local/bin/vulnhuntr-demo"

echo "✅ Vulnhuntr uninstalled successfully"
EOF

chmod +x "$VULNHUNTR_CONFIG_DIR/uninstall.sh"

# Final setup verification
echo -e "${BLUE}🔍 Verifying installation...${NC}"

# Check vulnhuntr installation
if command_exists vulnhuntr; then
    echo -e "${GREEN}✅ vulnhuntr command is available${NC}"
    VULNHUNTR_VERSION=$(vulnhuntr --help | head -1 || echo "Unable to determine version")
    echo "   Version info: $VULNHUNTR_VERSION"
else
    echo -e "${RED}❌ vulnhuntr command not found${NC}"
fi

# Check Python packages
echo -e "${BLUE}🐍 Checking Python dependencies...${NC}"
python3.10 -c "
import sys
required_packages = ['jedi', 'anthropic', 'openai', 'structlog', 'rich', 'pydantic']
missing = []

for pkg in required_packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg}')
    except ImportError:
        print(f'❌ {pkg}')
        missing.append(pkg)

if missing:
    print(f'Missing packages: {missing}')
    sys.exit(1)
else:
    print('🎉 All required packages are available')
"

# Display completion message
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "1. Restart your terminal or run: source ~/.zshrc"
echo "2. Set your API keys:"
echo "   export ANTHROPIC_API_KEY='your-claude-api-key'"
echo "   export OPENAI_API_KEY='your-openai-api-key'"
echo "3. Run demo: vulnhuntr-demo"
echo "4. Or analyze a project: vulnhuntr -r /path/to/project -l claude"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "   Config dir: $VULNHUNTR_CONFIG_DIR"
echo "   Performance script: $VULNHUNTR_CONFIG_DIR/performance.sh"
echo "   Uninstall script: $VULNHUNTR_CONFIG_DIR/uninstall.sh"
echo ""
echo -e "${GREEN}🚀 Ready to hunt vulnerabilities on Mac Studio M2!${NC}"