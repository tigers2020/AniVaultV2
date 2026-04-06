"""test_sql_queries_group_tmdb_match_upsert.py

GROUP_TMDB_MATCH_UPSERT_SQL 단일 출처(import) 검증 테스트.

Author: Pom Kim
"""

from anivault.adapters.persistence.sqlite.sql_queries import GROUP_TMDB_MATCH_UPSERT_SQL
from anivault.adapters.persistence.sqlite.sqlite_title_group_repository import (
    GROUP_TMDB_MATCH_UPSERT_SQL as GROUP_REPO_GROUP_TMDB_MATCH_UPSERT_SQL,
)
from anivault.adapters.persistence.sqlite.sqlite_title_match_repository import (
    GROUP_TMDB_MATCH_UPSERT_SQL as MATCH_REPO_GROUP_TMDB_MATCH_UPSERT_SQL,
)


def test_group_tmdb_match_upsert_sql_is_single_source_of_truth() -> None:
    """두 저장소가 동일 SQL 상수 객체를 참조하는지 검증한다.

    Args:
        없음.

    Returns:
        None.
    """
    assert GROUP_REPO_GROUP_TMDB_MATCH_UPSERT_SQL is GROUP_TMDB_MATCH_UPSERT_SQL
    assert MATCH_REPO_GROUP_TMDB_MATCH_UPSERT_SQL is GROUP_TMDB_MATCH_UPSERT_SQL

