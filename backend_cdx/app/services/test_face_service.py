# tests/test_face_service.py

import base64
import json
from io import BytesIO
from unittest.mock import MagicMock

import numpy as np
import pytest
from PIL import Image


from app.services.face_service import FaceService


@pytest.fixture
def service():
    """Create a FaceService without loading real ML models."""
    service = FaceService.__new__(FaceService)
    service.detector = MagicMock()
    service.embedder = MagicMock()
    return service


def make_base64_image(with_data_url=False):
    """Create a small valid PNG and return it as base64."""
    image = Image.new("RGB", (100, 100), color="red")

    buffer = BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(buffer.getvalue()).decode()

    if with_data_url:
        return f"data:image/png;base64,{encoded}"

    return encoded


class TestDecodeBase64Image:
    def test_decodes_base64_image(self, service):
        image_base64 = make_base64_image()

        result = service._decode_base64_image(image_base64)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_decodes_data_url(self, service):
        image_base64 = make_base64_image(with_data_url=True)

        result = service._decode_base64_image(image_base64)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    def test_converts_image_to_rgb(self, service):
        image = Image.new("RGBA", (20, 30), color=(255, 0, 0, 128))

        buffer = BytesIO()
        image.save(buffer, format="PNG")

        encoded = base64.b64encode(buffer.getvalue()).decode()

        result = service._decode_base64_image(encoded)

        assert result.shape == (30, 20, 3)


class TestSerialize:
    def test_serializes_encoding(self, service):
        encoding = [0.1, 0.2, 0.3]

        result = service.serialize(encoding)

        assert result == "[0.1, 0.2, 0.3]"

    def test_serialized_value_can_be_deserialized(self, service):
        encoding = [0.1, 0.2, 0.3]

        result = service.serialize(encoding)

        assert json.loads(result) == encoding


class TestCompare:
    def test_returns_true_when_encodings_are_identical(self, service):
        encoding = [0.1, 0.2, 0.3]

        result = service.compare(
            probe_encoding=encoding,
            stored_encoding=json.dumps(encoding),
        )

        assert result is True

    def test_returns_true_when_distance_is_below_threshold(self, service):
        stored = [0.0, 0.0, 0.0]
        probe = [0.1, 0.1, 0.1]

        result = service.compare(
            probe_encoding=probe,
            stored_encoding=json.dumps(stored),
            threshold=0.2,
        )

        assert result is True

    def test_returns_false_when_distance_is_above_threshold(self, service):
        stored = [0.0, 0.0, 0.0]
        probe = [1.0, 1.0, 1.0]

        result = service.compare(
            probe_encoding=probe,
            stored_encoding=json.dumps(stored),
            threshold=0.8,
        )

        assert result is False

    def test_returns_true_when_distance_equals_threshold(self, service):
        stored = [0.0, 0.0]
        probe = [0.6, 0.8]  # Euclidean distance = 1.0

        result = service.compare(
            probe_encoding=probe,
            stored_encoding=json.dumps(stored),
            threshold=1.0,
        )

        assert result is True

    def test_custom_threshold_is_used(self, service):
        stored = [0.0, 0.0]
        probe = [0.6, 0.8]  # distance = 1.0

        assert service.compare(
            probe,
            json.dumps(stored),
            threshold=0.99,
        ) is False

        assert service.compare(
            probe,
            json.dumps(stored),
            threshold=1.0,
        ) is True

    def test_invalid_stored_json_raises_error(self, service):
        with pytest.raises(json.JSONDecodeError):
            service.compare(
                probe_encoding=[0.1, 0.2],
                stored_encoding="not valid json",
            )

    def test_empty_encodings(self, service):
        result = service.compare(
            probe_encoding=[],
            stored_encoding="[]",
        )

        assert result is True


class TestEncodeImage:
    def test_raises_when_detector_is_missing(self):
        service = FaceService.__new__(FaceService)
        service.detector = None
        service.embedder = MagicMock()

        with pytest.raises(RuntimeError, match="Install mtcnn"):
            service.encode_image(make_base64_image())

    def test_raises_when_embedder_is_missing(self):
        service = FaceService.__new__(FaceService)
        service.detector = MagicMock()
        service.embedder = None

        with pytest.raises(RuntimeError, match="Install mtcnn"):
            service.encode_image(make_base64_image())

    def test_raises_when_no_face_is_detected(self, service):
        service.detector.detect_faces.return_value = []

        with pytest.raises(ValueError, match="No face detected"):
            service.encode_image(make_base64_image())

        service.detector.detect_faces.assert_called_once()

    def test_encodes_first_detected_face(self, service):
        image_base64 = make_base64_image()

        service.detector.detect_faces.return_value = [
            {
                "box": [10, 20, 50, 40],
                "confidence": 0.99,
            }
        ]

        embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        service.embedder.embeddings.return_value = np.array([embedding])

        result = service.encode_image(image_base64)

        assert result == [0.10000000149011612, 0.20000000298023224, 0.30000001192092896]

        service.detector.detect_faces.assert_called_once()
        service.embedder.embeddings.assert_called_once()

        face = service.embedder.embeddings.call_args.args[0][0]

        # cv2.resize() should produce the FaceNet input size.
        assert face.shape == (160, 160, 3)

    def test_returns_embedding_as_python_floats(self, service):
        service.detector.detect_faces.return_value = [
            {"box": [0, 0, 50, 50]}
        ]

        service.embedder.embeddings.return_value = np.array(
            [[1, 2, 3]],
            dtype=np.float32,
        )

        result = service.encode_image(make_base64_image())

        assert isinstance(result, list)
        assert all(isinstance(value, float) for value in result)
        assert len(result) == 3

    def test_negative_coordinates_are_clamped(self, service):
        service.detector.detect_faces.return_value = [
            {"box": [-10, -20, 50, 40]}
        ]

        service.embedder.embeddings.return_value = np.array(
            [[0.1, 0.2]],
            dtype=np.float32,
        )

        service.encode_image(make_base64_image())

        face = service.embedder.embeddings.call_args.args[0][0]

        assert face.shape == (160, 160, 3)

    def test_only_first_face_is_encoded(self, service):
        service.detector.detect_faces.return_value = [
            {"box": [10, 10, 30, 30]},
            {"box": [50, 50, 30, 30]},
        ]

        service.embedder.embeddings.return_value = np.array(
            [[0.1, 0.2, 0.3]],
            dtype=np.float32,
        )

        service.encode_image(make_base64_image())

        # FaceNet should receive one face, not all detected faces.
        faces = service.embedder.embeddings.call_args.args[0]
        assert len(faces) == 1

    def test_detector_receives_decoded_image(self, service):
        service.detector.detect_faces.return_value = [
            {"box": [0, 0, 20, 20]}
        ]

        service.embedder.embeddings.return_value = np.array(
            [[0.1]],
            dtype=np.float32,
        )

        service.encode_image(make_base64_image())

        detected_image = service.detector.detect_faces.call_args.args[0]

        assert isinstance(detected_image, np.ndarray)
        assert detected_image.shape == (100, 100, 3)