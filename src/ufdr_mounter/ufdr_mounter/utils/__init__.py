import platform

if platform.system() == "Windows":
    from .ufdr_mount_windows import UFDRMount
else:
    from .ufdr_mount_unix import UFDRMount
