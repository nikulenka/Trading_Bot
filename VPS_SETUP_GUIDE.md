# 🚀 Пошаговая установка Trading Bot на VPS

## Готовые команды для копирования

Ваш репозиторий: `https://github.com/nikulenka/Trading_Bot`

---

## Вариант 1: Быстрая установка через Docker (Рекомендуется) 🐳

### Шаг 1: Подключитесь к VPS

```bash
ssh root@YOUR_VPS_IP
# или
ssh your_username@YOUR_VPS_IP
```

### Шаг 2: Установите Docker

Скопируйте и выполните эти команды:

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Проверка установки
docker --version
docker-compose --version
```

**После этого выйдите и зайдите снова:**
```bash
exit
ssh root@YOUR_VPS_IP
```

### Шаг 3: Клонируйте репозиторий

```bash
# Создание директории и клонирование
cd /opt
sudo git clone https://github.com/nikulenka/Trading_Bot.git trading-bot
sudo chown -R $USER:$USER /opt/trading-bot
cd /opt/trading-bot
```

### Шаг 4: Настройте окружение

Создайте файл `.env` для backend:

```bash
cat > backend/.env << 'EOF'
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
EOF
```

### Шаг 5: Запустите приложение

```bash
# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f
```

### Шаг 6: Проверьте работу

```bash
# Проверка backend
curl http://localhost:8000/health

# Должен вернуть: {"status":"ok"}
```

### Шаг 7: Откройте в браузере

- **Frontend**: `http://YOUR_VPS_IP:3000`
- **Backend API**: `http://YOUR_VPS_IP:8000`

### Шаг 8: Настройте Firewall (опционально)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 3000/tcp  # Frontend
sudo ufw allow 8000/tcp  # Backend API
sudo ufw enable
sudo ufw status
```

---

## ✅ Готово!

Ваш Trading Bot теперь работает на VPS!

### Полезные команды для управления:

```bash
# Просмотр логов
docker-compose logs -f backend
docker-compose logs -f frontend

# Перезапуск
docker-compose restart

# Остановка
docker-compose down

# Обновление после изменений в GitHub
cd /opt/trading-bot
git pull
docker-compose up -d --build

# Просмотр использования ресурсов
docker stats
```

---

## Вариант 2: Production установка с Nginx и SSL 🔒

Если у вас есть доменное имя и нужен HTTPS:

### Шаг 1-3: Как в Варианте 1

### Шаг 4: Установите Nginx

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### Шаг 5: Настройте Nginx

Замените `yourdomain.com` на ваш домен:

```bash
sudo tee /etc/nginx/sites-available/trading-bot > /dev/null << 'EOF'
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

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
    server_name yourdomain.com www.yourdomain.com;

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

# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/trading-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Шаг 6: Настройте SSL

```bash
# Замените на ваши домены
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d api.yourdomain.com
```

### Шаг 7: Обновите CORS

```bash
# Обновите backend/.env
nano backend/.env
```

Добавьте ваш домен:
```
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com,https://www.yourdomain.com
```

Перезапустите:
```bash
docker-compose restart backend
```

---

## 🔍 Troubleshooting

### Проблема: Docker не запускается

```bash
# Проверьте статус Docker
sudo systemctl status docker

# Запустите Docker
sudo systemctl start docker
```

### Проблема: Порт занят

```bash
# Проверьте, что использует порт
sudo netstat -tulpn | grep 8000
sudo netstat -tulpn | grep 3000

# Остановите процесс или измените порт в docker-compose.yml
```

### Проблема: Нет данных

```bash
# Проверьте наличие CSV файлов
ls -lh /opt/trading-bot/backend/data/

# Если файлов нет, загрузите их
cd /opt/trading-bot/backend
# Скопируйте CSV файлы с локального компьютера или загрузите с Binance
```

### Проблема: CORS ошибки

```bash
# Проверьте backend/.env
cat backend/.env

# Убедитесь, что CORS_ORIGINS включает ваш домен
# Перезапустите backend
docker-compose restart backend
```

---

## 📊 Мониторинг

### Просмотр логов в реальном времени

```bash
# Все сервисы
docker-compose logs -f

# Только backend
docker-compose logs -f backend

# Только frontend
docker-compose logs -f frontend

# Последние 100 строк
docker-compose logs --tail=100
```

### Проверка использования ресурсов

```bash
# Docker статистика
docker stats

# Системные ресурсы
htop

# Дисковое пространство
df -h
```

---

## 🔄 Обновление после изменений

Когда вы обновите код на GitHub:

```bash
cd /opt/trading-bot
git pull
docker-compose down
docker-compose up -d --build
docker-compose logs -f
```

---

## 📞 Нужна помощь?

1. Проверьте логи: `docker-compose logs -f`
2. Проверьте статус: `docker-compose ps`
3. Проверьте health: `curl http://localhost:8000/health`
4. Смотрите DEPLOYMENT.md для подробной информации
