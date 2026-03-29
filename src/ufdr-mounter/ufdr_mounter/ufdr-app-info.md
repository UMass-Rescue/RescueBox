# UFDR-Mounter

A Python-based FUSE virtual filesystem that allows you to mount `.ufdr` and `.zip` archives as read-only directories. This tool lets you browse the contents of forensic archives (like Cellebrite UFDR exports) without extracting them.

Made for integration with RescueBox (UMass Amherst · Spring 2025).


# UFDR

A `.ufdr` file is a Cellebrite forensic export that combines an XML metadata blob and a ZIP archive of file contents. This project allows you to mount The ZIP portion as a virtual file structure.


### OS-Specific Notes

#### Linux 
Install FUSE via your package manager:

```bash
sudo apt update && sudo apt install fuse
```
If needed, also allow non-root FUSE mounts (depending on distro):
```bash
sudo usermod -a -G fuse $(whoami)
```

Then log out and log back in to apply group changes.


## Usage

### Using the Frontend (RescueBox)

1. Open the RescueBox model interface and run the UFDR Mount Service
2. Specify the mount point:
   - **Linux**:
     Specify the mount point:
        Use an absolute path (e.g., /mnt/test1)
        or a short name like test1 (which will be mounted inside the repo's mnt/ folder)

Note:   **Unmount task is not supported in this version**, suggest manually unmount.
On windows when you exit the RescueBox desktop the path will be un-mounted.


