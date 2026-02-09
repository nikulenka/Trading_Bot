---
description: Deploy Trading_Bot to VPS server
---

# Развертывание Trading_Bot на VPS

Этот workflow описывает полный процесс развертывания Trading_Bot на VPS сервере.

## Предварительные требования

- VPS сервер с Ubuntu 20.04+ или Debian 11+
- SSH доступ к серверу
- Доменное имя (опционально, для HTTPS)
- Минимум 2GB RAM, 20GB диска

## Шаг 1: Подключение к VPS

```bash
ssh root@YOUR_VPS_IP
# или
ssh your_username@YOUR_VPS_IP
```

## Шаг 2: Установка необходимых пакетов

// turbo
```bash
sudo apt update && sudo apt upgrade -y
```

// turbo
```bash
sudo apt install -y git curl python3 python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx
```

// turbo
```bash
# Установка Node.js 18+ (если версия старая)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

## Шаг 3: Клонирование репозитория

```bash
cd /opt
sudo git clone YOUR_REPOSITORY_URL trading-bot
sudo chown -R $USER:$USER /opt/trading-bot
cd /opt/trading-bot
```

> **Примечание**: Замените `YOUR_REPOSITORY_URL` на URL вашего Git репозитория.
> Если у вас еще нет репозитория, сначала создайте его на GitHub/GitLab и запушьте код.

## Шаг 4: Настройка Backend

```bash
cd /opt/trading-bot/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Создайте файл `.env`:

```bash
cat > .env << 'EOF'
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Origins (добавьте ваш домен)
CORS_ORIGINS=http://localhost:3000,http://YOUR_DOMAIN

# Optional: API Keys для бирж (если нужны)
# BINANCE_API_KEY=your_key
# BINANCE_API_SECRET=your_secret
EOF
```

## Шаг 5: Настройка Frontend

```bash
cd /opt/trading-bot/frontend
npm install
```

Создайте файл `.env.production`:

```bash
cat > .env.production << 'EOF'
NEXT_PUBLIC_API_URL=http://YOUR_VPS_IP:8000
# или если используете домен:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
EOF
```

Соберите production build:

```bash
npm run build
```

## Шаг 6: Создание systemd сервисов

### Backend Service

```bash
sudo tee /etc/systemd/system/trading-bot-backend.service > /dev/null << 'EOF'
[Unit]
Description=Trading Bot Backend API
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/trading-bot/backend
Environment="PATH=/opt/trading-bot/backend/venv/bin"
ExecStart=/opt/trading-bot/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

> **Важно**: Замените `YOUR_USERNAME` на ваше имя пользователя (узнать: `whoami`)

### Frontend Service

```bash
sudo tee /etc/systemd/system/trading-bot-frontend.service > /dev/null << 'EOF'
[Unit]
Description=Trading Bot Frontend
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/trading-bot/frontend
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

## Шаг 7: Запуск сервисов

// turbo
```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-bot-backend
sudo systemctl enable trading-bot-frontend
sudo systemctl start trading-bot-backend
sudo systemctl start trading-bot-frontend
```

Проверка статуса:

// turbo
```bash
sudo systemctl status trading-bot-backend
sudo systemctl status trading-bot-frontend
```

## Шаг 8: Настройка Nginx (Reverse Proxy)

```bash
sudo tee /etc/nginx/sites-available/trading-bot > /dev/null << 'EOF'
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;  # или используйте IP

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;  # или используйте IP

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
EOF
```

> **Примечание**: Если у вас нет домена, используйте только IP адрес:
> ```nginx
> server_name YOUR_VPS_IP;
> ```

Активируйте конфигурацию:

// turbo
```bash
sudo ln -s /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Шаг 9: Настройка HTTPS (опционально, если есть домен)

```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

Certbot автоматически настроит SSL и перенаправление с HTTP на HTTPS.

## Шаг 10: Настройка Firewall

// turbo
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Шаг 11: Проверка работы

Откройте в браузере:
- Frontend: `http://YOUR_VPS_IP` или `https://yourdomain.com`
- Backend API: `http://YOUR_VPS_IP/api/v1/health` или `https://api.yourdomain.com/health`

## Управление сервисами

### Просмотр логов

```bash
# Backend логи
sudo journalctl -u trading-bot-backend -f

# Frontend логи
sudo journalctl -u trading-bot-frontend -f
```

### Перезапуск после обновления кода

```bash
cd /opt/trading-bot
git pull

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart trading-bot-backend

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl restart trading-bot-frontend
```

### Остановка/запуск

```bash
sudo systemctl stop trading-bot-backend
sudo systemctl stop trading-bot-frontend

sudo systemctl start trading-bot-backend
sudo systemctl start trading-bot-frontend
```

## Альтернатива: Развертывание через Docker

См. файлы `Dockerfile` и `docker-compose.yml` в корне проекта.

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Запуск
cd /opt/trading-bot
docker-compose up -d
```

## Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
sudo journalctl -u trading-bot-backend -n 50

# Проверьте, что порт 8000 свободен
sudo netstat -tulpn | grep 8000

# Проверьте права доступа
ls -la /opt/trading-bot/backend
```

### Frontend не запускается

```bash
# Проверьте логи
sudo journalctl -u trading-bot-frontend -n 50

# Проверьте build
cd /opt/trading-bot/frontend
npm run build
```

### Проблемы с CORS

Убедитесь, что в `backend/.env` указаны правильные CORS_ORIGINS:
```
CORS_ORIGINS=http://yourdomain.com,https://yourdomain.com
```

И в `backend/main.py` origins включают ваш домен.
