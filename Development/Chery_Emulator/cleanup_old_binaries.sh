#!/bin/bash
# Скрипт для очистки старых бинарников QEMU при пересборке

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QEMU_DIR="${PROJECT_DIR}/qemu_g6sh"

echo "🧹 Очистка старых бинарников QEMU..."

# Удаляем старые бинарники из build/bin (если есть)
if [ -d "${QEMU_DIR}/build/bin" ]; then
    find "${QEMU_DIR}/build/bin" -name "qemu-system-aarch64*" -type f -delete
    echo "✅ Удалены старые бинарники из build/bin"
fi

# Удаляем промежуточный файл сборки (если есть)
if [ -f "${QEMU_DIR}/qemu-src/build/qemu-system-aarch64-unsigned" ]; then
    rm -f "${QEMU_DIR}/qemu-src/build/qemu-system-aarch64-unsigned"
    echo "✅ Удален промежуточный файл qemu-system-aarch64-unsigned"
fi

# Удаляем временные файлы из /tmp
rm -f /tmp/qemu_kernel_* /tmp/qemu_kernel_decompressed_* 2>/dev/null || true
echo "✅ Очищены временные файлы из /tmp"

echo "✅ Очистка завершена"

