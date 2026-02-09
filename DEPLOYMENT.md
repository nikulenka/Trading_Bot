# 🚀 Развертывание Trading Bot на VPS

Полное руководство по развертыванию торгового бота на VPS сервере.

## 📋 Содержание

1. [Быстрый старт (Docker)](#быстрый-старт-docker)
2. [Ручная установка](#ручная-установка)
3. [Настройка окружения](#настройка-окружения)
4. [Управление сервисами](#управление-сервисами)
5. [Мониторинг и логи](#мониторинг-и-логи)
6. [Обновление](#обновление)
7. [Troubleshooting](#troubleshooting)

---

## 🐳 Быстрый старт (Docker)

### Предварительные требования

- VPS с Ubuntu 20.04+ / Debian 11+
- Минимум 2GB RAM, 20GB диска
- Docker и Docker Compose

### Установка Docker

```bash
# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Перезайдите в систему для применения прав
exit
```

### Развертывание

```bash
# 1. Клонируйте репозиторий
git clone YOUR_REPOSITORY_URL /opt/trading-bot
cd /opt/trading-bot

# 2. Создайте .env файл для backend
cat > backend/.env << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
EOF

# 3. Запустите приложение
docker-compose up -d

# 4. Проверьте статус
docker-compose ps
docker-compose logs -f
```

Приложение будет доступно:
- **Frontend**: http://YOUR_VPS_IP:3000
- **Backend API**: http://YOUR_VPS_IP:8000
- **Health check**: http://YOUR_VPS_IP:8000/health

### Production развертывание с Nginx

Для production окружения с SSL:

```bash
# 1. Настройте домены в nginx.conf
nano nginx.conf
# Замените yourdomain.com на ваш домен

# 2. Создайте директорию для SSL сертификатов
mkdir -p ssl

# 3. Поместите ваши SSL сертификаты
# ssl/cert.pem - сертификат
# ssl/key.pem - приватный ключ

# 4. Запустите production конфигурацию
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🔧 Ручная установка

Подробная инструкция доступна в workflow:

```bash
# Используйте workflow для пошаговой установки
cat .agent/workflows/deploy-to-vps.md
```

Основные шаги:
1. Установка зависимостей (Python, Node.js, Nginx)
2. Настройка Backend (FastAPI + Uvicorn)
3. Настройка Frontend (Next.js)
4. Создание systemd сервисов
5. Настройка Nginx reverse proxy
6. Настройка SSL с Certbot

---

## ⚙️ Настройка окружения

### Backend Environment Variables

Создайте `backend/.env`:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS Origins (добавьте ваш домен)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Optional: Binance API (для live trading)
# BINANCE_API_KEY=your_api_key
# BINANCE_API_SECRET=your_api_secret
```

### Frontend Environment Variables

Создайте `frontend/.env.production`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://YOUR_VPS_IP:8000
# или для production с доменом:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### CORS Configuration

Обновите `backend/main.py` для добавления вашего домена:

```python
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://yourdomain.com",  # Добавьте ваш домен
    "https://www.yourdomain.com",
]
```

---

## 🎮 Управление сервисами

### Docker

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Перезапуск
docker-compose restart

# Просмотр логов
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Пересборка после изменений
docker-compose up -d --build
```

### Systemd (ручная установка)

```bash
# Статус
sudo systemctl status trading-bot-backend
sudo systemctl status trading-bot-frontend

# Запуск/остановка
sudo systemctl start trading-bot-backend
sudo systemctl stop trading-bot-backend

# Перезапуск
sudo systemctl restart trading-bot-backend
sudo systemctl restart trading-bot-frontend

# Автозапуск
sudo systemctl enable trading-bot-backend
sudo systemctl enable trading-bot-frontend
```

---

## 📊 Мониторинг и логи

### Docker логи

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend

# Последние 100 строк
docker-compose logs --tail=100 backend
```

### Systemd логи

```bash
# Просмотр логов backend
sudo journalctl -u trading-bot-backend -f

# Последние 50 строк
sudo journalctl -u trading-bot-backend -n 50

# Логи за сегодня
sudo journalctl -u trading-bot-backend --since today
```

### Nginx логи

```bash
# Access logs
sudo tail -f /var/log/nginx/access.log

# Error logs
sudo tail -f /var/log/nginx/error.log
```

### Мониторинг ресурсов

```bash
# Docker stats
docker stats

# Системные ресурсы
htop

# Дисковое пространство
df -h
```

---

## 🔄 Обновление

### Docker развертывание

```bash
cd /opt/trading-bot

# 1. Получите последние изменения
git pull

# 2. Пересоберите и перезапустите
docker-compose down
docker-compose up -d --build

# 3. Проверьте логи
docker-compose logs -f
```

### Ручная установка

```bash
cd /opt/trading-bot

# 1. Получите изменения
git pull

# 2. Обновите backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart trading-bot-backend

# 3. Обновите frontend
cd ../frontend
npm install
npm run build
sudo systemctl restart trading-bot-frontend

# 4. Проверьте статус
sudo systemctl status trading-bot-backend
sudo systemctl status trading-bot-frontend
```

---

## 🔍 Troubleshooting

### Backend не запускается

```bash
# Проверьте логи
docker-compose logs backend
# или
sudo journalctl -u trading-bot-backend -n 50

# Проверьте порт
sudo netstat -tulpn | grep 8000

# Проверьте .env файл
cat backend/.env

# Проверьте права доступа
ls -la backend/
```

### Frontend не запускается

```bash
# Проверьте логи
docker-compose logs frontend

# Проверьте build
cd frontend
npm run build

# Проверьте переменные окружения
cat .env.production
```

### CORS ошибки

1. Проверьте `backend/.env`:
   ```env
   CORS_ORIGINS=http://yourdomain.com,https://yourdomain.com
   ```

2. Проверьте `backend/main.py`:
   ```python
   origins = [
       "http://localhost:3000",
       "https://yourdomain.com",
   ]
   ```

3. Перезапустите backend:
   ```bash
   docker-compose restart backend
   ```

### Проблемы с SSL

```bash
# Проверьте сертификаты
sudo certbot certificates

# Обновите сертификаты
sudo certbot renew

# Проверьте Nginx конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl restart nginx
```

### Высокое использование памяти

```bash
# Проверьте использование
docker stats

# Ограничьте память для контейнеров
# Добавьте в docker-compose.yml:
services:
  backend:
    mem_limit: 512m
  frontend:
    mem_limit: 512m
```

### База данных не обновляется

```bash
# Проверьте наличие данных
ls -lh backend/data/

# Проверьте права доступа
sudo chown -R $USER:$USER backend/data/

# Повторно загрузите данные
cd backend
python fetch_data.py
```

---

## 🔒 Безопасность

### Firewall

```bash
# Настройте UFW
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

### Регулярные обновления

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Обновление Docker образов
docker-compose pull
docker-compose up -d
```

### Backup

```bash
# Backup данных
tar -czf trading-bot-backup-$(date +%Y%m%d).tar.gz \
  /opt/trading-bot/backend/data \
  /opt/trading-bot/backend/.env \
  /opt/trading-bot/frontend/.env.production

# Восстановление
tar -xzf trading-bot-backup-YYYYMMDD.tar.gz -C /
```

---

## 📞 Поддержка

Для получения помощи:
1. Проверьте логи (см. раздел "Мониторинг и логи")
2. Изучите раздел "Troubleshooting"
3. Проверьте техническую документацию: `TECHNICAL_DOCUMENTATION.md`

---

## 📝 Полезные команды

```bash
# Быстрая проверка всех сервисов
docker-compose ps && curl -s http://localhost:8000/health

# Очистка Docker
docker system prune -a

# Просмотр всех портов
sudo netstat -tulpn

# Проверка дискового пространства
du -sh /opt/trading-bot/*

# Мониторинг в реальном времени
watch -n 1 'docker stats --no-stream'
```
