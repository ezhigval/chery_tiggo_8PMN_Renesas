# Инструкция по использованию API ключа

## Текущий API ключ

```
c75cd846-c6de-425a-b974-41917fec5071
```

## Как использовать в коде

### Вариант 1: Прямое использование (только для тестирования)

В `MainActivity.java` раскомментировать:

```java
MapKitFactory.setApiKey("c75cd846-c6de-425a-b974-41917fec5071");
MapKitFactory.initialize(this);
```

### Вариант 2: Чтение из файла (текущая реализация)

Код уже настроен на чтение из файла `yandex_mapkit_api_key.txt`.

### Вариант 3: Чтение из assets (рекомендуется для production)

1. Создать файл `app/src/main/assets/api_key.txt`
2. Поместить туда API ключ
3. Код автоматически прочитает его

## ⚠️ БЕЗОПАСНОСТЬ

**ПЕРЕД КОММИТОМ В GIT:**

1. ✅ Убедитесь, что папка `API_KEY_TO_ENCRYPT_OR_REMOVE/` в `.gitignore`
2. ✅ Убедитесь, что файл `yandex_mapkit_api_key.txt` не коммитится
3. ⚠️ Удалите или зашифруйте API ключ перед публикацией
4. ⚠️ НЕ публикуйте API ключ в открытом доступе

## Проверка .gitignore

Выполните:
```bash
git check-ignore -v API_KEY_TO_ENCRYPT_OR_REMOVE/yandex_mapkit_api_key.txt
```

Если команда ничего не выводит - файл НЕ игнорируется, нужно добавить в `.gitignore`!

