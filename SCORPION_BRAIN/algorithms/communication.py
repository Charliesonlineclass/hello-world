"""
SCORPION_BRAIN Communication Algorithms
=======================================
HERMES specialty algorithms for text and expression.

Algorithms:
- tf_idf: Extract important terms from text
- sentiment_analysis: Analyze emotional content
- template_fill: Fill templates with dynamic content
"""

import re
import math
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter
import logging

logger = logging.getLogger(__name__)


# Sentiment lexicons (simplified)
POSITIVE_WORDS = {
    'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'awesome',
    'love', 'happy', 'joy', 'beautiful', 'perfect', 'best', 'brilliant', 'superb',
    'positive', 'success', 'win', 'winner', 'bright', 'cheerful', 'delightful',
    'enjoy', 'excited', 'glad', 'pleased', 'proud', 'satisfied', 'thrilled',
    'helpful', 'kind', 'nice', 'friendly', 'warm', 'generous', 'caring',
    'impressive', 'outstanding', 'remarkable', 'exceptional', 'magnificent'
}

NEGATIVE_WORDS = {
    'bad', 'terrible', 'awful', 'horrible', 'poor', 'worst', 'hate', 'sad',
    'angry', 'upset', 'disappointed', 'frustrated', 'annoyed', 'irritated',
    'fail', 'failure', 'wrong', 'error', 'mistake', 'problem', 'issue',
    'difficult', 'hard', 'painful', 'ugly', 'nasty', 'evil', 'dark', 'gloomy',
    'boring', 'dull', 'stupid', 'idiotic', 'useless', 'worthless', 'pathetic',
    'fear', 'scared', 'worried', 'anxious', 'nervous', 'stressed', 'depressed',
    'broken', 'damaged', 'ruined', 'destroyed', 'lost', 'missing', 'dead'
}

INTENSIFIERS = {
    'very': 1.5, 'really': 1.5, 'extremely': 2.0, 'incredibly': 2.0,
    'absolutely': 2.0, 'totally': 1.5, 'completely': 1.5, 'utterly': 2.0,
    'quite': 1.3, 'rather': 1.2, 'somewhat': 0.8, 'slightly': 0.5,
    'barely': 0.3, 'hardly': 0.3, 'almost': 0.7, 'nearly': 0.8
}

NEGATORS = {'not', 'no', "n't", 'never', 'neither', 'nobody', 'nothing', 'nowhere', 'none'}


@dataclass
class TFIDFResult:
    """Result of TF-IDF calculation."""
    term: str
    tf: float  # Term frequency
    idf: float  # Inverse document frequency
    tfidf: float  # Combined score
    doc_count: int  # Number of documents containing term


@dataclass
class SentimentScore:
    """Sentiment analysis result."""
    positive: float  # 0-1
    negative: float  # 0-1
    neutral: float  # 0-1
    compound: float  # -1 to 1
    dominant: str  # "positive", "negative", or "neutral"


@dataclass
class Template:
    """A template for text generation."""
    template: str
    variables: List[str] = field(default_factory=list)
    defaults: Dict[str, str] = field(default_factory=dict)
    validators: Dict[str, callable] = field(default_factory=dict)

    def __post_init__(self):
        # Extract variables from template
        self.variables = re.findall(r'\{(\w+)\}', self.template)


def tf_idf(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Calculate TF-IDF scores for terms in documents.

    Args:
        task: Query or document text
        context: Should contain 'documents' (list of texts) or 'corpus'

    Returns:
        Dict with TF-IDF scores and top terms
    """
    context = context or {}

    # Get documents
    documents = context.get('documents', context.get('corpus', [task]))
    if isinstance(documents, str):
        documents = [documents]

    # Ensure we have at least the task as a document
    if not documents:
        documents = [task]

    # Tokenize all documents
    doc_tokens = []
    for doc in documents:
        tokens = _tokenize(doc)
        doc_tokens.append(tokens)

    # Calculate document frequency for each term
    all_terms = set()
    doc_freq = Counter()

    for tokens in doc_tokens:
        unique_tokens = set(tokens)
        all_terms.update(unique_tokens)
        for token in unique_tokens:
            doc_freq[token] += 1

    num_docs = len(documents)

    # Calculate TF-IDF for each document
    results = []
    for doc_idx, tokens in enumerate(doc_tokens):
        term_counts = Counter(tokens)
        total_terms = len(tokens)

        doc_results = []
        for term, count in term_counts.items():
            tf = count / total_terms if total_terms > 0 else 0
            idf = math.log((num_docs + 1) / (doc_freq[term] + 1)) + 1  # Smoothed IDF
            tfidf = tf * idf

            doc_results.append(TFIDFResult(
                term=term,
                tf=tf,
                idf=idf,
                tfidf=tfidf,
                doc_count=doc_freq[term]
            ))

        # Sort by TF-IDF score
        doc_results.sort(key=lambda x: x.tfidf, reverse=True)
        results.append({
            "document_index": doc_idx,
            "terms": [
                {"term": r.term, "tfidf": round(r.tfidf, 4), "tf": round(r.tf, 4), "idf": round(r.idf, 4)}
                for r in doc_results[:20]  # Top 20 terms
            ]
        })

    # Get overall top terms across all documents
    all_scores = {}
    for doc_result in results:
        for term_info in doc_result["terms"]:
            term = term_info["term"]
            if term not in all_scores:
                all_scores[term] = 0
            all_scores[term] = max(all_scores[term], term_info["tfidf"])

    top_terms = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "algorithm": "tf_idf",
        "document_count": num_docs,
        "unique_terms": len(all_terms),
        "top_terms": [{"term": t, "max_tfidf": round(s, 4)} for t, s in top_terms],
        "document_results": results[:5],  # Limit to first 5 docs
        "keywords": [t for t, s in top_terms]
    }


def sentiment_analysis(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Analyze sentiment in text.

    Args:
        task: Text to analyze
        context: Optional settings

    Returns:
        Dict with sentiment scores and analysis
    """
    context = context or {}
    text = context.get('text', task)

    # Tokenize and analyze
    words = text.lower().split()
    sentences = _split_sentences(text)

    positive_count = 0
    negative_count = 0
    intensity_modifier = 1.0
    negation_active = False

    word_sentiments = []

    for i, word in enumerate(words):
        clean_word = re.sub(r'[^\w]', '', word)

        # Check for negators
        if clean_word in NEGATORS:
            negation_active = True
            continue

        # Check for intensifiers
        if clean_word in INTENSIFIERS:
            intensity_modifier = INTENSIFIERS[clean_word]
            continue

        # Check sentiment
        sentiment = 0
        if clean_word in POSITIVE_WORDS:
            sentiment = 1 * intensity_modifier
            if negation_active:
                sentiment = -sentiment
        elif clean_word in NEGATIVE_WORDS:
            sentiment = -1 * intensity_modifier
            if negation_active:
                sentiment = -sentiment

        if sentiment != 0:
            word_sentiments.append({
                "word": clean_word,
                "score": sentiment,
                "negated": negation_active,
                "intensified": intensity_modifier != 1.0
            })

            if sentiment > 0:
                positive_count += sentiment
            else:
                negative_count += abs(sentiment)

        # Reset modifiers
        intensity_modifier = 1.0
        negation_active = False

    # Calculate final scores
    total = positive_count + negative_count
    if total > 0:
        positive_score = positive_count / total
        negative_score = negative_count / total
    else:
        positive_score = 0.0
        negative_score = 0.0

    neutral_score = 1.0 - (positive_score + negative_score)
    neutral_score = max(0, min(1, neutral_score))

    # Compound score (-1 to 1)
    compound = (positive_count - negative_count) / (total + 1)
    compound = max(-1, min(1, compound))

    # Determine dominant sentiment
    if compound > 0.1:
        dominant = "positive"
    elif compound < -0.1:
        dominant = "negative"
    else:
        dominant = "neutral"

    # Analyze sentences
    sentence_sentiments = []
    for sentence in sentences[:10]:  # Limit to 10 sentences
        sent_result = _analyze_sentence_sentiment(sentence)
        sentence_sentiments.append(sent_result)

    return {
        "algorithm": "sentiment_analysis",
        "text_length": len(text),
        "word_count": len(words),
        "scores": {
            "positive": round(positive_score, 3),
            "negative": round(negative_score, 3),
            "neutral": round(neutral_score, 3),
            "compound": round(compound, 3)
        },
        "dominant_sentiment": dominant,
        "sentiment_words": word_sentiments[:20],
        "positive_words_found": [w["word"] for w in word_sentiments if w["score"] > 0][:10],
        "negative_words_found": [w["word"] for w in word_sentiments if w["score"] < 0][:10],
        "sentence_analysis": sentence_sentiments,
        "confidence": min(0.95, 0.5 + len(word_sentiments) * 0.05)
    }


def template_fill(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Fill a template with values.

    Args:
        task: Template string or description
        context: Should contain 'template' and 'values' dict

    Returns:
        Dict with filled template and metadata
    """
    context = context or {}

    template_str = context.get('template', task)
    values = context.get('values', {})

    # Create Template object
    template = Template(template=template_str)

    # Track what we fill
    filled_vars = []
    missing_vars = []
    used_defaults = []

    result = template_str

    for var in template.variables:
        placeholder = '{' + var + '}'

        if var in values:
            # Use provided value
            value = str(values[var])
            result = result.replace(placeholder, value)
            filled_vars.append({"variable": var, "value": value})
        elif var in template.defaults:
            # Use default
            value = template.defaults[var]
            result = result.replace(placeholder, value)
            used_defaults.append({"variable": var, "default": value})
        else:
            # Variable not filled
            missing_vars.append(var)

    # Calculate fill rate
    total_vars = len(template.variables)
    filled_count = len(filled_vars) + len(used_defaults)
    fill_rate = filled_count / total_vars if total_vars > 0 else 1.0

    return {
        "algorithm": "template_fill",
        "original_template": template_str,
        "filled_result": result,
        "variables_found": template.variables,
        "variables_filled": [f["variable"] for f in filled_vars],
        "defaults_used": [d["variable"] for d in used_defaults],
        "missing_variables": missing_vars,
        "fill_rate": fill_rate,
        "is_complete": len(missing_vars) == 0,
        "details": {
            "filled": filled_vars,
            "defaults": used_defaults
        }
    }


# Helper functions

def _tokenize(text: str) -> List[str]:
    """Tokenize text into words."""
    # Convert to lowercase and extract words
    words = re.findall(r'\b[a-z]+\b', text.lower())

    # Remove stopwords
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how'
    }

    return [w for w in words if w not in stopwords and len(w) > 2]


def _split_sentences(text: str) -> List[str]:
    """Split text into sentences."""
    # Simple sentence splitting
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]


def _analyze_sentence_sentiment(sentence: str) -> Dict:
    """Analyze sentiment of a single sentence."""
    words = sentence.lower().split()

    pos = sum(1 for w in words if re.sub(r'[^\w]', '', w) in POSITIVE_WORDS)
    neg = sum(1 for w in words if re.sub(r'[^\w]', '', w) in NEGATIVE_WORDS)

    if pos > neg:
        sentiment = "positive"
    elif neg > pos:
        sentiment = "negative"
    else:
        sentiment = "neutral"

    return {
        "sentence": sentence[:100],
        "sentiment": sentiment,
        "positive_count": pos,
        "negative_count": neg
    }


class CommunicationEngine:
    """
    High-level interface for communication algorithms.

    Usage:
        engine = CommunicationEngine()
        keywords = engine.extract_keywords(text)
        sentiment = engine.analyze_sentiment(text)
        filled = engine.fill_template(template, values)
    """

    def __init__(self):
        self.algorithms = {
            "tf_idf": tf_idf,
            "sentiment": sentiment_analysis,
            "template": template_fill
        }
        self.templates: Dict[str, Template] = {}

    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text."""
        result = tf_idf("", {"documents": [text]})
        return result.get("keywords", [])[:top_n]

    def analyze_sentiment(self, text: str) -> SentimentScore:
        """Analyze sentiment and return structured score."""
        result = sentiment_analysis("", {"text": text})
        scores = result["scores"]

        return SentimentScore(
            positive=scores["positive"],
            negative=scores["negative"],
            neutral=scores["neutral"],
            compound=scores["compound"],
            dominant=result["dominant_sentiment"]
        )

    def fill_template(self, template: str, values: Dict[str, str]) -> str:
        """Fill a template with values and return result."""
        result = template_fill("", {"template": template, "values": values})
        return result["filled_result"]

    def register_template(self, name: str, template: str, defaults: Dict = None):
        """Register a reusable template."""
        self.templates[name] = Template(
            template=template,
            defaults=defaults or {}
        )

    def use_template(self, name: str, values: Dict[str, str]) -> str:
        """Use a registered template."""
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")

        template = self.templates[name]
        result = template_fill("", {
            "template": template.template,
            "values": {**template.defaults, **values}
        })
        return result["filled_result"]

    def summarize_document(self, text: str) -> Dict:
        """Create a summary with keywords and sentiment."""
        keywords = self.extract_keywords(text)
        sentiment = self.analyze_sentiment(text)

        return {
            "keywords": keywords,
            "sentiment": sentiment.dominant,
            "compound_score": sentiment.compound,
            "word_count": len(text.split())
        }


# Convenience functions

def quick_keywords(text: str) -> List[str]:
    """Quick helper to extract keywords."""
    engine = CommunicationEngine()
    return engine.extract_keywords(text)


def quick_sentiment(text: str) -> str:
    """Quick helper to get dominant sentiment."""
    engine = CommunicationEngine()
    return engine.analyze_sentiment(text).dominant


def quick_fill(template: str, **values) -> str:
    """Quick helper to fill a template."""
    engine = CommunicationEngine()
    return engine.fill_template(template, values)


if __name__ == "__main__":
    # Demo
    engine = CommunicationEngine()

    # TF-IDF
    print("=== TF-IDF Keywords ===")
    text = """
    Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience. Deep learning is a
    subset of machine learning that uses neural networks.
    """
    keywords = engine.extract_keywords(text)
    print(f"Keywords: {keywords}")

    # Sentiment
    print("\n=== Sentiment Analysis ===")
    texts = [
        "I absolutely love this amazing product! It's fantastic!",
        "This is terrible. I hate it. Worst experience ever.",
        "The meeting is scheduled for tomorrow at 3pm."
    ]
    for t in texts:
        sentiment = engine.analyze_sentiment(t)
        print(f"'{t[:40]}...' -> {sentiment.dominant} ({sentiment.compound:.2f})")

    # Templates
    print("\n=== Template Fill ===")
    template = "Hello {name}, your order #{order_id} will arrive on {date}."
    filled = engine.fill_template(template, {
        "name": "Alice",
        "order_id": "12345",
        "date": "Monday"
    })
    print(f"Template: {template}")
    print(f"Filled:   {filled}")
