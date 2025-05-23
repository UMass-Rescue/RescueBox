import platform

if platform.system() == "Windows":
    try:
        from .ufdr_mount_windows import UFDRMount # type: ignore
    except EnvironmentError:
        print(
            "Warning: Windows fuse mount not available. "
        )
