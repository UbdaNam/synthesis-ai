from src.indexing.data_type_detector import DataTypeDetector
from tests.unit._stage4_test_utils import make_ldus


def test_data_type_detector_maps_stage3_chunk_types():
    detector = DataTypeDetector()
    data_types = detector.detect_for_chunks(make_ldus())
    assert data_types == ["figures", "lists", "narrative_text", "tables"]
