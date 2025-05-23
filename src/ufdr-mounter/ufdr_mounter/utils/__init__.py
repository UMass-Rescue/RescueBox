import platform

if platform.system() == "Windows":
    try:
        from .ufdr_mount_windows import UFDRMount
    except EnvironmentError:
        print(
            "Warning: Windows fuse mount not available. "
        )
else:
    try:
        from .ufdr_mount_unix import UFDRMount
    except EnvironmentError:
        print(
            "Warning: Unix fuse mount not available. "
        )