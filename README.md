# Install RescueBox 3.1 on Windows 11

**Recommended hardware:** powerful CPU, 32 GB RAM, NVIDIA GPU with latest driver.

Refer to the screenshots PDF in `help`.

---

## 1. Administrator login and NVIDIA prerequisites

Log in to Windows with **administrator** rights.

GPU-accelerated models require these NVIDIA components on Windows 11:

| Component | Install |
|-----------|---------|
| **cuDNN 9.x** | [NVIDIA cuDNN downloads (Windows 11, x86_64, exe local)](https://developer.nvidia.com/cudnn-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local) |
| **CUDA 12.x** | [CUDA 12.0 download archive (Windows 11, x86_64, exe local)](https://developer.nvidia.com/cuda-12-0-0-download-archive?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local) |

Accept installer defaults. No other prerequisites (for example Visual Studio) are required.

**Verify** — open `cmd.exe` and run:

```text
where cublasLt64_12.dll
```

Expected output:

```text
C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.0\bin\cublasLt64_12.dll
```

---

## 2. Download the RescueBox installer bundle

Download the RescueBox installer ZIP to your Windows machine.

---

## 3. Extract the bundle

Extract all files to a folder and confirm **`RescueBox_3.1.0_x64_en-US.msi`** is present along with the other ZIPs:

- `ollama_models_3.1.zip`
- `onnx_models_3.1.zip`
- `pre-reqs_3.1.zip` (bundle may label this similarly to `pre-req_3.1.zip`)

---

## 4. Trust the signing certificate

Double-click **`rescuebox.cer`** and import the certificate.

Self-signed certificate thumbprint: `721dc6509d5643bc3232c43d3a27ef8af06a1651`

---

## 5. Run the MSI installer

Double-click **`RescueBox_3.1.0_x64_en-US.msi`**. This installs RescueBox and bundled prerequisites.

See the installer PDF in `docs` for a screenshot sequence.

### a. Destination folder

Choose a destination with at least **2 GB** free space.

**Default:** `C:\Users\<USER>\AppData\Local\RescueBox\` — use this or enter another path.

### b. Model extraction and prerequisites

The installer extracts AI/ML models (this can take a while) and installs prerequisites such as **Ollama**, **PostgreSQL**, and **WinFsp**.

Review Ollama and permission prompts; accept defaults and close when finished.

### c. After install

RescueBox starts automatically. Open the UI at:

**http://localhost:8080**

---

## 6. Assistant UI, shutdown, and uninstall

- If you **exit the RescueBox assistant** (thin client), the **server keeps running** — you can still use RescueBox in the browser.
- To **shut down RescueBox**, use the checkbox to stop the server, then close the assistant UI.
- To **uninstall**, use **Add or remove programs** in Windows Settings / Control Panel.
- **Ollama** and **WinFsp** must be uninstalled manually if you no longer need them.
