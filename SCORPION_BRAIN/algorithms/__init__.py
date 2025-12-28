"""
SCORPION_BRAIN Algorithms Module
================================
Core algorithms used by the AI babies.

Categories:
- Reasoning: Chain of thought, tree of thoughts, Bayesian (MARCUS)
- Building: Cosine similarity, graph search, pattern matching (VULCAN)
- Communication: TF-IDF, sentiment, template fill (HERMES)
- Universal: Embeddings, ChromaDB search, tool calls (ALL)
"""

from .reasoning import (
    chain_of_thought,
    tree_of_thoughts,
    bayesian_reasoning,
    ReasoningEngine
)

from .building import (
    cosine_similarity,
    graph_bfs,
    graph_dfs,
    pattern_match,
    BuildingEngine
)

from .communication import (
    tf_idf,
    sentiment_analysis,
    template_fill,
    CommunicationEngine
)

from .universal import (
    generate_embeddings,
    chromadb_search,
    tool_call,
    UniversalEngine
)

__all__ = [
    # Reasoning
    'chain_of_thought',
    'tree_of_thoughts',
    'bayesian_reasoning',
    'ReasoningEngine',
    # Building
    'cosine_similarity',
    'graph_bfs',
    'graph_dfs',
    'pattern_match',
    'BuildingEngine',
    # Communication
    'tf_idf',
    'sentiment_analysis',
    'template_fill',
    'CommunicationEngine',
    # Universal
    'generate_embeddings',
    'chromadb_search',
    'tool_call',
    'UniversalEngine',
]
