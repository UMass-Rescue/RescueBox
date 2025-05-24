import platform

if platform.system() == "Windows":
    from .ufdr_mount_windows import UFDRMount  # noqa: F401
else:
    from .ufdr_mount_unix import UFDRMount  # noqa: F401
