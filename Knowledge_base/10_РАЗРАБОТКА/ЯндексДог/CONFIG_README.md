# Конфигурация ЯндексДог

## API ключи

### Yandex MapKit API Key

**Файл:** `api_key.txt`  
**Формат:** Простой текстовый файл с одной строкой

**API Key:**
```
c75cd846-c6de-425a-b974-41917fec5071
```

**Использование в коде:**

Java (Android):
```java
String apiKey = readApiKeyFromFile("config/api_key.txt");
MapKitFactory.setApiKey(apiKey);
```

Native (C):
```c
// Чтение API ключа из файла или передача через JNI
```

## Безопасность

⚠️ **Важно:** 
- Этот файл НЕ должен быть закоммичен в git репозиторий
- Добавьте `config/api_key.txt` в `.gitignore`
- Не распространяйте API ключ публично

## Файлы

- `api_key.txt` - API ключ Yandex MapKit (простой текстовый файл)
- `api_key.properties` - API ключ в формате properties (для Java)
- `README.md` - Этот файл с инструкциями

