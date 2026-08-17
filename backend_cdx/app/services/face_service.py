import base64
import json
from io import BytesIO

import numpy as np
from PIL import Image
import cv2

from scipy.spatial.distance import euclidean
from keras_facenet import FaceNet
from mtcnn import MTCNN



class FaceService:
    """Detect faces with MTCNN and encode them with FaceNet."""

    def __init__(self):
        self.detector = MTCNN() if MTCNN else None
        self.embedder = FaceNet() if FaceNet else None

    def encode_image(self, image_base64: str) -> list[float]:
        """Convert a base64 image into a FaceNet embedding."""
        if not self.detector or not self.embedder:
            raise RuntimeError("Install mtcnn and keras-facenet to enable face recognition.")

        image = self._decode_base64_image(image_base64)
        faces = self.detector.detect_faces(image)
        if not faces:
            raise ValueError("No face detected in the image.")

        x, y, width, height = faces[0]["box"]
        x, y = max(x, 0), max(y, 0)
        face = image[y : y + height, x : x + width]
        if cv2:
            face = cv2.resize(face, (160, 160))
        embedding = self.embedder.embeddings([face])[0]
        return embedding.astype(float).tolist()

    def compare(self, probe_encoding: list[float], stored_encoding: str, threshold: float = 0.8) -> bool:
        """Compare two face encodings with Euclidean distance."""
        stored = np.array(json.loads(stored_encoding), dtype=float)
        probe = np.array(probe_encoding, dtype=float)
        distance = euclidean(stored, probe) if euclidean else np.linalg.norm(stored - probe)
        return bool(distance <= threshold)

    def serialize(self, encoding: list[float]) -> str:
        """Store the encoding as JSON text in SQLite."""
        return json.dumps(encoding)

    def _decode_base64_image(self, image_base64: str) -> np.ndarray:
        """Decode browser camera output into an RGB NumPy image."""
        if "," in image_base64:
            image_base64 = image_base64.split(",", 1)[1]
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return np.asarray(image)
