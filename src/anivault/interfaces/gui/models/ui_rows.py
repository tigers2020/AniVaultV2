"""ui_rows.py

파이프라인 표시용 행 타입. Qt 모델만 소비한다.

Author: Pom Kim
"""

from collections import OrderedDict
from dataclasses import dataclass, field


@dataclass
class PipelineRow:
    """파이프라인 테이블 한 파일 행. 테이블·포스터·operations 공통."""

    original_file: str
    parsed_title: str
    parse_group: str
    tmdb_korean_title_group: str
    tmdb_series_id: str
    tmdb_poster_path: str
    tmdb_backdrop_path: str
    year: str
    season: str
    resolution: str
    status: str
    poster_url: str
    backdrop_url: str
    target_path: str


def _aggregate_str(members: tuple[PipelineRow, ...], attr: str, *, mixed: str = "—") -> str:
    """멤버들의 속성 값이 모두 같으면 그 값, 여러 개면 mixed 표기를 반환한다.

    Args:
        members: 그룹 멤버 튜플.
        attr: PipelineRow 필드 이름.
        mixed: 값이 여러 개일 때 쓸 문자열.

    Returns:
        공통 값, 빈 집합이면 빈 문자열.
    """
    vals = {(getattr(m, attr) or "").strip() for m in members}
    vals.discard("")
    if not vals:
        return ""
    if len(vals) == 1:
        return next(iter(vals))
    return mixed


def _aggregate_resolution(members: tuple[PipelineRow, ...]) -> str:
    """그룹 멤버에서 표시용 해상도 문자열을 한 번만 계산한다.

    Args:
        members: 같은 파싱 제목 그룹의 파일 행.

    Returns:
        단일 해상도, 슬래시 구분 복수값, 또는 빈 문자열.
    """
    vals = sorted({(m.resolution or "").strip() for m in members} - {""})
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0]
    return " / ".join(vals)


@dataclass(frozen=True)
class PipelineGroupRow:
    """같은 표시 그룹 키(파싱 제목)를 가진 파일 묶음."""

    members: tuple[PipelineRow, ...]
    _resolution_cached: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """멤버 검증 후 해상도 표시 문자열을 캐시한다.

        Args:
            self: 이 그룹 행.

        Returns:
            None.

        Raises:
            ValueError: members가 비어 있을 때.
        """
        if not self.members:
            raise ValueError("PipelineGroupRow requires at least one member")
        object.__setattr__(self, "_resolution_cached", _aggregate_resolution(self.members))

    @property
    def original_file(self) -> str:
        """단일 멤버면 경로, 복수면 'N개 파일' 형태.

        Args:
            self: 이 그룹 행.

        Returns:
            표시용 문자열.
        """
        if len(self.members) == 1:
            return self.members[0].original_file
        return f"{len(self.members)}개 파일"

    @property
    def parsed_title(self) -> str:
        """parsed_title 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "parsed_title")

    @property
    def parse_group(self) -> str:
        """parse_group 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "parse_group")

    @property
    def tmdb_korean_title_group(self) -> str:
        """TMDB 한글 그룹 제목 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "tmdb_korean_title_group")

    @property
    def year(self) -> str:
        """연도 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "year")

    @property
    def season(self) -> str:
        """시즌 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "season")

    @property
    def resolution(self) -> str:
        """파일별 해상도가 다르면 ' / '로 이어 붙인다.

        Args:
            self: 이 그룹 행.

        Returns:
            단일 또는 결합 문자열.
        """
        return self._resolution_cached

    @property
    def status(self) -> str:
        """상태 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "status")

    @property
    def poster_url(self) -> str:
        """비어 있지 않은 첫 poster_url.

        Args:
            self: 이 그룹 행.

        Returns:
            URL 또는 빈 문자열.
        """
        for m in self.members:
            if (m.poster_url or "").strip():
                return m.poster_url
        return ""

    @property
    def backdrop_url(self) -> str:
        """비어 있지 않은 첫 backdrop_url.

        Args:
            self: 이 그룹 행.

        Returns:
            URL 또는 빈 문자열.
        """
        for m in self.members:
            if (m.backdrop_url or "").strip():
                return m.backdrop_url
        return ""

    @property
    def target_path(self) -> str:
        """대상 경로 집계.

        Args:
            self: 이 그룹 행.

        Returns:
            공통 또는 mixed.
        """
        return _aggregate_str(self.members, "target_path")

    def representative(self) -> PipelineRow:
        """썸네일·폴백용 대표 행(경로 정렬 첫 멤버).

        Args:
            self: 이 그룹 행.

        Returns:
            PipelineRow.
        """
        return self.members[0]


def _pipeline_row_group_key(row: PipelineRow) -> str:
    """표시 그룹 버킷 키. TMDB ID가 있으면 그걸 우선한다.

    Args:
        row: 파이프라인 파일 행.

    Returns:
        버킷 키 문자열.
    """
    tid = (row.tmdb_series_id or "").strip()
    if tid:
        return f"tmdb:{tid}"
    pt = (row.parsed_title or "").strip()
    if pt:
        return pt
    return row.original_file


def group_pipeline_rows(rows: list[PipelineRow]) -> list[PipelineGroupRow]:
    """TMDB 시리즈 ID(있으면) 또는 parsed_title(빈 경우 original_file)로 그룹화한다.

    Args:
        rows: 파일 행 목록.

    Returns:
        PipelineGroupRow 목록(삽입 순서 유지).
    """
    buckets: OrderedDict[str, list[PipelineRow]] = OrderedDict()
    for r in rows:
        key = _pipeline_row_group_key(r)
        buckets.setdefault(key, []).append(r)
    out: list[PipelineGroupRow] = []
    for members in buckets.values():
        sorted_members = tuple(sorted(members, key=lambda x: x.original_file))
        out.append(PipelineGroupRow(members=sorted_members))
    return out
