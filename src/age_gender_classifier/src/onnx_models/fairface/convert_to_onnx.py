from transformers import ViTForImageClassification
from transformers import ViTImageProcessor
import torch
from pathlib import Path
import os

# Load model and processor from HuggingFace
model_name = "dima806/fairface_age_image_detection"
model = ViTForImageClassification.from_pretrained(model_name)
processor = ViTImageProcessor.from_pretrained(model_name)

# Set model to evaluation mode
model.eval()

# Dummy input for ONNX export
dummy_input = torch.randn(1, 3, 224, 224)  # ViT expects (B, C, H, W)

# Output path
output_dir = Path("onnx_exports")
output_dir.mkdir(exist_ok=True)
onnx_model_path = output_dir / "fairface_age.onnx"


# Export to ONNX
torch.onnx.export(
    model,
    dummy_input,
    onnx_model_path.as_posix(),
    input_names=["pixel_values"],
    output_names=["logits"],
    dynamic_axes={"pixel_values": {0: "batch_size"}, "logits": {0: "batch_size"}},
    opset_version=14,
)

print(f"Model exported to: {onnx_model_path.resolve()}")
