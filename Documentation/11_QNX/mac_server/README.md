# Reverse Tunnel Server для Mac

Сервер для приема входящих соединений от ГУ через интернет.

## Быстрый старт

```bash
# Запустить сервер
./start_tunnel_server.sh 22222

# Или напрямую
python3 reverse_tunnel_server.py 22222
```

## Настройка

1. **Изменить порт (опционально):**
   ```bash
   ./start_tunnel_server.sh 33333
   ```

2. **Настроить файрвол:**
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/bin/python3
   ```

3. **Настроить роутер (если Mac за NAT):**
   - Пробросить порт 22222 на Mac

4. **Настроить Dynamic DNS (опционально):**
   - Зарегистрироваться на noip.com или duckdns.org
   - Обновлять IP автоматически

## Автозапуск

Создать LaunchAgent для автозапуска при загрузке Mac (см. REMOTE_TUNNEL_SETUP.md)

## Протокол

Сервер использует простой текстовый протокол:

- `TUNNEL_READY` - приветствие от сервера
- `DEVICE_INFO:...` - информация от клиента
- `ADB:команда` - выполнение ADB команды
- `QNX:команда` - выполнение QNX команды
- `SHELL:команда` - выполнение shell команды
- `PING` - проверка соединения
- `STATUS` - статус сервера

## Требования

- Python 3.6+
- ADB (для выполнения ADB команд)
- Доступ в интернет
- Публичный IP или Dynamic DNS

