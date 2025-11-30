#!/usr/bin/env bash
#
# Подготовка кастомного QEMU с поддержкой машины g6sh.
#
# Что делает скрипт:
#   1. Клонирует официальные исходники QEMU в подкаталог qemu-src (если ещё не клонированы).
#   2. Чекаутит стабильную ветку v8.2.0.
#   3. Запускает ./configure и сборку aarch64-softmmu.
#   4. Создаёт симлинк qemu-system-aarch64 в текущей папке.
#
# ВАЖНО: саму машину g6sh (hw/arm/g6sh.c и правки в Kconfig/meson.build)
# нужно добавить в qemu-src вручную по докам:
#   Documentation/09_ЭМУЛЯТОР/Руководства/QEMU_CUSTOMIZATION_PLAN.md
#   Documentation/11_QNX/QEMU_UART_INTEGRATION.md
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

QEMU_DIR="${SCRIPT_DIR}/qemu-src"
BUILD_DIR="${SCRIPT_DIR}/build"

if [[ ! -d "${QEMU_DIR}" ]]; then
  echo "==> Клонирую QEMU в ${QEMU_DIR}..."
  git clone https://git.qemu.org/git/qemu.git "${QEMU_DIR}"
  cd "${QEMU_DIR}"
  git checkout v8.2.0
else
  echo "==> QEMU уже клонирован в ${QEMU_DIR}."
  cd "${QEMU_DIR}"
fi

# QEMU v8.x использует отдельный build-каталог внутри исходников.
# Если он уже существует и был создан НЕ через ./configure, конфигуратор падает
# с ошибкой: "build dir already exists and was not previously created by configure".
# Чтобы гарантировать чистую пересборку, всегда удаляем старый qemu-src/build.
if [[ -d "${QEMU_DIR}/build" ]]; then
  echo "==> Удаляю старый qemu-src/build перед конфигурацией..."
  rm -rf "${QEMU_DIR}/build"
fi

mkdir -p "${BUILD_DIR}"

echo "==> Конфигурирую сборку (aarch64-softmmu)..."
./configure --target-list=aarch64-softmmu --prefix="${BUILD_DIR}"

echo "==> Собираю QEMU..."
make -j"$(sysctl -n hw.ncpu)"

echo "==> Устанавливаю в ${BUILD_DIR} (optional)..."
make install

cd "${SCRIPT_DIR}"

BIN_SRC="${BUILD_DIR}/bin/qemu-system-aarch64"
if [[ -x "${BIN_SRC}" ]]; then
  ln -sf "${BIN_SRC}" "${SCRIPT_DIR}/qemu-system-aarch64"
  echo "==> Готово. Кастомный qemu-system-aarch64 доступен по пути:"
  echo "    ${SCRIPT_DIR}/qemu-system-aarch64"
else
  echo "!! Не найден бинарь ${BIN_SRC}. Проверь вывод сборки выше." >&2
fi


