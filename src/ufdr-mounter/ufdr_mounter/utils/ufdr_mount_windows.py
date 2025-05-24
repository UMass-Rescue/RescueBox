#!/usr/bin/env python3

import os
import sys
import zipfile
import logging
import signal
import errno
import time
import platform

from fuse import FUSE, FuseOSError, Operations, LoggingMixIn

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Dummy UID/GID for Windows

DEFAULT_UID = 1000
DEFAULT_GID = 1000


class UFDRMount(LoggingMixIn, Operations):

    def __init__(self, ufdr_path):
        super().__init__()
        self.ufdr_path = os.path.abspath(ufdr_path)
        if not os.path.isfile(self.ufdr_path):
            raise ValueError(f"UFDR file not found: {self.ufdr_path}")

        self.zip_offset = -1
        self.xml_data = b""
        self.files_info = {}
        self.dirs = set()
        self._parse_ufdr()

    def _parse_ufdr(self):

        log.info("Scanning UFDR file for embedded ZIP...")
        with open(self.ufdr_path, "rb") as f:
            head = f.read(16384)
            signature = b"PK\x03\x04"
            self.zip_offset = head.find(signature)
            if self.zip_offset < 0:
                raise RuntimeError("No ZIP signature found in UFDR file.")

            self.xml_data = head[: self.zip_offset]

            log.info(
                f"Found ZIP at offset {self.zip_offset}. Metadata size: {len(self.xml_data)}"
            )

            f.seek(self.zip_offset)

            with zipfile.ZipFile(f, "r") as z:
                all_items = z.infolist()
                self.dirs.add("/")
                for info in all_items:
                    if info.is_dir() or info.filename.endswith("/"):
                        self.dirs.add("/" + info.filename.rstrip("/"))

                    else:
                        path = "/" + info.filename

                        self.files_info[path] = {
                            "filename": info.filename,
                            "size": info.file_size,
                            "mtime": info.date_time,
                        }
                        self._ensure_parents(path)

                self.files_info["/metadata.xml"] = {
                    "filename": None,
                    "size": len(self.xml_data),
                    "mtime": (2023, 1, 1, 0, 0, 0),
                    "is_metadata": True,
                }

        log.info(
            f"Parsed {len(self.files_info)} files and {len(self.dirs)} directories in UFDR"
        )

    def _ensure_parents(self, path):
        parts = path.strip("/").split("/")
        cumulative = ""

        for part in parts[:-1]:
            cumulative += "/" + part
            self.dirs.add(cumulative)

    def getattr(self, path, fh=None):
        log.debug(f"getattr({path})")

        if path == "/" or path in self.dirs:
            return self._make_dir_stat()

        if path in self.files_info:
            size = self.files_info[path]["size"]
            return self._make_file_stat(size)

        raise FuseOSError(errno.ENOENT)

    def readdir(self, path, fh):
        log.debug(f"readdir({path})")
        entries = [".", ".."]

        prefix = path

        if not prefix.endswith("/"):
            prefix += "/"

        for d in self.dirs:
            if d.startswith(prefix) and d != path:
                suffix = d[len(prefix) :]
                if "/" not in suffix:
                    entries.append(suffix)

        for fpath in self.files_info:
            if fpath.startswith(prefix) and fpath != path:
                suffix = fpath[len(prefix) :]
                if "/" not in suffix:
                    entries.append(suffix)

        return sorted(set(entries))

    def read(self, path, size, offset, fh):
        log.debug(f"read({path}, size={size}, offset={offset})")

        if path in self.files_info and self.files_info[path].get("is_metadata"):
            return self.xml_data[offset : offset + size]

        if path in self.files_info and self.files_info[path]["filename"] is not None:
            return self._read_from_zip(path, size, offset)

        raise FuseOSError(errno.ENOENT)

    def _read_from_zip(self, path, size, offset):
        with open(self.ufdr_path, "rb") as f:
            f.seek(self.zip_offset)

            with zipfile.ZipFile(f, "r") as z:
                filename = self.files_info[path]["filename"]
                with z.open(filename) as zf:
                    if offset > 0:
                        zf.read(offset)
                    return zf.read(size)

    def open(self, path, flags):
        log.debug(f"open({path}, flags={flags})")
        if path not in self.files_info and path not in self.dirs:
            raise FuseOSError(errno.ENOENT)

        return 0

    @staticmethod
    def _make_file_stat(size):
        now = int(time.time())
        return {
            "st_mode": 0o100444,
            "st_size": size,
            "st_uid": DEFAULT_UID,
            "st_gid": DEFAULT_GID,
            "st_nlink": 1,
            "st_atime": now,
            "st_mtime": now,
            "st_ctime": now,
        }

    @staticmethod
    def _make_dir_stat():
        now = int(time.time())
        return {
            "st_mode": 0o040555,
            "st_size": 0,
            "st_uid": DEFAULT_UID,
            "st_gid": DEFAULT_GID,
            "st_nlink": 2,
            "st_atime": now,
            "st_mtime": now,
            "st_ctime": now,
        }


def handle_exit(signum, frame):
    print("\nReceived signal, exiting...")
    # Try to unmount if it's still running (best effort)
    if platform.system() == "Windows":
        print(
            "Unmount manually if needed (Windows does not support auto-unmount via signal)."
        )
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    if len(sys.argv) < 3:
        print("Usage: ufdr_mount_windows.py <ufdr_file> <mount_drive_letter>")
        sys.exit(1)

    ufdr_file = os.path.abspath(sys.argv[1])
    mount_point = sys.argv[2]

    if not os.path.isfile(ufdr_file):
        print(f"Error: UFDR file {ufdr_file} not found.")
        sys.exit(1)

    if not mount_point.endswith(":"):
        print("Error: Mount point must be a Windows drive letter (e.g., 'M:').")
        sys.exit(1)

    print(f"Mounting {ufdr_file} to {mount_point}")
    print("Press Ctrl+C to unmount and exit.")

    FUSE(UFDRMount(ufdr_file), mount_point, foreground=True, ro=True, allow_other=False)


if __name__ == "__main__":
    main()
