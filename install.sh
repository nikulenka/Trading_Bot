#!/bin/bash

###############################################################################
# Trading Bot - Automated VPS Installation Script
# Repository: https://github.com/nikulenka/Trading_Bot
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_step() {
    echo -e "\n${BLUE}==>${NC} ${GREEN}$1${NC}\n"
}

print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    print_warning "Please do not run as root. Run as regular user with sudo privileges."
    exit 1
fi

# Banner
echo -e "${BLUE}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║           Trading Bot - VPS Installation Script            ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Configuration
INSTALL_DIR="/opt/trading-bot"
REPO_URL="https://github.com/nikulenka/Trading_Bot.git"

print_step "Step 1/8: Updating system packages"
sudo apt update -qq
sudo apt upgrade -y -qq
print_success "System updated"

print_step "Step 2/8: Installing dependencies"
sudo apt install -y -qq git curl
print_success "Dependencies installed"

print_step "Step 3/8: Installing Docker"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_success "Docker installed"
else
    print_success "Docker already installed"
fi

print_step "Step 4/8: Installing Docker Compose"
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_success "Docker Compose installed"
else
    print_success "Docker Compose already installed"
fi

print_step "Step 5/8: Cloning repository"
if [ -d "$INSTALL_DIR" ]; then
    print_warning "Directory $INSTALL_DIR already exists. Updating..."
    cd $INSTALL_DIR
    sudo git pull
else
    sudo git clone $REPO_URL $INSTALL_DIR
    sudo chown -R $USER:$USER $INSTALL_DIR
fi
cd $INSTALL_DIR
print_success "Repository cloned to $INSTALL_DIR"

print_step "Step 6/8: Configuring environment"
# Create backend .env file
cat > backend/.env << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
EOF
print_success "Environment configured"

print_step "Step 7/8: Starting services with Docker Compose"
# Need to use newgrp or sg to apply docker group without logout
if groups | grep -q docker; then
    docker-compose up -d
else
    print_warning "Docker group not yet active. Starting with sudo..."
    sudo docker-compose up -d
fi
print_success "Services started"

print_step "Step 8/8: Verifying installation"
sleep 5  # Wait for services to start

# Check if containers are running
if sudo docker-compose ps | grep -q "Up"; then
    print_success "Containers are running"
else
    print_error "Containers failed to start. Check logs with: docker-compose logs"
    exit 1
fi

# Check backend health
if curl -s http://localhost:8000/health | grep -q "ok"; then
    print_success "Backend API is healthy"
else
    print_warning "Backend API health check failed. It may still be starting..."
fi

# Get server IP
SERVER_IP=$(curl -s ifconfig.me || echo "YOUR_SERVER_IP")

# Final message
echo -e "\n${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              ✓ Installation Complete!                      ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${BLUE}Access your Trading Bot:${NC}"
echo -e "  Frontend:  ${GREEN}http://$SERVER_IP:3000${NC}"
echo -e "  Backend:   ${GREEN}http://$SERVER_IP:8000${NC}"
echo -e "  Health:    ${GREEN}http://$SERVER_IP:8000/health${NC}\n"

echo -e "${BLUE}Useful commands:${NC}"
echo -e "  View logs:      ${YELLOW}cd $INSTALL_DIR && docker-compose logs -f${NC}"
echo -e "  Restart:        ${YELLOW}cd $INSTALL_DIR && docker-compose restart${NC}"
echo -e "  Stop:           ${YELLOW}cd $INSTALL_DIR && docker-compose down${NC}"
echo -e "  Update:         ${YELLOW}cd $INSTALL_DIR && git pull && docker-compose up -d --build${NC}\n"

echo -e "${BLUE}Configure firewall (optional):${NC}"
echo -e "  ${YELLOW}sudo ufw allow 3000/tcp${NC}  # Frontend"
echo -e "  ${YELLOW}sudo ufw allow 8000/tcp${NC}  # Backend API\n"

if ! groups | grep -q docker; then
    echo -e "${YELLOW}⚠ NOTE: You need to log out and log back in for Docker group changes to take effect.${NC}"
    echo -e "${YELLOW}   After re-login, restart services with: cd $INSTALL_DIR && docker-compose restart${NC}\n"
fi

print_success "Installation script completed successfully!"
