# 🚀 Quick Install

One-command installation for VPS deployment.

## Installation

### Option 1: Direct from GitHub (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/nikulenka/Trading_Bot/main/install.sh | bash
```

### Option 2: Download and run

```bash
wget https://raw.githubusercontent.com/nikulenka/Trading_Bot/main/install.sh
chmod +x install.sh
./install.sh
```

### Option 3: Manual clone and run

```bash
git clone https://github.com/nikulenka/Trading_Bot.git
cd Trading_Bot
chmod +x install.sh
./install.sh
```

## What the script does

1. ✅ Updates system packages
2. ✅ Installs Git and Curl
3. ✅ Installs Docker
4. ✅ Installs Docker Compose
5. ✅ Clones the repository to `/opt/trading-bot`
6. ✅ Creates environment configuration
7. ✅ Starts all services with Docker Compose
8. ✅ Verifies installation

## After installation

Access your application:
- **Frontend**: `http://YOUR_VPS_IP:3000`
- **Backend API**: `http://YOUR_VPS_IP:8000`
- **Health Check**: `http://YOUR_VPS_IP:8000/health`

## Requirements

- Ubuntu 20.04+ or Debian 11+
- Minimum 2GB RAM
- 20GB disk space
- User with sudo privileges (don't run as root)

## Troubleshooting

### View logs
```bash
cd /opt/trading-bot
docker-compose logs -f
```

### Restart services
```bash
cd /opt/trading-bot
docker-compose restart
```

### Check status
```bash
cd /opt/trading-bot
docker-compose ps
```

## Manual installation

For detailed manual installation instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)
