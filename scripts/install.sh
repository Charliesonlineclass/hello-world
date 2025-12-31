#!/bin/bash
# =============================================================================
# SCORPION KING - Installation Script
# =============================================================================
# One-command installer for the SCORPION AI automation platform.
#
# USAGE:
#   chmod +x scripts/install.sh
#   ./scripts/install.sh
#
# OPTIONS:
#   --no-docker    Skip Docker setup
#   --no-models    Skip Ollama model downloads
#   --dev          Development mode (no daemon)
#
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCORPION_DIR="${SCORPION_DIR:-$(pwd)}"
DOCKER_DIR="${SCORPION_DIR}/body/docker"
DATA_DIRS=("data" "logs" "transcripts" "quotes" "chromadb_data" "reports" "backups")

# Options
SKIP_DOCKER=false
SKIP_MODELS=false
DEV_MODE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-docker) SKIP_DOCKER=true; shift ;;
        --no-models) SKIP_MODELS=true; shift ;;
        --dev) DEV_MODE=true; shift ;;
        *) shift ;;
    esac
done

# =============================================================================
# FUNCTIONS
# =============================================================================

print_banner() {
    echo -e "${CYAN}"
    cat << 'EOF'
███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗
██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██║██╔═══██╗████╗  ██║
███████╗██║     ██║   ██║██████╔╝██████╔╝██║██║   ██║██╔██╗ ██║
╚════██║██║     ██║   ██║██╔══██╗██╔═══╝ ██║██║   ██║██║╚██╗██║
███████║╚██████╗╚██████╔╝██║  ██║██║     ██║╚██████╔╝██║ ╚████║
╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝
                    INSTALLATION SCRIPT
EOF
    echo -e "${NC}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_command() {
    if command -v "$1" &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# =============================================================================
# DEPENDENCY CHECKS
# =============================================================================

check_dependencies() {
    log_info "Checking dependencies..."

    local missing=()

    # Check Docker
    if ! check_command docker; then
        missing+=("docker")
    else
        log_success "Docker found: $(docker --version | head -n1)"
    fi

    # Check Docker Compose
    if ! check_command docker-compose && ! docker compose version &> /dev/null; then
        missing+=("docker-compose")
    else
        log_success "Docker Compose found"
    fi

    # Check Python
    if ! check_command python3; then
        missing+=("python3")
    else
        log_success "Python found: $(python3 --version)"
    fi

    # Check Ollama
    if ! check_command ollama; then
        log_warning "Ollama not found - will need to install separately"
        echo -e "  Install with: ${CYAN}curl -fsSL https://ollama.com/install.sh | sh${NC}"
    else
        log_success "Ollama found: $(ollama --version 2>/dev/null || echo 'installed')"
    fi

    # Check Git
    if ! check_command git; then
        missing+=("git")
    else
        log_success "Git found: $(git --version)"
    fi

    # Report missing dependencies
    if [ ${#missing[@]} -gt 0 ]; then
        log_error "Missing required dependencies: ${missing[*]}"
        echo ""
        echo "Please install the missing dependencies:"
        for dep in "${missing[@]}"; do
            case $dep in
                docker)
                    echo "  Docker: https://docs.docker.com/get-docker/"
                    ;;
                docker-compose)
                    echo "  Docker Compose: https://docs.docker.com/compose/install/"
                    ;;
                python3)
                    echo "  Python: apt install python3 python3-pip"
                    ;;
                git)
                    echo "  Git: apt install git"
                    ;;
            esac
        done
        exit 1
    fi

    log_success "All required dependencies found!"
}

# =============================================================================
# DIRECTORY SETUP
# =============================================================================

setup_directories() {
    log_info "Setting up directories..."

    for dir in "${DATA_DIRS[@]}"; do
        if [ ! -d "${SCORPION_DIR}/${dir}" ]; then
            mkdir -p "${SCORPION_DIR}/${dir}"
            log_success "Created: ${dir}/"
        else
            log_info "Exists: ${dir}/"
        fi
    done

    # Create Docker config directories
    mkdir -p "${DOCKER_DIR}/nginx/conf.d"
    mkdir -p "${DOCKER_DIR}/nginx/ssl"
    mkdir -p "${DOCKER_DIR}/n8n/workflows"
    mkdir -p "${DOCKER_DIR}/data"

    log_success "Directory structure ready"
}

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

setup_environment() {
    log_info "Setting up environment..."

    local env_file="${DOCKER_DIR}/.env"

    if [ -f "$env_file" ]; then
        log_warning ".env file already exists, skipping"
        return
    fi

    # Generate secure passwords
    local api_key=$(openssl rand -hex 16 2>/dev/null || echo "scorpion-$(date +%s)")
    local chroma_key=$(openssl rand -hex 16 2>/dev/null || echo "chroma-$(date +%s)")
    local db_pass=$(openssl rand -hex 16 2>/dev/null || echo "dbpass-$(date +%s)")

    cat > "$env_file" << EOF
# =============================================================================
# SCORPION Environment Configuration
# Generated: $(date)
# =============================================================================

# API Security
SCORPION_API_KEY=${api_key}
CHROMA_AUTH_TOKEN=${chroma_key}

# Database
POSTGRES_USER=scorpion
POSTGRES_PASSWORD=${db_pass}

# n8n
N8N_USER=commander
N8N_PASSWORD=scorpion

# Ollama
OLLAMA_HOST=http://host.docker.internal:11434

# Logging
LOG_LEVEL=INFO
EOF

    chmod 600 "$env_file"
    log_success "Environment file created: ${env_file}"
    log_warning "API Key: ${api_key} (save this!)"
}

# =============================================================================
# PYTHON DEPENDENCIES
# =============================================================================

install_python_deps() {
    log_info "Installing Python dependencies..."

    if [ -f "${SCORPION_DIR}/body/docker/requirements.txt" ]; then
        pip3 install -q -r "${SCORPION_DIR}/body/docker/requirements.txt" 2>/dev/null || {
            log_warning "Some Python packages failed to install (may need sudo)"
        }
    fi

    # Essential packages for CLI
    pip3 install -q rich click colorama requests 2>/dev/null || true

    log_success "Python dependencies installed"
}

# =============================================================================
# OLLAMA MODELS
# =============================================================================

setup_ollama() {
    if $SKIP_MODELS; then
        log_info "Skipping Ollama model setup (--no-models)"
        return
    fi

    if ! check_command ollama; then
        log_warning "Ollama not installed, skipping model setup"
        return
    fi

    log_info "Setting up Ollama models..."

    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        log_info "Starting Ollama..."
        ollama serve &> /dev/null &
        sleep 3
    fi

    # Models to pull
    local models=("mistral" "phi")

    for model in "${models[@]}"; do
        log_info "Pulling model: ${model}..."
        if ollama pull "$model" 2>/dev/null; then
            log_success "Model ready: ${model}"
        else
            log_warning "Failed to pull ${model} (try manually: ollama pull ${model})"
        fi
    done

    log_success "Ollama setup complete"
}

# =============================================================================
# DOCKER SETUP
# =============================================================================

setup_docker() {
    if $SKIP_DOCKER; then
        log_info "Skipping Docker setup (--no-docker)"
        return
    fi

    log_info "Setting up Docker containers..."

    cd "${DOCKER_DIR}"

    # Build images
    log_info "Building SCORPION Brain image..."
    if docker-compose build --quiet 2>/dev/null; then
        log_success "Docker images built"
    else
        log_warning "Docker build had warnings (continuing...)"
    fi

    # Start services
    if $DEV_MODE; then
        log_info "Starting services in foreground (dev mode)..."
        docker-compose up
    else
        log_info "Starting services..."
        if docker-compose up -d 2>/dev/null; then
            log_success "Docker services started"
        else
            log_error "Failed to start Docker services"
            return 1
        fi
    fi

    cd "${SCORPION_DIR}"
}

# =============================================================================
# VERIFICATION
# =============================================================================

verify_installation() {
    log_info "Verifying installation..."

    local all_ok=true

    # Check Docker containers
    if ! $SKIP_DOCKER; then
        if docker ps | grep -q "scorpion-brain"; then
            log_success "scorpion-brain container running"
        else
            log_warning "scorpion-brain container not running"
            all_ok=false
        fi
    fi

    # Check API
    sleep 5  # Wait for services to start
    if curl -s http://localhost:8080/health &> /dev/null; then
        log_success "SCORPION API responding"
    else
        log_warning "SCORPION API not responding (may still be starting)"
    fi

    # Check Ollama
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        log_success "Ollama responding"
    else
        log_warning "Ollama not responding"
    fi

    if $all_ok; then
        log_success "All services verified!"
    fi
}

# =============================================================================
# COMPLETION
# =============================================================================

print_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║            SCORPION INSTALLATION COMPLETE!                    ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${CYAN}Quick Commands:${NC}"
    echo "    Check status:      python -m integration.cli status"
    echo "    Ask MARCUS:        python -m integration.cli ask marcus \"Hello\""
    echo "    View logs:         docker-compose -f body/docker/docker-compose.yml logs -f"
    echo ""
    echo -e "  ${CYAN}Access Points:${NC}"
    echo "    API Docs:          http://localhost:8080/docs"
    echo "    n8n Workflows:     http://localhost:5678"
    echo "    ChromaDB:          http://localhost:8000"
    echo ""
    echo -e "  ${CYAN}Documentation:${NC}"
    echo "    Architecture:      docs/ARCHITECTURE.md"
    echo "    Quick Start:       docs/QUICKSTART.md"
    echo ""
    echo -e "${YELLOW}  Remember to save your API key from .env file!${NC}"
    echo ""
    echo -e "  ${GREEN}🦂 SCORPION is ready!${NC}"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    print_banner

    log_info "Starting SCORPION installation..."
    log_info "Installation directory: ${SCORPION_DIR}"
    echo ""

    check_dependencies
    echo ""

    setup_directories
    echo ""

    setup_environment
    echo ""

    install_python_deps
    echo ""

    setup_ollama
    echo ""

    setup_docker
    echo ""

    verify_installation
    echo ""

    print_completion
}

# Run main
main "$@"
