"""
Unit tests for the multilingual classifier.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.classifier import ComplaintClassifier

@pytest.fixture
def classifier():
    """Create a classifier instance for testing."""
    clf = ComplaintClassifier()
    clf.load_model()
    clf.load_prototypes()
    clf.build_index()
    return clf

def test_language_detection(classifier):
    """Test language detection for different inputs."""
    # English
    assert classifier.detect_language("pothole on main road") == "en"

    # Hindi
    lang = classifier.detect_language("सड़क पर गड्ढा है")
    assert lang in ["hi", "en"]  # May vary

    # Hinglish
    lang = classifier.detect_language("road pe bahut bada pothole hai")
    assert lang in ["en", "hi-en"]

def test_classification(classifier):
    """Test complaint classification."""
    # Roads
    results = classifier.classify("big pothole on main road")
    assert len(results) > 0
    assert results[0]["category"] == "roads"
    assert results[0]["confidence"] > 0.5

    # Water
    results = classifier.classify("water pipeline leaking")
    assert len(results) > 0
    assert results[0]["category"] == "water"

    # Waste
    results = classifier.classify("garbage not collected")
    assert len(results) > 0
    assert results[0]["category"] == "waste"

def test_multilingual_classification(classifier):
    """Test classification with Hindi text."""
    # Hindi roads complaint
    results = classifier.classify("सड़क पर गड्ढा है")
    assert len(results) > 0
    # Should classify as roads (may have lower confidence due to limited prototypes)
    assert any(r["category"] == "roads" for r in results)

def test_predict_category(classifier):
    """Test single category prediction."""
    category, department, confidence = classifier.predict_category("pothole on road")
    assert category in ["roads", "water", "waste", "streetlights", "drainage", "trees"]
    assert department is not None
    assert 0 <= confidence <= 1

def test_severity_scoring(classifier):
    """Test severity scoring."""
    # Low severity
    assert classifier.score_severity("small pothole", "roads") == "low"

    # Medium severity
    assert classifier.score_severity("road needs repair", "roads") in ["low", "medium"]

    # High severity
    assert classifier.score_severity("major road damage", "roads") in ["medium", "high"]

    # Critical severity
    assert classifier.score_severity("emergency, dangerous pothole, accident", "roads") == "critical"

def test_embedding_generation(classifier):
    """Test embedding generation."""
    embedding = classifier.get_embedding("test complaint")
    assert isinstance(embedding, list)
    assert len(embedding) == 384  # MiniLM dimension
    assert all(isinstance(x, float) for x in embedding)

def test_department_mapping(classifier):
    """Test department mapping."""
    assert classifier.dept_mapping["roads"] == "Roads & Infrastructure"
    assert classifier.dept_mapping["water"] == "Water Supply & Sewerage"
    assert classifier.dept_mapping["waste"] == "Solid Waste Management"
    assert classifier.dept_mapping["streetlights"] == "Electrical & Street Lighting"
    assert classifier.dept_mapping["drainage"] == "Storm Water Drains"
    assert classifier.dept_mapping["trees"] == "Horticulture & Parks"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
