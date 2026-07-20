//! Detect NVIDIA CUDA toolkit and cuDNN bin dirs for the backend (``dll_paths.py``).

use std::fs;
use std::path::{Path, PathBuf};

pub struct BackendGpuDllPaths {
    pub cuda_bin: Option<String>,
    pub cudnn_bin: Option<String>,
    toolkit_cuda_version: String,
}

impl BackendGpuDllPaths {
    pub fn detect() -> Self {
        let cuda_bin = cuda_bin_for_backend();
        let cudnn_bin = cudnn_bin_for_backend();
        let toolkit_cuda_version = toolkit_cuda_version_label();
        Self {
            cuda_bin,
            cudnn_bin,
            toolkit_cuda_version,
        }
    }

    pub fn startup_log_line(&self) -> String {
        format!(
            "GPU DLL paths for backend (toolkit CUDA {}): CUDA bin={}; cuDNN bin={}",
            self.toolkit_cuda_version,
            self.cuda_bin.as_deref().unwrap_or("not found"),
            self.cudnn_bin.as_deref().unwrap_or("not found"),
        )
    }

    /// Prepend CUDA/cuDNN bins to ``PATH`` (ONNX Runtime loads cuDNN via PATH, not only ``add_dll_directory``).
    pub fn prepend_path_env(&self) -> Option<String> {
        let mut front: Vec<&str> = Vec::new();
        if let Some(ref p) = self.cudnn_bin {
            front.push(p.as_str());
        }
        if let Some(ref p) = self.cuda_bin {
            front.push(p.as_str());
        }
        if front.is_empty() {
            return None;
        }
        let existing = std::env::var("PATH").unwrap_or_default();
        Some(format!("{};{}", front.join(";"), existing))
    }
}

fn toolkit_cuda_version_label() -> String {
    #[cfg(windows)]
    {
        let cuda_override = std::env::var("RESCUEBOX_CUDA_BIN")
            .ok()
            .map(|s| PathBuf::from(s.trim()))
            .filter(|p| !p.as_os_str().is_empty());
        return toolkit_version_for_cudnn(cuda_override.as_deref())
            .map(|(m, n)| format!("{m}.{n}"))
            .unwrap_or_else(|| "unknown".to_string());
    }
    #[cfg(not(windows))]
    "unknown".to_string()
}

/// ``RESCUEBOX_CUDA_BIN`` for backend ``dll_paths.py`` (ONNX CUDA runtime).
fn cuda_bin_for_backend() -> Option<String> {
    if let Ok(path) = std::env::var("RESCUEBOX_CUDA_BIN") {
        let path = path.trim();
        if !path.is_empty() {
            return Some(path.to_string());
        }
    }
    #[cfg(windows)]
    {
        return detect_cuda_bin_windows().map(|p| p.to_string_lossy().into_owned());
    }
    #[cfg(not(windows))]
    None
}

/// ``RESCUEBOX_CUDNN_BIN`` for backend ``dll_paths.py`` (ONNX CUDA/cuDNN).
fn cudnn_bin_for_backend() -> Option<String> {
    if let Ok(path) = std::env::var("RESCUEBOX_CUDNN_BIN") {
        let path = path.trim();
        if !path.is_empty() {
            return Some(path.to_string());
        }
    }
    #[cfg(windows)]
    {
        let cuda_override = std::env::var("RESCUEBOX_CUDA_BIN")
            .ok()
            .map(|s| PathBuf::from(s.trim()))
            .filter(|p| !p.as_os_str().is_empty());
        let toolkit_ver = toolkit_version_for_cudnn(cuda_override.as_deref());
        return detect_cudnn_bin_windows(toolkit_ver).map(|p| p.to_string_lossy().into_owned());
    }
    #[cfg(not(windows))]
    None
}

#[cfg(windows)]
const CUDNN_INSTALL_ROOT: &str = r"C:\Program Files\NVIDIA\CUDNN";

#[cfg(windows)]
const CUDA_TOOLKIT_ROOT: &str = r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA";

#[cfg(windows)]
fn is_cudnn_x64_bin(dir: &Path) -> bool {
    if !dir.is_dir() {
        return false;
    }
    let Ok(entries) = fs::read_dir(dir) else {
        return false;
    };
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().to_lowercase();
        if name.starts_with("cudnn") && name.ends_with(".dll") {
            return true;
        }
    }
    false
}

#[cfg(windows)]
fn parse_dot_version(name: &str) -> Option<(u32, u32)> {
    let mut parts = name.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next().unwrap_or("0").parse().ok()?;
    Some((major, minor))
}

#[cfg(windows)]
fn pick_cudnn_cuda_bin(
    cuda_bins: &[(PathBuf, (u32, u32))],
    toolkit_ver: Option<(u32, u32)>,
) -> Option<PathBuf> {
    if cuda_bins.is_empty() {
        return None;
    }
    let Some((major, minor)) = toolkit_ver else {
        let mut sorted = cuda_bins.to_vec();
        sorted.sort_by(|a, b| b.1.cmp(&a.1));
        return Some(sorted[0].0.clone());
    };
    let mut candidates: Vec<&(PathBuf, (u32, u32))> = cuda_bins
        .iter()
        .filter(|(_, ver)| ver.0 == major)
        .collect();
    if candidates.is_empty() {
        return None;
    }
    candidates.sort_by(|a, b| {
        let da = a.1.1.abs_diff(minor);
        let db = b.1.1.abs_diff(minor);
        da.cmp(&db).then_with(|| b.1.cmp(&a.1))
    });
    Some(candidates[0].0.clone())
}

#[cfg(windows)]
fn cuda_version_from_bin(bin_dir: &Path) -> Option<(u32, u32)> {
    bin_dir
        .parent()
        .and_then(|p| p.file_name())
        .and_then(|n| n.to_str())
        .and_then(|name| name.strip_prefix('v'))
        .and_then(parse_dot_version)
}

#[cfg(windows)]
fn detect_cudnn_bin_windows(toolkit_ver: Option<(u32, u32)>) -> Option<PathBuf> {
    let root = PathBuf::from(CUDNN_INSTALL_ROOT);
    if !root.is_dir() {
        return None;
    }
    let mut cudnn_versions: Vec<(PathBuf, (u32, u32))> = Vec::new();
    for entry in fs::read_dir(&root).ok()?.flatten() {
        if !entry.file_type().ok()?.is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().into_owned();
        let Some(ver) = name.strip_prefix('v').and_then(parse_dot_version) else {
            continue;
        };
        cudnn_versions.push((entry.path(), ver));
    }
    cudnn_versions.sort_by(|a, b| b.1.cmp(&a.1));

    for (ver_dir, _) in cudnn_versions {
        let bin_dir = ver_dir.join("bin");
        if !bin_dir.is_dir() {
            continue;
        }
        let mut cuda_bins: Vec<(PathBuf, (u32, u32))> = Vec::new();
        for entry in fs::read_dir(&bin_dir).ok()?.flatten() {
            if !entry.file_type().ok()?.is_dir() {
                continue;
            }
            let name = entry.file_name().to_string_lossy().into_owned();
            if name.eq_ignore_ascii_case("x64") {
                continue;
            }
            let Some(cuda_ver) = parse_dot_version(&name) else {
                continue;
            };
            let x64 = entry.path().join("x64");
            if is_cudnn_x64_bin(&x64) {
                cuda_bins.push((x64, cuda_ver));
            }
        }
        if let Some(picked) = pick_cudnn_cuda_bin(&cuda_bins, toolkit_ver) {
            return Some(picked);
        }
        if toolkit_ver.is_none() {
            let x64 = bin_dir.join("x64");
            if is_cudnn_x64_bin(&x64) {
                return Some(x64);
            }
            if is_cudnn_x64_bin(&bin_dir) {
                return Some(bin_dir);
            }
        }
    }
    None
}

#[cfg(windows)]
fn is_cuda_toolkit_bin(dir: &Path) -> bool {
    if !dir.is_dir() {
        return false;
    }
    let Ok(entries) = fs::read_dir(dir) else {
        return false;
    };
    for entry in entries.flatten() {
        let name = entry.file_name().to_string_lossy().to_lowercase();
        if name.starts_with("cudart64") && name.ends_with(".dll") {
            return true;
        }
    }
    false
}

#[cfg(windows)]
fn detect_cuda_toolkit_windows() -> Option<(PathBuf, (u32, u32))> {
    let root = PathBuf::from(CUDA_TOOLKIT_ROOT);
    if !root.is_dir() {
        return None;
    }
    let mut versions: Vec<(PathBuf, (u32, u32))> = Vec::new();
    for entry in fs::read_dir(&root).ok()?.flatten() {
        if !entry.file_type().ok()?.is_dir() {
            continue;
        }
        let name = entry.file_name().to_string_lossy().into_owned();
        let Some(ver) = name.strip_prefix('v').and_then(parse_dot_version) else {
            continue;
        };
        let bin_dir = entry.path().join("bin");
        if is_cuda_toolkit_bin(&bin_dir) {
            versions.push((bin_dir, ver));
        }
    }
    if versions.is_empty() {
        return None;
    }
    versions.sort_by(|a, b| b.1.cmp(&a.1));
    Some(versions[0].clone())
}

#[cfg(windows)]
fn detect_cuda_bin_windows() -> Option<PathBuf> {
    detect_cuda_toolkit_windows().map(|(bin, _)| bin)
}

#[cfg(windows)]
fn toolkit_version_for_cudnn(cuda_bin_override: Option<&Path>) -> Option<(u32, u32)> {
    if let Some(bin_dir) = cuda_bin_override {
        if let Some(ver) = cuda_version_from_bin(bin_dir) {
            return Some(ver);
        }
    }
    detect_cuda_toolkit_windows().map(|(_, ver)| ver)
}
