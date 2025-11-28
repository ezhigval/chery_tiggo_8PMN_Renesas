#!/usr/bin/env bash
#
# Подготовка отдельного форка QEMU с поддержкой g6sh + SCIF0 для QNX.
#
# Скрипт НИЧЕГО не трогает в существующем qemu_g6sh и образах.
#

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QEMU_DIR="${ROOT_DIR}/qemu-src"
BUILD_DIR="${ROOT_DIR}/build"

echo "==> SCIF QEMU fork setup"
echo "Root:      ${ROOT_DIR}"
echo "QEMU src:  ${QEMU_DIR}"
echo "Build dir: ${BUILD_DIR}"
echo

if [[ ! -d "${QEMU_DIR}" ]]; then
  echo "==> Cloning upstream QEMU into qemu-src..."
  git clone https://git.qemu.org/git/qemu.git "${QEMU_DIR}"
  cd "${QEMU_DIR}"
  git checkout v8.2.0
else
  echo "==> Using existing QEMU sources at ${QEMU_DIR}"
  cd "${QEMU_DIR}"
fi

mkdir -p "${BUILD_DIR}"

echo "==> Configuring aarch64-softmmu build..."
./configure --target-list=aarch64-softmmu --prefix="${BUILD_DIR}"

echo "==> Building QEMU (this may take a while)..."
if command -v ninja >/dev/null 2>&1; then
  ninja -C build
else
  make -j"$(sysctl -n hw.ncpu)"
fi

echo "==> (Optional) Installing into ${BUILD_DIR}..."
make install || echo "install step failed or skipped; binaries still available in build/"

if [[ -x "${BUILD_DIR}/bin/qemu-system-aarch64" ]]; then
  ln -sf "${BUILD_DIR}/bin/qemu-system-aarch64" "${ROOT_DIR}/qemu-system-aarch64"
  echo "==> Fork binary ready:"
  echo "    ${ROOT_DIR}/qemu-system-aarch64"
else
  echo "!! qemu-system-aarch64 not found under ${BUILD_DIR}/bin" >&2
fi


