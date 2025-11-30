# CAN Bridge для macOS

Этот Docker контейнер позволяет использовать Linux socketcan на macOS через Docker.

## Проблема

Socketcan - это Linux-специфичная технология, недоступная на macOS. QEMU использует `can-host-socketcan`, который требует Linux socketcan интерфейс (vcan0).

## Решение

Docker контейнер с Linux, где работает socketcan и создается vcan0 интерфейс. CAN bridge сервис пересылает CAN фреймы из TCP (macOS) в socketcan (контейнер).

## Использование

### 1. Запуск контейнера

```bash
cd Development/Chery_Emulator/docker/can-bridge
./start.sh
```

Или вручную:

```bash
docker-compose up -d --build
```

### 2. Проверка vcan0

```bash
docker exec chery-can-bridge ip link show vcan0
```

Должно показать:
```
3: vcan0: <NOARP,UP,LOWER_UP> mtu 72 qdisc noqueue state UNKNOWN
```

### 3. Использование в эмуляторе

После запуска контейнера:

1. **CAN bridge работает** в контейнере и слушает TCP порт 1238
2. **CAN server на хосте** подключается к контейнеру через TCP (localhost:1238)
3. **QEMU** использует `can-host-socketcan` с vcan0 (через host network mode)

### 4. Проверка работы

```bash
# Логи контейнера
docker logs chery-can-bridge

# Проверка подключения
docker exec chery-can-bridge netstat -tuln | grep 1238
```

### 5. Остановка

```bash
docker-compose down
```

## Архитектура

```
macOS Host                    Docker Container (Linux)
┌─────────────────┐          ┌─────────────────────────┐
│  CAN Server     │  TCP    │  CAN Bridge             │
│  (Python)       │─────────>│  (Python)               │
│  Port 1238      │         │  Port 1238               │
└─────────────────┘         │                         │
                             │  ┌───────────────────┐ │
                             │  │  vcan0            │ │
                             │  │  (socketcan)      │ │
                             │  └───────────────────┘ │
                             └─────────────────────────┘
                                      │
                                      │ socketcan
                                      ▼
                             ┌───────────────────┐
                             │  QEMU             │
                             │  can-host-socketcan│
                             └───────────────────┘
```

## Требования

- Docker Desktop для macOS
- Привилегированный доступ для создания сетевых интерфейсов

## Примечания

- Контейнер использует `network_mode: host` для доступа к vcan0
- Контейнер требует `privileged: true` для создания vcan интерфейса
- vcan0 доступен только внутри контейнера, но QEMU может подключиться через host network

