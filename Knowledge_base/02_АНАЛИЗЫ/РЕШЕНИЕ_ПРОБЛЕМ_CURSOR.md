# Решение проблем с подключением Cursor IDE

## Проблема
Периодически появляется ошибка: "Connection failed. If the problem persists, please check your internet connection or VPN"

## Быстрые решения

### 1. Перезапуск Cursor
Самое простое решение - полностью закрыть и перезапустить Cursor IDE.

### 2. Очистка кэша
1. Закройте Cursor полностью
2. Удалите следующие папки:
   - `%APPDATA%\Cursor\Cache`
   - `%LOCALAPPDATA%\Cursor\Cache`
   - `%APPDATA%\Cursor\CachedData`
   - `%LOCALAPPDATA%\Cursor\CachedData`
3. Запустите Cursor заново

**Или используйте скрипт:** `development/scripts/fix_cursor_connection.ps1` или `.bat`

### 3. Проверка интернет-соединения
```powershell
# Проверка соединения
Test-Connection -ComputerName "8.8.8.8" -Count 4

# Проверка DNS
Resolve-DnsName cursor.sh
```

### 4. Настройка DNS
Если проблемы с DNS, попробуйте использовать:
- **Google DNS:** 8.8.8.8, 8.8.4.4
- **Cloudflare DNS:** 1.1.1.1, 1.0.0.1

**Как изменить DNS в Windows:**
1. Откройте "Настройки сети и Интернет"
2. Выберите ваш сетевой адаптер
3. Нажмите "Изменить параметры адаптера"
4. Правый клик на адаптере → Свойства
5. Выберите "Протокол Интернета версии 4 (TCP/IPv4)"
6. Установите "Использовать следующие адреса DNS-серверов"
7. Введите предпочитаемый DNS: 8.8.8.8
8. Введите альтернативный DNS: 8.8.4.4

### 5. Проверка прокси и VPN
1. **Временное отключение VPN** - проверьте, не блокирует ли VPN соединение
2. **Проверка прокси-настроек:**
   ```powershell
   # Проверить настройки прокси
   Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
   ```
3. **Переменные окружения:**
   - Проверьте `HTTP_PROXY` и `HTTPS_PROXY`
   - Если установлены некорректно, удалите их

### 6. Файрвол и антивирус
1. Временно отключите файрвол Windows для проверки
2. Добавьте Cursor в исключения антивируса
3. Проверьте, не блокирует ли антивирус исходящие соединения

### 7. Сброс сетевых настроек
```powershell
# Сброс DNS кэша
ipconfig /flushdns

# Сброс сетевого стека (требует перезагрузки)
netsh winsock reset
netsh int ip reset
```

### 8. Проверка файрвола Windows
```powershell
# Проверить правила файрвола для Cursor
Get-NetFirewallApplicationFilter | Where-Object {$_.Program -like "*Cursor*"}
```

Если правил нет, добавьте:
```powershell
New-NetFirewallRule -DisplayName "Cursor IDE" -Direction Outbound -Program "C:\Users\$env:USERNAME\AppData\Local\Programs\cursor\Cursor.exe" -Action Allow
```

## Автоматическая диагностика

Используйте скрипты для автоматической диагностики:

### PowerShell (рекомендуется)
```powershell
cd development/scripts
.\fix_cursor_connection.ps1
```

### Batch файл
```cmd
cd development\scripts
fix_cursor_connection.bat
```

## Дополнительные решения

### Увеличение таймаутов (если доступно в настройках)
В настройках Cursor попробуйте увеличить таймауты соединения, если такая опция есть.

### Проверка логов
Логи Cursor обычно находятся в:
- `%APPDATA%\Cursor\logs`
- `%LOCALAPPDATA%\Cursor\logs`

Проверьте логи на наличие ошибок соединения.

### Переустановка Cursor
Если ничего не помогает:
1. Экспортируйте настройки (если возможно)
2. Полностью удалите Cursor
3. Переустановите последнюю версию с официального сайта

## Профилактика

1. **Регулярная очистка кэша** - раз в неделю
2. **Обновление Cursor** - используйте последнюю версию
3. **Стабильное интернет-соединение** - проверьте качество соединения
4. **Мониторинг VPN** - убедитесь, что VPN не блокирует соединения

## Если проблема сохраняется

1. Проверьте статус серверов Cursor на их официальном сайте
2. Создайте issue в репозитории Cursor на GitHub
3. Проверьте, не блокирует ли ваш провайдер доступ к серверам Cursor

## Контакты поддержки

- GitHub Issues: https://github.com/getcursor/cursor/issues
- Официальный сайт: https://cursor.sh

