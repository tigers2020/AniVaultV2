"""Shared public contracts used across multiple AniVault layers."""

from anivault.contracts.library_index import (
    BulkMediaUpsertItem,
    BulkMediaUpsertResult,
    IndexedMediaForParse,
    MediaFileRecord,
)
from anivault.contracts.organize_plan import (
    OrganizeOperationKind,
    OrganizePlanAppendRow,
    OrganizePlanBundle,
    OrganizePlanHeaderRecord,
    OrganizePlanItemRecord,
    OrganizePlanItemStatus,
    OrganizePlanListEntry,
    OrganizePlanStatus,
)
from anivault.contracts.parse import ParseInput, ParseResult
from anivault.contracts.parse_cache import (
    ParseCacheErrorWrite,
    ParseCacheLookup,
    ParseCacheOkWrite,
)
from anivault.contracts.pipeline import GroupMatchResult, MatchInput, MatchResult, PipelineRow
from anivault.contracts.planning import (
    ApplyInput,
    ApplyResult,
    PlanInput,
    PlanMovePreviewMeta,
    PlanResult,
)
from anivault.contracts.progress import ProgressEvent, progress_dialog_value_and_maximum
from anivault.contracts.scan import ScanInput, ScanResult
from anivault.contracts.title_groups import (
    GroupType,
    MemberRole,
    TitleGroupBundle,
    TitleGroupingRow,
    TitleGroupListRecord,
    TitleGroupMember,
)
from anivault.contracts.title_match import GroupTmdbMatchRecord, MatchStatus
from anivault.contracts.tmdb import SearchTvLibraryRecord, TmdbSearchInput, TmdbSeriesCandidate

__all__ = [
    "ApplyInput",
    "ApplyResult",
    "BulkMediaUpsertItem",
    "BulkMediaUpsertResult",
    "GroupMatchResult",
    "GroupTmdbMatchRecord",
    "GroupType",
    "IndexedMediaForParse",
    "MatchInput",
    "MatchResult",
    "MatchStatus",
    "MediaFileRecord",
    "MemberRole",
    "OrganizeOperationKind",
    "OrganizePlanAppendRow",
    "OrganizePlanBundle",
    "OrganizePlanHeaderRecord",
    "OrganizePlanItemRecord",
    "OrganizePlanItemStatus",
    "OrganizePlanListEntry",
    "OrganizePlanStatus",
    "ParseCacheErrorWrite",
    "ParseCacheLookup",
    "ParseCacheOkWrite",
    "ParseInput",
    "ParseResult",
    "PipelineRow",
    "PlanInput",
    "PlanMovePreviewMeta",
    "PlanResult",
    "ProgressEvent",
    "ScanInput",
    "ScanResult",
    "SearchTvLibraryRecord",
    "TitleGroupBundle",
    "TitleGroupListRecord",
    "TitleGroupMember",
    "TitleGroupingRow",
    "TmdbSearchInput",
    "TmdbSeriesCandidate",
    "progress_dialog_value_and_maximum",
]
