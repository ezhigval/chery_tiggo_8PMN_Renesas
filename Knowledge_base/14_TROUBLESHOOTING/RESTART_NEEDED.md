# ⚠️ ТРЕБУЕТСЯ ПЕРЕЗАПУСК GUI

## Проблема

После нажатия Start в логах нет записей о попытке запуска QEMU. Это означает, что:
- Либо код не перезагрузился (Python кэширует модули)
- Либо есть ошибка, которая не логируется

## Решение

### Вариант 1: Перезапуск GUI (РЕКОМЕНДУЕТСЯ)

1. **Закройте окно GUI** (или нажмите Ctrl+C в терминале, если запущено оттуда)

2. **Запустите заново:**
   ```bash
   cd /Users/valentinezov/Projects/Tiggo/development/emulator
   python3 main.py
   ```

3. **Нажмите Start** в новом окне

### Вариант 2: Проверка кода

Убедитесь, что изменения загружены:
```bash
cd development/emulator
grep -A 5 "project_root = Path" gui/main_window.py
```

Должно быть:
```python
project_root = Path(__file__).parent.parent.parent.parent
```

### Вариант 3: Альтернативный запуск

Если GUI не работает, используйте скрипт:
```bash
cd development/scripts
./simulate_t18fl3_complete.sh --android
```

## После перезапуска

Следите за логами:
```bash
tail -f development/emulator/logs/*.log | grep -E "(QEMU|ERROR|started)"
```

Должны появиться:
- `=== QEMU START REQUESTED ===`
- `QEMU command built: X arguments`
- `QEMU process started with PID: XXXX`

