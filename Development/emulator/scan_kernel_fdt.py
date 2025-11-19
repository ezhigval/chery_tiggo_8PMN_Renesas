#!/usr/bin/env python3
"""
Поиск встроенных DTB (Device Tree Blob) внутри kernel из boot.img.

Идея:
 1. Разобрать boot.img как Android boot image (как в QEMUManager._extract_boot_components).
 2. Вытащить kernel (и при возможности распаковать LZ4).
 3. Просканировать kernel на FDT magic (0xd00dfeed), вырезать каждый DTB по полю totalsize.
 4. Для каждого найденного DTB запустить dtc и вывести все serial@/uart-узлы.
"""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path
import tempfile


FDT_MAGIC_BE = b"\xd0\x0d\xfe\xed"  # big-endian 0xd00dfeed


def extract_kernel_from_boot(boot_img: Path) -> Path | None:
    """Извлечь kernel (в распакованном виде, если это LZ4) из boot.img в /tmp и вернуть путь."""
    if not boot_img.exists():
        print(f"❌ boot.img not found: {boot_img}")
        return None

    data = boot_img.read_bytes()
    if data[:8] != b"ANDROID!":
        print("❌ Invalid boot image: missing ANDROID! magic")
        return None

    # Поля стандартного Android boot header v1
    kernel_size = struct.unpack("<I", data[8:12])[0]
    ramdisk_size = struct.unpack("<I", data[16:20])[0]
    page_size = struct.unpack("<I", data[36:40])[0]

    print(f"boot.img header:")
    print(f"  kernel_size = {kernel_size}")
    print(f"  ramdisk_size = {ramdisk_size}")
    print(f"  page_size = {page_size}")

    kernel_offset = page_size
    ramdisk_offset = kernel_offset + ((kernel_size + page_size - 1) // page_size) * page_size

    print(f"  kernel_offset = 0x{kernel_offset:x}")
    print(f"  ramdisk_offset = 0x{ramdisk_offset:x}")

    kernel_data = data[kernel_offset:kernel_offset + kernel_size]
    if len(kernel_data) != kernel_size:
        print(f"❌ Failed to read kernel data: expected {kernel_size}, got {len(kernel_data)}")
        return None

    tmp_dir = Path(tempfile.gettempdir()) / "t18fl3_kernel_scan"
    tmp_dir.mkdir(exist_ok=True)

    kernel_path = tmp_dir / "kernel"
    kernel_unpacked = tmp_dir / "kernel_unpacked"

    # Пишем сырой kernel
    kernel_path.write_bytes(kernel_data)
    print(f"✅ Raw kernel written to {kernel_path}")

    # Пробуем распаковать LZ4 (как в QEMUManager)
    try:
        # lz4 распакует kernel в kernel_unpacked (или упадёт, тогда будем использовать сырой)
        print("→ Trying to decompress kernel with lz4...")
        result = subprocess.run(
            ["lz4", "-d", "-f", str(kernel_path), str(kernel_unpacked)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if kernel_unpacked.exists() and kernel_unpacked.stat().st_size > 1_000_000:
            print(
                f"✅ Kernel decompressed with lz4: {kernel_unpacked.stat().st_size} bytes "
                f"(compressed: {kernel_size})"
            )
            return kernel_unpacked
        else:
            print(
                "⚠️ lz4 did not produce a large enough file, falling back to raw kernel "
                f"(lz4 rc={result.returncode})"
            )
    except Exception as e:
        print(f"⚠️ lz4 failed: {e}; using raw kernel")

    return kernel_path


def scan_kernel_for_fdt(kernel_path: Path) -> int:
    """Просканировать kernel на наличие FDT-блоков и вывести UART/serial узлы."""
    data = kernel_path.read_bytes()
    print(f"\nScanning {kernel_path} ({len(data)} bytes) for FDT magic...")

    offsets: list[int] = []
    idx = 0
    while True:
        pos = data.find(FDT_MAGIC_BE, idx)
        if pos == -1:
            break
        offsets.append(pos)
        idx = pos + 4

    if not offsets:
        print("❌ No FDT magic (0xd00dfeed) found in kernel.")
        return 1

    print(f"✅ Found {len(offsets)} potential FDT blobs at offsets: {', '.join(hex(o) for o in offsets)}")

    # Проверяем наличие dtc
    try:
        subprocess.run(
            ["dtc", "-v"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        print("❌ dtc not found. Install via `brew install dtc` and retry.")
        return 1

    tmp_dir = kernel_path.parent
    total_uart_blocks = 0

    for i, off in enumerate(offsets):
        if off + 8 > len(data):
            continue

        # totalsize лежит сразу после magic, big-endian u32
        _, totalsize = struct.unpack(">II", data[off:off + 8])
        if totalsize <= 0 or off + totalsize > len(data):
            print(f"⚠️ FDT #{i}: suspicious totalsize={totalsize}, clipping to end of file")
            totalsize = len(data) - off

        blob = data[off:off + totalsize]
        dtb_path = tmp_dir / f"kernel_fdt_{i}.dtb"
        dts_path = tmp_dir / f"kernel_fdt_{i}.dts"
        dtb_path.write_bytes(blob)
        print(f"\nDTB #{i}: offset=0x{off:x}, totalsize={totalsize} → {dtb_path}")

        # Декомпилируем в DTS
        try:
            subprocess.run(
                ["dtc", "-I", "dtb", "-O", "dts", "-o", str(dts_path), str(dtb_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            print(f"  ❌ dtc failed on {dtb_path.name}: {e}")
            continue

        text = dts_path.read_text(errors="ignore")
        lines = text.splitlines()
        found_here = 0
        for j, line in enumerate(lines):
            if "serial@" in line or "uart" in line:
                start = max(0, j - 3)
                end = min(len(lines), j + 6)
                block = lines[start:end]
                print("\n--- UART candidate ---")
                for b in block:
                    print(b)
                found_here += 1
        if found_here == 0:
            print("  (no obvious serial@/uart nodes in this DTB)")
        total_uart_blocks += found_here

    if total_uart_blocks == 0:
        print("\n⚠️ No UART/serial nodes found in any embedded DTB.")
    else:
        print(f"\n✅ Total UART-related blocks across embedded DTBs: {total_uart_blocks}")

    return 0


def main() -> int:
    boot_img = Path("/Users/valentinezov/Projects/Tiggo/update_extracted/payload/boot.img")
    kernel = extract_kernel_from_boot(boot_img)
    if not kernel:
        return 1
    return scan_kernel_for_fdt(kernel)


if __name__ == "__main__":
    raise SystemExit(main())


