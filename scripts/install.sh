#!/bin/bash
# Scrap AI Bot - Installation Script
# This script sets up the complete environment for running Scrap AI Bot

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo "================================================"
echo "   Scrap AI Bot - Installation"
echo "================================================"
echo ""

# Check if running on supported OS
log_info "Checking operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_success "Linux detected"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    log_warning "macOS detected - some features may require additional setup"
else
    log_error "Unsupported operating system: $OSTYPE"
    log_error "This script is designed for Linux (Ubuntu/Debian)"
    exit 1
fi

# Check for required commands
log_info "Checking for required system dependencies..."

check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 is not installed"
        return 1
    else
        log_success "$1 is installed"
        return 0
    fi
}

MISSING_DEPS=0

check_command "docker" || MISSING_DEPS=1
check_command "docker-compose" || check_command "docker compose" || MISSING_DEPS=1
check_command "git" || MISSING_DEPS=1
check_command "python3" || MISSING_DEPS=1

if [ $MISSING_DEPS -eq 1 ]; then
    log_error "Missing required dependencies"
    echo ""
    echo "Please install the missing dependencies:"
    echo "  - Docker: https://docs.docker.com/get-docker/"
    echo "  - Docker Compose: https://docs.docker.com/compose/install/"
    echo "  - Git: sudo apt-get install git"
    echo "  - Python 3: sudo apt-get install python3 python3-pip"
    exit 1
fi

# Check Python version
log_info "Checking Python version..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    log_error "Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
else
    log_success "Python $PYTHON_VERSION is compatible"
fi

# Check for audio system
log_info "Checking audio system..."
if command -v pactl &> /dev/null; then
    log_success "PulseAudio detected"
elif command -v aplay &> /dev/null; then
    log_success "ALSA detected"
else
    log_warning "No audio system detected - voice input may not work"
    log_warning "Install PulseAudio: sudo apt-get install pulseaudio"
fi

# Initialize git submodules
log_info "Initializing git submodules (Anthropic Computer Use Demo)..."
if [ -d ".git" ]; then
    git submodule update --init --recursive
    log_success "Submodules initialized"
else
    log_warning "Not a git repository - skipping submodule initialization"
    log_warning "You may need to manually clone computer-use-demo"
fi

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p logs
mkdir -p temp/audio
mkdir -p cache
mkdir -p config
log_success "Directories created"

# Check for .env file
log_info "Checking for .env file..."
if [ ! -f ".env" ]; then
    log_warning ".env file not found"
    if [ -f ".env.example" ]; then
        log_info "Copying .env.example to .env..."
        cp .env.example .env
        log_warning "Please edit .env and add your API keys:"
        log_warning "  - ANTHROPIC_API_KEY (get from https://console.anthropic.com/)"
        log_warning "  - OPENAI_API_KEY (get from https://platform.openai.com/)"
        log_warning "  - PICOVOICE_ACCESS_KEY (get from https://console.picovoice.ai/)"
    else
        log_error ".env.example not found - cannot create .env"
        exit 1
    fi
else
    log_success ".env file exists"
    
    # Check if API keys are set
    log_info "Checking API keys in .env..."
    source .env
    
    if [[ -z "$ANTHROPIC_API_KEY" || "$ANTHROPIC_API_KEY" == *"your-key-here"* ]]; then
        log_warning "ANTHROPIC_API_KEY not set in .env"
    else
        log_success "ANTHROPIC_API_KEY is set"
    fi
    
    if [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == *"your-key-here"* ]]; then
        log_warning "OPENAI_API_KEY not set in .env"
    else
        log_success "OPENAI_API_KEY is set"
    fi
    
    if [[ -z "$PICOVOICE_ACCESS_KEY" || "$PICOVOICE_ACCESS_KEY" == *"your-key-here"* ]]; then
        log_warning "PICOVOICE_ACCESS_KEY not set in .env"
    else
        log_success "PICOVOICE_ACCESS_KEY is set"
    fi
fi

# Install Python dependencies (for development)
log_info "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    log_success "Virtual environment created"
else
    log_success "Virtual environment already exists"
fi

log_info "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
log_success "Dependencies installed"

# Install development dependencies
read -p "Install development dependencies? (for testing/contributing) [y/N]: " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "Installing development dependencies..."
    pip install -r requirements-dev.txt
    log_success "Development dependencies installed"
    
    # Setup pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        log_info "Setting up pre-commit hooks..."
        pre-commit install
        log_success "Pre-commit hooks installed"
    fi
fi

# Build Docker image
log_info "Building Docker image..."
log_warning "This may take several minutes..."

if docker build -f docker/Dockerfile.voice -t scrap-ai-bot:latest .; then
    log_success "Docker image built successfully"
else
    log_error "Failed to build Docker image"
    exit 1
fi

# Test Docker setup
log_info "Testing Docker configuration..."
if docker-compose --version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    log_error "Docker Compose not found"
    exit 1
fi

log_success "Docker Compose available: $DOCKER_COMPOSE_CMD"

# Create docker-compose override for local development (optional)
if [ ! -f "docker-compose.override.yml" ]; then
    read -p "Create docker-compose.override.yml for local development? [y/N]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cat > docker-compose.override.yml <<EOF
# Local development overrides
# This file is not committed to git

version: '3.8'

services:
  scrap-ai-bot:
    volumes:
      - ./voice-layer:/home/computeruse/voice-layer:ro
      - ./logs:/home/computeruse/logs
    environment:
      - LOG_LEVEL=DEBUG
EOF
        log_success "docker-compose.override.yml created"
    fi
fi

# Test microphone access
log_info "Testing microphone access..."
if [ -d "/dev/snd" ]; then
    log_success "Audio devices found in /dev/snd"
else
    log_warning "No audio devices found - voice input may not work in Docker"
    log_warning "You may need to configure audio passthrough"
fi

# Summary
echo ""
echo "================================================"
log_success "Installation completed!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys if you haven't already"
echo "2. Run './scripts/start.sh' to start Scrap AI Bot"
echo "3. Access the interface at http://localhost:6080"
echo "4. Say 'Ok Computer' followed by your command"
echo ""
echo "Useful commands:"
echo "  ./scripts/start.sh   - Start the bot"
echo "  ./scripts/stop.sh    - Stop the bot"
echo "  docker logs -f scrap-ai-bot   - View logs"
echo ""
echo "Documentation:"
echo "  README.md           - User guide"
echo "  ARCHITECTURE.md     - Technical details"
echo "  CONTRIBUTING.md     - How to contribute"
echo ""
echo "Need help? Visit: https://github.com/andresmascl/scrap-ai-bot/issues"
echo ""

# Final checks
if [[ -z "$ANTHROPIC_API_KEY" || "$ANTHROPIC_API_KEY" == *"your-key-here"* ]] || \
   [[ -z "$OPENAI_API_KEY" || "$OPENAI_API_KEY" == *"your-key-here"* ]] || \
   [[ -z "$PICOVOICE_ACCESS_KEY" || "$PICOVOICE_ACCESS_KEY" == *"your-key-here"* ]]; then
    echo ""
    log_warning "IMPORTANT: API keys are not configured!"
    log_warning "Edit .env and add your API keys before starting the bot"
    echo ""
fi

deactivate 2>/dev/null || true
