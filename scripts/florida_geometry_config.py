"""Configuration for official Florida district geometry source files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from election_db import ROOT_DIR


SOURCE_NAME = "Florida Legislature Office of Economic and Demographic Research"
SOURCE_HOMEPAGE = "https://edr.state.fl.us/content/redistricting/2020redistricting/index.cfm"
DISCOVERY_URL = SOURCE_HOMEPAGE
BASE_URL = "https://edr.state.fl.us/content/redistricting/2020redistricting"
RAW_DIR = ROOT_DIR / "data/raw/florida/geometry/2022"


@dataclass(frozen=True)
class FloridaGeometryLayer:
    layer_key: str
    geo_type: str
    name: str
    official_plan_id: str
    shapefile_name: str
    block_equivalency_name: str
    valid_from: int
    valid_to: int | None
    expected_features: int
    id_field: str
    label_field: str
    district_label_prefix: str
    notes: str

    @property
    def shapefile_url(self) -> str:
        return f"{BASE_URL}/{self.shapefile_name}"

    @property
    def block_equivalency_url(self) -> str:
        return f"{BASE_URL}/{self.block_equivalency_name}"

    @property
    def shapefile_path(self) -> Path:
        return RAW_DIR / self.shapefile_name

    @property
    def block_equivalency_path(self) -> Path:
        return RAW_DIR / self.block_equivalency_name


FLORIDA_GEOMETRY_LAYERS: dict[str, FloridaGeometryLayer] = {
    "fl-2022-congressional-districts": FloridaGeometryLayer(
        layer_key="fl-2022-congressional-districts",
        geo_type="congressional_district",
        name="Florida 2022 congressional districts",
        official_plan_id="P000C0109",
        shapefile_name="P000C0109.zip",
        block_equivalency_name="P000C0109.txt",
        valid_from=2022,
        valid_to=None,
        expected_features=28,
        id_field="DISTRICT",
        label_field="DISTRICT",
        district_label_prefix="District",
        notes="Final congressional district plan enacted for the 2022 redistricting cycle.",
    ),
    "fl-2022-state-house-districts": FloridaGeometryLayer(
        layer_key="fl-2022-state-house-districts",
        geo_type="state_house_district",
        name="Florida 2022 State House districts",
        official_plan_id="H000H8013",
        shapefile_name="H000H8013.zip",
        block_equivalency_name="H000H8013.txt",
        valid_from=2022,
        valid_to=None,
        expected_features=120,
        id_field="DISTRICT",
        label_field="DISTRICT",
        district_label_prefix="District",
        notes="Final State House district plan enacted for the 2022 redistricting cycle.",
    ),
    "fl-2022-state-senate-districts": FloridaGeometryLayer(
        layer_key="fl-2022-state-senate-districts",
        geo_type="state_senate_district",
        name="Florida 2022 State Senate districts",
        official_plan_id="S027S8058",
        shapefile_name="S027S8058.zip",
        block_equivalency_name="S027S8058.txt",
        valid_from=2022,
        valid_to=None,
        expected_features=40,
        id_field="DISTRICT",
        label_field="DISTRICT",
        district_label_prefix="District",
        notes="Final State Senate district plan enacted for the 2022 redistricting cycle.",
    ),
}


def selected_layers(layer_key: str | None, all_layers: bool) -> list[FloridaGeometryLayer]:
    if all_layers:
        return [FLORIDA_GEOMETRY_LAYERS[key] for key in sorted(FLORIDA_GEOMETRY_LAYERS)]
    if layer_key is None:
        layer_key = "fl-2022-congressional-districts"
    try:
        return [FLORIDA_GEOMETRY_LAYERS[layer_key]]
    except KeyError as exc:
        supported = ", ".join(sorted(FLORIDA_GEOMETRY_LAYERS))
        raise ValueError(f"Unsupported Florida geometry layer {layer_key!r}. Supported layers: {supported}.") from exc
