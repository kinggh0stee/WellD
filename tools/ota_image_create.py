#!/usr/bin/env python3
"""Pack an ESP-IDF app image into a Zigbee OTA upgrade file (.zigbee).

File layout (ZCL spec 07-5123, section 11.4) - byte-for-byte the same as
esp-zigbee-sdk's tools/image_builder_tool/image_builder_tool.py, which
esp-zigbee-lib's OTA client expects and the firmware's parser
(welld_ota_parser_* in components/welld_core) consumes:

    OTA header, little-endian:
        u32 file identifier 0x0BEEF11E   u16 header version 0x0100
        u16 header length                u16 field control
        u16 manufacturer code            u16 image type
        u32 file version                 u16 Zigbee stack version
        32s header string                u32 total file size
        [u16 min HW version, u16 max HW version]   (field control bit 2)
    one sub-element:
        u16 tag 0x0000 (Upgrade Image)   u32 length   <app image bytes>

The device only installs a file whose manufacturer code and image type match
OTA_MANUFACTURER_CODE / OTA_IMAGE_TYPE in components/zigbee/zigbee.c and whose
file version is newer than the running OTA_FW_VERSION (0xMMmmPP00 derived from
PROJECT_VER in the root CMakeLists.txt).

Usage:
    python tools/ota_image_create.py --manufacturer-code 0x1234 \\
        --image-type 0x0001 --file-version 0x01020000 \\
        --output build/welld.ota.zigbee build/welld.bin
"""

import argparse
import struct
import sys

OTA_FILE_IDENTIFIER = 0x0BEEF11E
OTA_HEADER_VERSION = 0x0100
TAG_UPGRADE_IMAGE = 0x0000
ESP_IMAGE_MAGIC = 0xE9
FC_HW_VERSION_PRESENT = 0x0004


def build_ota_file(image, manufacturer_code, image_type, file_version,
                   stack_version=0x0002, header_string="",
                   min_hw_ver=None, max_hw_ver=None):
    """Return the complete .zigbee file as bytes."""
    header_str = header_string.encode("ascii")
    if len(header_str) > 32:
        raise ValueError("header string is limited to 32 ASCII bytes")

    field_control = 0
    optional = b""
    if min_hw_ver is not None or max_hw_ver is not None:
        if min_hw_ver is None or max_hw_ver is None:
            raise ValueError("--min-hw-ver and --max-hw-ver must be given together")
        field_control |= FC_HW_VERSION_PRESENT
        optional = struct.pack("<HH", min_hw_ver, max_hw_ver)

    element = struct.pack("<HI", TAG_UPGRADE_IMAGE, len(image)) + image
    header_len = struct.calcsize("<IHHHHHIH32sI") + len(optional)
    total_len = header_len + len(element)

    header = struct.pack(
        "<IHHHHHIH32sI",
        OTA_FILE_IDENTIFIER,
        OTA_HEADER_VERSION,
        header_len,
        field_control,
        manufacturer_code,
        image_type,
        file_version,
        stack_version,
        header_str.ljust(32, b"\x00"),
        total_len,
    )
    return header + optional + element


def u16(text):
    value = int(text, 0)
    if not 0 <= value <= 0xFFFF:
        raise argparse.ArgumentTypeError(f"{text} does not fit in 16 bits")
    return value


def u32(text):
    value = int(text, 0)
    if not 0 <= value <= 0xFFFFFFFF:
        raise argparse.ArgumentTypeError(f"{text} does not fit in 32 bits")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--manufacturer-code", type=u16, required=True)
    parser.add_argument("--image-type", type=u16, required=True)
    parser.add_argument("--file-version", type=u32, required=True,
                        help="0xMMmmPP00, derived from PROJECT_VER")
    parser.add_argument("--stack-version", type=u16, default=0x0002)
    parser.add_argument("--header-string", default="WellD")
    parser.add_argument("--min-hw-ver", type=u16)
    parser.add_argument("--max-hw-ver", type=u16)
    parser.add_argument("--output", required=True, help="output .zigbee path")
    parser.add_argument("image", help="ESP-IDF app binary, e.g. build/welld.bin")
    args = parser.parse_args(argv)

    with open(args.image, "rb") as f:
        image = f.read()
    if not image or image[0] != ESP_IMAGE_MAGIC:
        sys.exit(f"error: {args.image} is not an ESP app image "
                 f"(first byte must be 0x{ESP_IMAGE_MAGIC:02X})")

    data = build_ota_file(image, args.manufacturer_code, args.image_type,
                          args.file_version, args.stack_version,
                          args.header_string, args.min_hw_ver, args.max_hw_ver)
    with open(args.output, "wb") as f:
        f.write(data)
    print(f"{args.output}: {len(data)} bytes (image {len(image)} bytes, "
          f"manufacturer 0x{args.manufacturer_code:04X}, "
          f"type 0x{args.image_type:04X}, version 0x{args.file_version:08X})")


if __name__ == "__main__":
    main()
