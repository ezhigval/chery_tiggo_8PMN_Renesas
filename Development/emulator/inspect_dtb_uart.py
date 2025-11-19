#!/usr/bin/env python3
"""
Инспектор DTB для поиска UART/serial узлов.
Пробует распарсить dtb.img через dtc и вывести все serial@*/uart* узлы
с их base-адресами и совместимостью.
"""

import subprocess
import sys
from pathlib import Path


FDT_MAGIC_BE = b"\xd0\x0d\xfe\xed"  # big-endian 0xd00dfeed
DTBO_MAGIC_BE = b"\xd7\xb7\xab\x1e"  # big-endian 0xd7b7ab1e (Android DTBO)


def _run_dtc_on_blob(blob_path: Path) -> str | None:
    """Запустить dtc на конкретном DTB-блобе и вернуть текст DTS или None при ошибке."""
    dts_path = blob_path.with_suffix(".dts")
    try:
        subprocess.run(
            ["dtc", "-I", "dtb", "-O", "dts", "-o", str(dts_path), str(blob_path)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError:
        return None
    try:
        return dts_path.read_text(errors="ignore")
    except Exception:
        return None


def inspect_dtb(dtb_path: Path) -> int:
    if not dtb_path.exists():
        print(f"❌ DTB not found: {dtb_path}")
        return 1

    # Проверяем наличие dtc
    try:
        subprocess.run(["dtc", "-v"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("❌ dtc (device-tree-compiler) not found. Install via `brew install dtc` and retry.")
        return 1

    data = dtb_path.read_bytes()

    # Проверяем, не является ли это Android DTBO-образом (d7 b7 ab 1e)
    if data.startswith(DTBO_MAGIC_BE):
        print(f"✅ {dtb_path.name} looks like Android DTBO image (magic d7 b7 ab 1e)")
        return _inspect_dtbo_container(dtb_path, data)

    # Фоллбек: поиск "голых" FDT-блоков
    offsets: list[int] = []
    idx = 0
    while True:
        pos = data.find(FDT_MAGIC_BE, idx)
        if pos == -1:
            break
        offsets.append(pos)
        idx = pos + 4

    if not offsets:
        print("❌ No FDT magic (0xd00dfeed) found inside image — сложно вытащить UART без ручного анализа.")
        return 1

    print(f"✅ Found {len(offsets)} potential FDT blobs inside {dtb_path.name}: offsets {', '.join(hex(o) for o in offsets)}")

    total_found = 0
    for i, off in enumerate(offsets):
        blob_path = Path(f"/tmp/t18fl3_dtb_blob_{i}.dtb")
        blob_path.write_bytes(data[off:])
        dts = _run_dtc_on_blob(blob_path)
        if not dts:
            continue

        print(f"\n================ DTB #{i} (offset {hex(off)}) ================")
        lines = dts.splitlines()
        found_here = 0
        for j, line in enumerate(lines):
            if "serial@" in line or "uart" in line:
                start = max(0, j - 3)
                end = min(len(lines), j + 6)
                block = lines[start:end]
                print("\n---")
                for b in block:
                    print(b)
                found_here += 1
        if found_here == 0:
            print("  (no obvious serial@/uart nodes in this blob)")
        total_found += found_here

    if total_found == 0:
        print("\n⚠️ No UART/serial nodes found in any DTB blob.")
    else:
        print(f"\n✅ Total UART-related blocks across all blobs: {total_found}")

    return 0


def _inspect_dtbo_container(path: Path, data: bytes) -> int:
    """Разобрать Android DTBO-контейнер и вытащить все встроенные DTB/DTBO."""
    import struct

    # Формат заголовка dt_table_header из AOSP (big-endian):
    # u32 magic; u32 total_size; u32 header_size; u32 dt_entry_size;
    # u32 dt_entry_count; u32 dt_entries_offset; u32 page_size; u32 version;
    if len(data) < 32:
        print("❌ dtbo image too small to contain header")
        return 1

    magic, total_size, header_size, dt_entry_size, dt_entry_count, dt_entries_offset, page_size, version = struct.unpack(
        ">8I", data[:32]
    )

    print("DTBO header:")
    print(f"  magic          = 0x{magic:08x}")
    print(f"  total_size     = {total_size}")
    print(f"  header_size    = {header_size}")
    print(f"  dt_entry_size  = {dt_entry_size}")
    print(f"  dt_entry_count = {dt_entry_count}")
    print(f"  dt_entries_off = {dt_entries_offset}")
    print(f"  page_size      = {page_size}")
    print(f"  version        = {version}")

    if magic != int.from_bytes(DTBO_MAGIC_BE, "big"):
        print("❌ magic does not match DTBO, fallback to raw FDT search")
        return 1

    if dt_entry_size < 32:
        print("❌ dt_entry_size too small, unsupported format")
        return 1

    total_found = 0
    for idx in range(dt_entry_count):
        off = dt_entries_offset + idx * dt_entry_size
        if off + dt_entry_size > len(data):
            print(f"⚠️ entry {idx}: offset out of range, skipping")
            continue

        # Формат dt_table_entry (big-endian):
        # u32 dt_size; u32 dt_offset; u32 id; u32 rev; u32 flags; u32 custom[3]
        dt_size, dt_offset, entry_id, rev, flags, c1, c2, c3 = struct.unpack(">8I", data[off:off+32])
        print(f"\nEntry #{idx}: dt_size={dt_size}, dt_offset={dt_offset}, id={entry_id}, rev={rev}, flags=0x{flags:08x}")

        if dt_offset + dt_size > len(data):
            print("  ⚠️ dt_offset+dt_size out of range, skipping this entry")
            continue

        blob = data[dt_offset:dt_offset+dt_size]
        blob_path = Path(f"/tmp/t18fl3_dtbo_entry_{idx}.dtb")
        blob_path.write_bytes(blob)

        dts = _run_dtc_on_blob(blob_path)
        if not dts:
            print("  ⚠️ dtc failed on this entry")
            continue

        lines = dts.splitlines()
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
            print("  (no obvious serial@/uart nodes in this entry)")
        total_found += found_here

    if total_found == 0:
        print("\n⚠️ No UART/serial nodes found in any DTBO entry.")
    else:
        print(f"\n✅ Total UART-related blocks across DTBO entries: {total_found}")
    return 0


def main(argv: list[str]) -> int:
    # По умолчанию используем штатный dtb.img проекта
    if len(argv) >= 2:
        dtb = Path(argv[1])
    else:
        dtb = Path(__file__).resolve().parent.parent / "update_extracted" / "payload" / "dtb.img"
    return inspect_dtb(dtb)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))


