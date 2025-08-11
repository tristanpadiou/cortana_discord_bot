#!/bin/bash

# Raspberry Pi Setup Script for Cortana Discord Bot
# Run this script once on your Raspberry Pi to set up the environment

set -e

echo "🚀 Setting up Raspberry Pi for Cortana Discord Bot deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/tristanpadiou/cortana_discord_bot.git"  # Update this!
APP_DIR="$HOME/cortana_discord_bot"
SERVICE_NAME="cortana-discord-bot"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
print_status "Installing required packages..."
sudo apt install -y \
    git \
    curl \
    wget \
    htop \
    nano \
    ca-certificates \
    gnupg \
    lsb-release

# Check if Docker is already installed
if command -v docker &> /dev/null; then
    print_status "Docker is already installed. Checking version..."
    docker --version
    
    # Check if Docker Compose plugin is available
    if docker compose version &> /dev/null; then
        print_status "Docker Compose plugin is already available."
    else
        print_warning "Docker Compose plugin not found. Installing..."
        # Install Docker Compose plugin
        sudo apt update
        sudo apt install -y docker-compose-plugin
    fi
else
    print_status "Installing Docker CE for Raspberry Pi..."
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Add Docker repository
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker CE
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
fi

# Add user to docker group
print_status "Adding user to docker group..."
sudo usermod -aG docker $USER

# Enable and start Docker
print_status "Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

# Clone the repository
print_status "Cloning repository..."
if [ -d "$APP_DIR" ]; then
    print_warning "Directory $APP_DIR already exists. Pulling latest changes..."
    cd "$APP_DIR"
    git pull
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi

# Login to GitHub Container Registry
print_status "Setting up container registry access..."
echo "You'll need to authenticate with GitHub Container Registry."
echo "Please create a Personal Access Token (PAT) with 'read:packages' permission:"
echo "https://github.com/settings/tokens/new?scopes=read:packages"
echo ""
read -p "Enter your GitHub username: " GITHUB_USERNAME
read -s -p "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

# Test login
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
if [ $? -eq 0 ]; then
    print_status "✅ Successfully logged into GitHub Container Registry"
else
    print_error "❌ Failed to login to GitHub Container Registry"
    exit 1
fi

# Configure Git to use token authentication
print_status "Configuring Git authentication..."
git config --global credential.helper store
echo "https://$GITHUB_USERNAME:$GITHUB_TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials
print_status "✅ Git authentication configured"

# Create necessary directories
print_status "Creating application directories..."
mkdir -p logs data tmp

# Set proper permissions
chmod -R 755 logs data tmp

# Handle environment file configuration
print_status "Setting up environment configuration..."

# Check if .env file already exists in the app directory
if [ -f .env ]; then
    print_status "✅ .env file already exists in app directory, keeping existing configuration"
elif [ -f "$HOME/Desktop/cortana_discord_bot_env/.env" ]; then
    print_status "📋 Found .env file in ~/Desktop/cortana_discord_bot_env/, copying to app directory..."
    cp "$HOME/Desktop/cortana_discord_bot_env/.env" .env
    chmod 600 .env  # Secure permissions
    print_status "✅ .env file copied successfully!"
else
    print_warning "No .env file found. Creating template..."
    cat > .env.template << EOF
# Cortana API Environment Configuration
# Copy this file to .env and customize with your actual values

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Add your specific environment variables here
# OPENAI_API_KEY=your_openai_key_here
# NOTION_TOKEN=your_notion_token_here
# OUTLOOK_CLIENT_ID=your_outlook_client_id_here
# OUTLOOK_CLIENT_SECRET=your_outlook_client_secret_here
# DATABASE_URL=your_database_url_here

# Logfire Logging (Optional)
# cortana_api_logfire_token=your_logfire_token_here
EOF
    
    print_warning "⚠️  ENVIRONMENT SETUP NEEDED:"
    print_warning "   Option 1 (Recommended): Place your .env file at ~/Desktop/cortana_discord_bot_env/.env and re-run this script"
    print_warning "   Option 2: Manual setup:"
    print_warning "     cp .env.template .env"
    print_warning "     nano .env  # Add your actual API keys and secrets"
fi

# Create systemd service for auto-start
print_status "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null << EOF
[Unit]
Description=Cortana Discord Bot Docker Service
Requires=docker.service
After=docker.service
StartLimitIntervalSec=0

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0
User=$USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
print_status "Enabling systemd service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Create update script
print_status "Creating update script..."
cat > update-app.sh << 'EOF'
#!/bin/bash
# Manual update script

set -e

echo "🔄 Updating Cortana API..."

# Pull latest changes
git pull

# Pull latest image and restart
docker compose down
docker compose pull
docker compose up -d

# Clean up old images
docker image prune -f

echo "✅ Update complete!"
EOF

chmod +x update-app.sh

# Create monitoring script
print_status "Creating monitoring script..."
cat > monitor.sh << 'EOF'
#!/bin/bash
# Simple monitoring script

echo "📊 Cortana API Status:"
echo "===================="

# Check if containers are running
echo "🐳 Docker Status:"
docker compose ps

echo ""
echo "📈 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo ""
echo "📝 Recent Logs:"
docker compose logs --tail=10
EOF

chmod +x monitor.sh

# Create log rotation configuration
print_status "Setting up log rotation..."
sudo tee /etc/logrotate.d/cortana-api > /dev/null << EOF
$APP_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}
EOF

print_status "Setup complete! 🎉"
echo ""
print_warning "⚠️  IMPORTANT NEXT STEPS:"

# Check if .env was successfully set up
if [ -f "$APP_DIR/.env" ]; then
    print_status "✅ Environment variables are configured!"
    echo "1. Log out and back in for Docker group changes to take effect"
    echo ""
    echo "2. Start your application:"
    echo "   cd $APP_DIR && docker compose up -d"
    echo ""
    echo "3. Test the setup by running:"
    echo "   cd $APP_DIR && ./update-app.sh"
else
    echo "1. Set up your environment variables:"
    echo "   Option A: Place .env file at ~/Desktop/cortana_discord_bot_env/.env and re-run this script"
    echo "   Option B: Manual setup in $APP_DIR"
    echo ""
    echo "2. Log out and back in for Docker group changes to take effect"
    echo ""
    echo "3. Start your application:"
    echo "   cd $APP_DIR && docker compose up -d"
fi

echo ""
echo "📊 Monitor your application with:"
echo "   cd $APP_DIR && ./monitor.sh"
echo ""
print_status "The service will auto-start on boot. Manual control:"
echo "   sudo systemctl start $SERVICE_NAME"
echo "   sudo systemctl stop $SERVICE_NAME"
echo "   sudo systemctl status $SERVICE_NAME"
