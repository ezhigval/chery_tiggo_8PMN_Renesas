"""
Extract kernel from boot.img for loading at correct address in QEMU.

This module extracts the kernel from boot.img without modifying the original image.
The kernel is then loaded directly by QEMU at the address specified in boot.img header.
Supports decompression of LZ4 compressed kernels.
"""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path
from typing import Optional


def extract_kernel_from_bootimg(boot_img_path: Path, output_kernel_path: Optional[Path] = None) -> Path:
    """
    Extract kernel from Android boot.img format.

    Android boot.img format:
    - Header: 1632 bytes (Android bootimg v2/v3)
    - Kernel: at page_size offset
    - Ramdisk: at page_size + kernel_size (aligned to page_size)
    - Second stage: (optional)
    - Device tree: (optional)

    Returns path to extracted kernel file.
    """
    if not boot_img_path.exists():
        raise FileNotFoundError(f"boot.img not found: {boot_img_path}")

    with boot_img_path.open("rb") as f:
        # Read header (first 1632 bytes)
        header = f.read(1632)

        if len(header) < 1632:
            raise ValueError(f"boot.img too small or invalid header: {len(header)} bytes")

        # Parse header fields (all little-endian)
        # Offsets according to Android bootimg.h
        page_size = struct.unpack('<I', header[36:40])[0]  # offset 36: page_size
        kernel_size = struct.unpack('<I', header[8:12])[0]   # offset 8: kernel_size
        kernel_addr = struct.unpack('<I', header[12:16])[0]  # offset 12: kernel_addr
        ramdisk_size = struct.unpack('<I', header[16:20])[0] # offset 16: ramdisk_size
        ramdisk_addr = struct.unpack('<I', header[20:24])[0] # offset 20: ramdisk_addr

        # Validate
        if page_size == 0 or page_size % 2048 != 0:
            raise ValueError(f"Invalid page_size: {page_size}")

        if kernel_size == 0:
            raise ValueError("kernel_size is zero")

        # Seek to kernel start (after header, aligned to page_size)
        kernel_offset = page_size
        f.seek(kernel_offset)

        # Read kernel
        kernel_data = f.read(kernel_size)

        if len(kernel_data) < kernel_size:
            raise ValueError(f"Could not read full kernel: got {len(kernel_data)}, expected {kernel_size}")

    # Determine output path
    if output_kernel_path is None:
        output_kernel_path = boot_img_path.parent / f"{boot_img_path.stem}_kernel"

    # Write extracted kernel
    output_kernel_path.parent.mkdir(parents=True, exist_ok=True)
    with output_kernel_path.open("wb") as out:
        out.write(kernel_data)

    # Check if kernel is compressed (LZ4) and decompress if needed
    decompressed_kernel_path = None
    is_compressed = False
    try:
        # Check for LZ4 magic - magic number is 0x184D2204
        # In bytes: 04 22 4D 18 (little-endian as stored in file)
        lz4_magic_le = b'\x04\x22\x4d\x18'  # 0x184D2204 in little-endian
        if len(kernel_data) >= 4 and kernel_data[:4] == lz4_magic_le:
            is_compressed = True
            # Kernel is LZ4 compressed, decompress it
            decompressed_kernel_path = output_kernel_path.parent / f"{output_kernel_path.stem}_decompressed"
            decompress_lz4(output_kernel_path, decompressed_kernel_path)
            final_kernel_path = decompressed_kernel_path
        else:
            final_kernel_path = output_kernel_path
    except Exception as e:
        # If decompression fails, log but continue with original kernel
        import logging
        logging.warning(f"Failed to decompress LZ4 kernel: {e}, using compressed kernel")
        final_kernel_path = output_kernel_path

    # Return kernel info
    kernel_info = {
        "kernel_path": str(final_kernel_path),
        "kernel_size": kernel_size,
        "kernel_addr": hex(kernel_addr),
        "page_size": page_size,
        "ramdisk_size": ramdisk_size,
        "ramdisk_addr": hex(ramdisk_addr),
        "compressed": is_compressed,
    }

    return final_kernel_path, kernel_info


def decompress_lz4(input_path: Path, output_path: Path) -> None:
    """
    Decompress LZ4 compressed kernel using system lz4 command.

    Falls back to Python lz4 library if available, or raises exception.
    """
    # Try system lz4 command first
    try:
        result = subprocess.run(
            ["lz4", "-dc", str(input_path), str(output_path)],
            capture_output=True,
            check=True,
            timeout=60
        )
        return
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try Python lz4 library
    try:
        import lz4.frame
        with input_path.open("rb") as inf, output_path.open("wb") as outf:
            decompressed = lz4.frame.decompress(inf.read())
            outf.write(decompressed)
        return
    except ImportError:
        pass

    raise RuntimeError(
        "Cannot decompress LZ4 kernel: neither 'lz4' command nor 'lz4' Python package found. "
        "Install with: brew install lz4  # or: pip install lz4"
    )


def extract_kernel_if_needed(boot_img_path: Path, cache_dir: Optional[Path] = None) -> tuple[Path, dict]:
    """
    Extract kernel from boot.img, using cache if available.

    Returns (kernel_path, kernel_info_dict).
    """
    if cache_dir is None:
        cache_dir = boot_img_path.parent / "extracted"

    cache_dir.mkdir(parents=True, exist_ok=True)
    kernel_path = cache_dir / "kernel"

    # Check if already extracted
    if kernel_path.exists():
        # Read info if available
        info_path = cache_dir / "kernel_info.txt"
        if info_path.exists():
            info = {}
            with info_path.open("r") as f:
                for line in f:
                    if ":" in line:
                        key, value = line.strip().split(":", 1)
                        info[key.strip()] = value.strip()

            # Verify it's still valid (check boot.img mtime)
            if boot_img_path.stat().st_mtime <= kernel_path.stat().st_mtime:
                return kernel_path, info

    # Extract kernel
    kernel_path, kernel_info = extract_kernel_from_bootimg(boot_img_path, kernel_path)

    # Save info
    info_path = cache_dir / "kernel_info.txt"
    with info_path.open("w") as f:
        for key, value in kernel_info.items():
            f.write(f"{key}: {value}\n")

    return kernel_path, kernel_info

