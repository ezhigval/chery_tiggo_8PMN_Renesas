#!/usr/bin/env python3
"""
Небольшой оффлайн‑валидатор boot.img для T18FL3.
Читает заголовок Android Boot Image и выводит все ключевые поля,
чтобы можно было сравнить с тем, что мы используем в эмуляторе.
"""

import sys
import struct
from pathlib import Path


def inspect_boot_image(path: Path) -> int:
    if not path.exists():
        print(f"❌ boot.img not found: {path}")
        return 1

    with path.open("rb") as f:
        header = f.read(1632)

    if header[:8] != b"ANDROID!":
        print("❌ Invalid magic, this is not an Android boot image (no ANDROID!)")
        return 1

    kernel_size = struct.unpack("<I", header[8:12])[0]
    kernel_addr = struct.unpack("<I", header[12:16])[0]
    ramdisk_size = struct.unpack("<I", header[16:20])[0]
    ramdisk_addr = struct.unpack("<I", header[20:24])[0]
    second_size = struct.unpack("<I", header[24:28])[0]
    second_addr = struct.unpack("<I", header[28:32])[0]
    tags_addr = struct.unpack("<I", header[32:36])[0]
    page_size = struct.unpack("<I", header[36:40])[0]
    name = header[48:64].rstrip(b"\x00").decode(errors="ignore")
    cmdline = header[64:64+512].rstrip(b"\x00").decode(errors="ignore")

    print("✅ ANDROID boot image header:")
    print(f"  kernel_size : {kernel_size} bytes")
    print(f"  kernel_addr : 0x{kernel_addr:08x}")
    print(f"  ramdisk_size: {ramdisk_size} bytes")
    print(f"  ramdisk_addr: 0x{ramdisk_addr:08x}")
    print(f"  second_size : {second_size} bytes")
    print(f"  second_addr : 0x{second_addr:08x}")
    print(f"  tags_addr   : 0x{tags_addr:08x}")
    print(f"  page_size   : {page_size} bytes")
    print(f"  name        : '{name}'")
    print(f"  cmdline     : '{cmdline}'")

    # Вычисляем смещения так же, как в QEMUManager._extract_boot_components
    kernel_offset = page_size
    ramdisk_offset = kernel_offset + ((kernel_size + page_size - 1) // page_size) * page_size

    print()
    print("  Calculated offsets:")
    print(f"    kernel_offset : {kernel_offset} (0x{kernel_offset:x})")
    print(f"    ramdisk_offset: {ramdisk_offset} (0x{ramdisk_offset:x})")

    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("Usage: inspect_boot_image.py /path/to/boot.img")
        return 1

    return inspect_boot_image(Path(argv[1]))


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


