"""Parser for key fields from LAStools lasinfo text reports."""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LasInfoSummary:
    total_points: int | None = None
    ground_points: int | None = None
    unclassified_points: int | None = None
    crs: str | None = None


def parse_lasinfo(text):
    total = None
    ground = None
    unclassified = None
    crs = None

    m = re.search(r"number of point records:\s*(\d+)", text)
    if m:
        total = int(m.group(1))

    m = re.search(r"^\s*(\d+)\s+ground \(2\)\s*$", text, flags=re.MULTILINE)
    if m:
        ground = int(m.group(1))

    m = re.search(r"^\s*(\d+)\s+unclassified \(1\)\s*$", text, flags=re.MULTILINE)
    if m:
        unclassified = int(m.group(1))

    m = re.search(r"ProjectedCSTypeGeoKey:\s*(.+)$", text, flags=re.MULTILINE)
    if m:
        crs = m.group(1).strip()

    return LasInfoSummary(total, ground, unclassified, crs)
