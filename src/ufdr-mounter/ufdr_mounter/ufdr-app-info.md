# UFDR-Mounter

A Python-based FUSE virtual filesystem that allows you to mount `.ufdr` and `.zip` archives as read-only directories. This tool lets you browse the contents of forensic archives (like Cellebrite UFDR exports) without extracting them.

Made for integration with RescueBox (UMass Amherst · Spring 2025).


# UFDR

A `.ufdr` file is a Cellebrite forensic export that combines an XML metadata blob and a ZIP archive of file contents. This project allows you to mount The ZIP portion as a virtual file structure.


### OS-Specific Notes

#### Windows 

Requires Windows File System Proxy setup - [WinFsp (FUSE-compatible)](https://github.com/winfsp/winfsp/releases)
This is auto  Downloaded (Release 2.0 is recommended) and installed . 

If  manual install, it is mandatory to select the `Developer` feature in the Custom Setup wizard.

Note: the rescuebox plugin will mount a drive letter .

## Usage

### Using the Frontend (RescueBox)

1. Open the RescueBox model interface and run the UFDR Mount Service
2. Specify the mount point:
   - **Windows**:  
     Enter a valid **drive letter** (e.g., `M:` or `R:`) as the mount point.

Note:  When you exit the RescueBox desktop the path will be un-mounted. Unmount task is not supported in this version.



