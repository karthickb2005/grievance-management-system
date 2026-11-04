"""
Multilingual complaint classifier using sentence transformers and FAISS.
Handles English, Hinglish, Hindi, Kannada, and Tamil.
"""
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
from langdetect import detect, LangDetectException

from app.config import settings

class ComplaintClassifier:
    def __init__(self):
        self.model = None
        self.index = None
        self.prototypes = []
        self.categories = ["roads", "water", "waste", "streetlights", "drainage", "trees"]

        # Department mapping
        self.dept_mapping = {
            "roads": "Roads & Infrastructure",
            "water": "Water Supply & Sewerage",
            "waste": "Solid Waste Management",
            "streetlights": "Electrical & Street Lighting",
            "drainage": "Storm Water Drains",
            "trees": "Horticulture & Parks"
        }

    def load_model(self):
        """Load the multilingual embedding model (lazy loading)."""
        if self.model is None:
            print(f"Loading embedding model: {settings.EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            print("Model loaded successfully.")

    def load_prototypes(self, prototype_file: Optional[Path] = None):
        """Load classification prototypes from JSON."""
        if prototype_file is None:
            prototype_file = settings.DATA_DIR / "prototypes.json"

        if not prototype_file.exists():
            print(f"Warning: Prototype file not found at {prototype_file}")
            self._create_default_prototypes()
            return

        with open(prototype_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.prototypes = data.get("prototypes", [])

        print(f"Loaded {len(self.prototypes)} prototypes across {len(self.categories)} categories.")

    def _create_default_prototypes(self):
        """Create minimal prototypes in memory (used if file missing)."""
        self.prototypes = [
            {"category": "roads", "text": "pothole on main road", "language": "en"},
            {"category": "roads", "text": "सड़क पर गड्ढा है", "language": "hi"},
            {"category": "roads", "text": "road damage near my house", "language": "en"},

            {"category": "water", "text": "water pipeline leaking", "language": "en"},
            {"category": "water", "text": "पानी की पाइप लीक हो रही है", "language": "hi"},
            {"category": "water", "text": "no water supply since morning", "language": "en"},

            {"category": "waste", "text": "garbage not collected", "language": "en"},
            {"category": "waste", "text": "कचरा नहीं उठाया गया", "language": "hi"},
            {"category": "waste", "text": "overflowing dustbin near park", "language": "en"},

            {"category": "streetlights", "text": "street light not working", "language": "en"},
            {"category": "streetlights", "text": "बत्ती नहीं जल रही है", "language": "hi"},
            {"category": "streetlights", "text": "streetlight broken", "language": "en"},

            {"category": "drainage", "text": "drain blocked with garbage", "language": "en"},
            {"category": "drainage", "text": "नाली में पानी भर गया है", "language": "hi"},
            {"category": "drainage", "text": "drainage overflow on street", "language": "en"},

            {"category": "trees", "text": "tree branches blocking road", "language": "en"},
            {"category": "trees", "text": "पेड़ की डाली गिर गई है", "language": "hi"},
            {"category": "trees", "text": "need tree pruning", "language": "en"},
        ]

    def build_index(self):
        """Build FAISS index from prototypes."""
        self.load_model()

        if not self.prototypes:
            self.load_prototypes()

        # Generate embeddings for all prototypes
        texts = [p["text"] for p in self.prototypes]
        print(f"Generating embeddings for {len(texts)} prototypes...")
        embeddings = self.model.encode(texts, show_progress_bar=False)

        # Build FAISS index (simple flat L2 for small dataset)
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))

        print(f"FAISS index built with {self.index.ntotal} vectors.")

    def detect_language(self, text: str) -> str:
        """Detect language of the complaint text."""
        try:
            lang = detect(text)
            # Map to our supported languages
            lang_map = {
                'en': 'en',
                'hi': 'hi',
                'kn': 'kn',
                'ta': 'ta'
            }
            detected = lang_map.get(lang, 'en')

            # Check for Hinglish (mixed script or English with Hindi transliteration)
            if lang == 'en' and any(word in text.lower() for word in ['hai', 'nahi', 'karo', 'road', 'paani']):
                detected = 'hi-en'

            return detected
        except LangDetectException:
            return 'en'  # Default to English

    def classify(self, text: str, top_k: int = 3) -> List[Dict[str, any]]:
        """
        Classify complaint text into categories.
        Returns list of {category, score, department} sorted by confidence.
        """
        if self.model is None:
            self.load_model()

        if self.index is None:
            self.build_index()

        # Generate embedding for input text
        query_embedding = self.model.encode([text], show_progress_bar=False)

        # Search in FAISS index
        distances, indices = self.index.search(query_embedding.astype('float32'), k=top_k)

        # Convert distances to similarity scores (cosine-like)
        # Lower L2 distance = higher similarity
        max_dist = np.max(distances[0]) if np.max(distances[0]) > 0 else 1.0
        scores = 1 - (distances[0] / max_dist)

        results = []
        for idx, score in zip(indices[0], scores):
            prototype = self.prototypes[idx]
            category = prototype["category"]
            department = self.dept_mapping.get(category, "General")

            results.append({
                "category": category,
                "confidence": float(score),
                "department": department
            })

        return results

    def predict_category(self, text: str) -> Tuple[str, str, float]:
        """
        Predict single best category for a complaint.
        Returns (category, department, confidence).
        """
        results = self.classify(text, top_k=1)
        if results:
            top = results[0]
            return top["category"], top["department"], top["confidence"]
        return "roads", "Roads & Infrastructure", 0.5  # Default fallback

    def score_severity(self, text: str, category: str) -> str:
        """
        Score severity based on keywords (placeholder for vision model).

        NOTE: This is a SIMPLIFIED keyword-based approach.
        A real system would use:
        - Image analysis (vision transformer)
        - Contextual severity model
        - Historical data patterns
        """
        text_lower = text.lower()

        # Critical keywords
        critical_keywords = [
            'emergency', 'urgent', 'dangerous', 'accident', 'injured',
            'live wire', 'open manhole', 'flooding', 'collapsed',
            'अत्यावश्यक', 'खतरनाक', 'दुर्घटना'
        ]

        # High severity keywords
        high_keywords = [
            'broken', 'major', 'severe', 'blocked', 'overflow',
            'leaking badly', 'multiple', 'main road',
            'बड़ा', 'गंभीर', 'मुख्य सड़क'
        ]

        # Medium severity keywords
        medium_keywords = [
            'needs repair', 'not working', 'damaged', 'problem',
            'मरम्मत', 'खराब', 'समस्या'
        ]

        if any(kw in text_lower for kw in critical_keywords):
            return "critical"
        elif any(kw in text_lower for kw in high_keywords):
            return "high"
        elif any(kw in text_lower for kw in medium_keywords):
            return "medium"
        else:
            return "low"

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        if self.model is None:
            self.load_model()

        embedding = self.model.encode([text], show_progress_bar=False)[0]
        return embedding.tolist()

# Global instance (lazy loaded)
_classifier = None

def get_classifier() -> ComplaintClassifier:
    """Get or create global classifier instance."""
    global _classifier
    if _classifier is None:
        _classifier = ComplaintClassifier()
    return _classifier
