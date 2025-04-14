import os
import cv2
from deepface import DeepFace
from src.facematch.utils.embedding_utils import get_arcface_embedding
from scipy.spatial.distance import cosine

# Setup paths
script_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(script_dir, "src/facematch/models")
model_path = os.path.join(models_dir, "arcface_model_new.onnx")

# Test image
img_path = "visualization/single.jpg_step4_final_face0.jpg"
img = cv2.imread(img_path)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# DeepFace embedding (with error handling)
try:
    deepface_emb = DeepFace.represent(
        img_path=img_path,
        model_name="ArcFace",
        detector_backend="skip",
        enforce_detection=False
    )[0]["embedding"]
except Exception as e:
    print(f"DeepFace error: {e}")
    exit(1)

# Your custom embedding
try:
    custom_emb = get_arcface_embedding(img_rgb, model_path)
except Exception as e:
    print(f"Custom embedding error: {e}")
    exit(1)

# Compare embedding dimensions
print(f"DeepFace shape: {len(deepface_emb)}, Custom shape: {len(custom_emb)}")

# Compare value ranges
print(f"DeepFace range: {min(deepface_emb):.6f} to {max(deepface_emb):.6f}")
print(f"Custom range: {min(custom_emb):.6f} to {max(custom_emb):.6f}")

# Calculate similarity between embeddings
similarity = 1 - cosine(deepface_emb, custom_emb)
print(f"Cosine similarity between embeddings: {similarity:.6f}")

# Compare first few values
print("\nFirst 5 values comparison:")
for i in range(5):
    print(f"Index {i}: DeepFace={deepface_emb[i]:.6f}, Custom={custom_emb[i]:.6f}, Diff={abs(deepface_emb[i]-custom_emb[i]):.6f}")