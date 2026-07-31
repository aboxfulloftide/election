"""Configuration for official California district geometry source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from election_db import ROOT_DIR


SOURCE_NAME = "California Citizens Redistricting Commission"
SOURCE_HOMEPAGE = "https://wedrawthelines.ca.gov/final-maps/"
RAW_DIR = ROOT_DIR / "data/raw/official/california/geometry"


@dataclass(frozen=True)
class CaliforniaGeometryLayer:
    layer_key: str
    geo_type: str
    office: str
    name: str
    source_url: str
    file_name: str
    valid_from: int
    valid_to: int | None
    expected_features: int
    district_label_suffix: str
    notes: str

    @property
    def raw_path(self) -> Path:
        return RAW_DIR / self.file_name


CALIFORNIA_GEOMETRY_LAYERS: dict[str, CaliforniaGeometryLayer] = {
    "ca-2022-congressional-districts": CaliforniaGeometryLayer(
        layer_key="ca-2022-congressional-districts",
        geo_type="congressional_district",
        office="U.S. House",
        name="California 2022 congressional districts",
        source_url="https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-2.zip",
        file_name="congressional-final-shapefile.zip",
        valid_from=2022,
        valid_to=None,
        expected_features=52,
        district_label_suffix="Congressional District",
        notes="Final approved congressional districts by the 2020 California Citizens Redistricting Commission.",
    ),
    "ca-2022-state-senate-districts": CaliforniaGeometryLayer(
        layer_key="ca-2022-state-senate-districts",
        geo_type="state_senate_district",
        office="State Senate",
        name="California 2022 State Senate districts",
        source_url="https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-3.zip",
        file_name="state-senate-final-shapefile.zip",
        valid_from=2022,
        valid_to=None,
        expected_features=40,
        district_label_suffix="State Senate District",
        notes="Final approved State Senate districts by the 2020 California Citizens Redistricting Commission; Senate districts phase in over two election cycles.",
    ),
    "ca-2022-state-assembly-districts": CaliforniaGeometryLayer(
        layer_key="ca-2022-state-assembly-districts",
        geo_type="state_assembly_district",
        office="State Assembly",
        name="California 2022 State Assembly districts",
        source_url="https://wedrawthelines.ca.gov/wp-content/uploads/sites/64/2023/01/OneDrive_2023-01-19-5.zip",
        file_name="state-assembly-final-shapefile.zip",
        valid_from=2022,
        valid_to=None,
        expected_features=80,
        district_label_suffix="Assembly District",
        notes="Final approved State Assembly districts by the 2020 California Citizens Redistricting Commission.",
    ),
}


def selected_layers(layer_key: str | None, all_layers: bool) -> list[CaliforniaGeometryLayer]:
    if all_layers:
        return [CALIFORNIA_GEOMETRY_LAYERS[key] for key in sorted(CALIFORNIA_GEOMETRY_LAYERS)]
    if layer_key is None:
        layer_key = "ca-2022-congressional-districts"
    try:
        return [CALIFORNIA_GEOMETRY_LAYERS[layer_key]]
    except KeyError as exc:
        supported = ", ".join(sorted(CALIFORNIA_GEOMETRY_LAYERS))
        raise ValueError(f"Unsupported California geometry layer {layer_key!r}. Supported layers: {supported}.") from exc
