"""Clients package for external API integrations.

Primary AI provider: OpenAI (GPT-4o, text-embedding-3-small)
Legacy providers moved to clients/legacy/
"""
from .openai_client import openai_client, OpenAIClient
from .supabase_client import supabase_client, SupabaseClient
from .qdrant_client import qdrant_client, ZyanaQdrantClient

__all__ = [
    "openai_client",
    "OpenAIClient",
    "supabase_client",
    "SupabaseClient",
    "qdrant_client",
    "ZyanaQdrantClient"
]

