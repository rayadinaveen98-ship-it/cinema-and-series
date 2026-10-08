"""P2.3 read-only artwork source adapter contracts.

Adapters normalize external artwork candidates. They never publish assets.
Any candidate intended for production must carry asset-level rights evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


ADAPTER_VERSIONS = {"wikimedia_commons": "wikimedia_commons_v1", "internet_archive": "internet_archive_v1"}


SourceKey = Literal["wikimedia_commons", "internet_archive"]
ArtworkRole = Literal["POSTER", "BACKDROP", "LOGO", "THUMBNAIL"]


@dataclass(frozen=True)
class ArtworkCandidate:
    source_key: SourceKey
    source_asset_id: str
    source_page_url: str
    delivery_url: str
    role: ArtworkRole
    attribution: str | None
    license_identifier: str | None
    rights_evidence_url: str | None
    language: str | None
    territory: str | None
    width: int | None
    height: int | None
    discovered_at: str

    @property
    def aspect_ratio(self) -> float | None:
        if not self.width or not self.height or self.width <= 0 or self.height <= 0:
            return None
        return self.width / self.height


ALLOWED_HOSTS = {
    "wikimedia_commons": {"commons.wikimedia.org"},
    "internet_archive": {"archive.org", "www.archive.org"},
}


def validate_candidate(candidate: ArtworkCandidate) -> None:
    """Fail closed on source identity, URLs, and missing rights evidence."""
    if not candidate.source_asset_id.strip():
        raise ValueError("source_asset_id is required")
    if candidate.source_key not in ALLOWED_HOSTS or ADAPTER_VERSIONS.get(candidate.source_key) is None:
        raise ValueError("unsupported source")
    for field_name, url in (
        ("source_page_url", candidate.source_page_url),
        ("delivery_url", candidate.delivery_url),
    ):
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS[candidate.source_key]:
            raise ValueError(f"{field_name} is outside the source allowlist")
    if not candidate.license_identifier or not candidate.rights_evidence_url:
        raise ValueError("asset-level license and rights evidence are required")
    evidence = urlparse(candidate.rights_evidence_url)
    if evidence.scheme != "https":
        raise ValueError("rights evidence URL must use HTTPS")



def can_publish_candidate(
    candidate: ArtworkCandidate,
    *,
    source_review_status: str,
    source_enabled_for_publication: bool,
) -> bool:
    """Return True only when source policy and asset rights are both approved."""
    validate_candidate(candidate)
    return source_review_status == "APPROVED" and source_enabled_for_publication


def normalize_candidate(raw: dict, *, source_key: SourceKey) -> ArtworkCandidate:
    """Normalize adapter output deterministically; does not fetch or publish."""
    candidate = ArtworkCandidate(
        source_key=source_key,
        source_asset_id=str(raw.get("source_asset_id", "")).strip(),
        source_page_url=str(raw.get("source_page_url", "")).strip(),
        delivery_url=str(raw.get("delivery_url", "")).strip(),
        role=raw.get("role", "POSTER"),
        attribution=(str(raw["attribution"]).strip() if raw.get("attribution") else None),
        license_identifier=(str(raw["license_identifier"]).strip() if raw.get("license_identifier") else None),
        rights_evidence_url=(str(raw["rights_evidence_url"]).strip() if raw.get("rights_evidence_url") else None),
        language=(str(raw["language"]).strip() if raw.get("language") else None),
        territory=(str(raw["territory"]).strip() if raw.get("territory") else None),
        width=int(raw["width"]) if raw.get("width") is not None else None,
        height=int(raw["height"]) if raw.get("height") is not None else None,
        discovered_at=str(raw.get("discovered_at", "")).strip(),
    )
    validate_candidate(candidate)
    return candidate
