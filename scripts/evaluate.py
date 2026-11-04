"""
Model evaluation script for Grievance Router.
Tests classification accuracy on sample complaints.
"""
import sys
import os
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.classifier import get_classifier
from app.services.geocoder import get_geo_service

# Test cases: (text, expected_category)
EVALUATION_CASES = [
    # Roads - English
    ("big pothole on main road, cars getting stuck", "roads"),
    ("road damaged needs immediate repair", "roads"),
    ("severe road damage on highway", "roads"),
    ("pothole causing accidents", "roads"),

    # Roads - Hindi
    ("सड़क पर बड़ा गड्ढा है", "roads"),
    ("रास्ता खराब हो गया है", "roads"),

    # Water - English
    ("water pipeline leaking badly", "water"),
    ("no water supply since yesterday", "water"),
    ("water pipe burst on road", "water"),
    ("drinking water not available", "water"),

    # Water - Hindi
    ("पानी की पाइप से पानी रिस रहा है", "water"),
    ("पानी की आपूर्ति नहीं हो रही", "water"),

    # Waste - English
    ("garbage not collected for a week", "waste"),
    ("dustbin overflowing, bad smell", "waste"),
    ("waste dumped on empty plot", "waste"),
    ("trash pile on roadside", "waste"),

    # Waste - Hindi
    ("कचरा नहीं उठाया गया", "waste"),
    ("गंदगी से बदबू आ रही है", "waste"),

    # Streetlights - English
    ("street light not working on our street", "streetlights"),
    ("area is dark, multiple lights broken", "streetlights"),
    ("streetlight pole damaged", "streetlights"),
    ("no street lights in our area", "streetlights"),

    # Streetlights - Hindi
    ("बत्ती नहीं जल रही है", "streetlights"),
    ("स्ट्रीट लाइट खराब है", "streetlights"),

    # Drainage - English
    ("drain blocked with garbage", "drainage"),
    ("drainage water overflow on road", "drainage"),
    ("sewage water coming out", "drainage"),
    ("drain needs cleaning", "drainage"),

    # Drainage - Hindi
    ("नाली में पानी भर गया है", "drainage"),
    ("नाली बंद हो गई है", "drainage"),

    # Trees - English
    ("tree branch fallen on road", "trees"),
    ("tree needs pruning, blocking path", "trees"),
    ("dangerous tree leaning on house", "trees"),
    ("tree fallen blocking traffic", "trees"),

    # Trees - Hindi
    ("पेड़ की डाली टूटकर गिर गई है", "trees"),
    ("पेड़ काटना है", "trees"),
]

def evaluate_classifier():
    """Evaluate classifier on test cases."""
    print("=" * 60)
    print("GRIEVANCE ROUTER - CLASSIFICATION EVALUATION")
    print("=" * 60)

    classifier = get_classifier()
    print(f"\nLoading model: {classifier.model}")
    classifier.load_model()
    classifier.load_prototypes()
    classifier.build_index()

    # Run evaluation
    results = defaultdict(lambda: {"correct": 0, "total": 0})

    correct = 0
    total = len(EVALUATION_CASES)

    print(f"\nEvaluating {total} test cases...")

    for text, expected_category in EVALUATION_CASES:
        predicted_category, _, confidence = classifier.predict_category(text)

        results[expected_category]["total"] += 1
        if predicted_category == expected_category:
            results[expected_category]["correct"] += 1
            correct += 1
            status = "✓"
        else:
            status = "✗"

        print(f"  {status} '{text[:40]}...' => expected: {expected_category}, got: {predicted_category} (conf: {confidence:.2f})")

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS BY CATEGORY")
    print("=" * 60)

    for category in sorted(results.keys()):
        stats = results[category]
        accuracy = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {category:15s}: {stats['correct']:2d}/{stats['total']:2d} ({accuracy:5.1f}%)")

    overall_accuracy = correct / total * 100 if total > 0 else 0
    print("-" * 60)
    print(f"  {'OVERALL':15s}: {correct:2d}/{total:2d} ({overall_accuracy:5.1f}%)")

    return overall_accuracy

def evaluate_geo_service():
    """Evaluate geocoding service."""
    print("\n" + "=" * 60)
    print("GEOCODING EVALUATION")
    print("=" * 60)

    geo_service = get_geo_service()

    # Test distance calculation
    print("\nDistance calculation tests:")

    # HSR to Koramangala (approx 3km)
    dist = geo_service.distance_meters(12.9121, 77.6446, 12.9352, 77.6245)
    print(f"  HSR to Koramangala: {dist:.0f}m (expected ~3000m)")
    assert 2500 < dist < 3500, "Distance calculation off"

    # Test within merge radius
    print("\nMerge radius tests:")

    nearby = geo_service.find_nearby_complaints(
        12.9121, 77.6446,
        [
            {'id': 1, 'latitude': 12.9121, 'longitude': 77.6446},
            {'id': 2, 'latitude': 12.9125, 'longitude': 77.6450},  # ~50m
            {'id': 3, 'latitude': 12.9200, 'longitude': 77.6500},  # ~1km
        ],
        radius_meters=150
    )
    print(f"  Found {len(nearby)} complaints within 150m (expected 2)")
    assert len(nearby) == 2

    print("\n✓ Geo service tests passed!")

if __name__ == "__main__":
    try:
        accuracy = evaluate_classifier()
        evaluate_geo_service()

        print("\n" + "=" * 60)
        if accuracy >= 70:
            print(f"EVALUATION COMPLETE - Accuracy: {accuracy:.1f}% ✓")
        elif accuracy >= 50:
            print(f"EVALUATION COMPLETE - Accuracy: {accuracy:.1f}% (acceptable)")
        else:
            print(f"EVALUATION COMPLETE - Accuracy: {accuracy:.1f}% (needs improvement)")
        print("=" * 60)

    except Exception as e:
        print(f"\nEvaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)