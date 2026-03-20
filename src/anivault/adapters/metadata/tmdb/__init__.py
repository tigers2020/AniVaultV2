"""TMDB adapter: implements MetadataProvider via tmdbapis."""

from anivault.adapters.metadata.tmdb.client import TmdbApiClient
from anivault.adapters.metadata.tmdb.provider import TmdbMetadataProvider

__all__ = ["TmdbApiClient", "TmdbMetadataProvider"]
