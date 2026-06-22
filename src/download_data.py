"""
Download boundaries + waterways + trails for:
  - Yellowstone National Park
  - John D. Rockefeller Jr. Memorial Parkway
  - Grand Teton National Park

Data source: OpenStreetMap via Overpass API.
Saves GeoJSON files to data/.

Usage:
    /Users/ianvandusen/anaconda3/envs/geodata/bin/python src/download_data.py
"""

import json
import time
import requests
from pathlib import Path
from shapely.geometry import LineString, mapping
from shapely.ops import linemerge, unary_union

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Combined bbox covering YNP + Rockefeller Parkway + Grand Teton NP
# (south, west, north, east)
COMBINED_BBOX = "43.35,-111.25,45.15,-109.75"


HEADERS = {"User-Agent": "YellowstoneWaterwayMapper/1.0 (itogeospatial@gmail.com)"}


def overpass_post(query: str, timeout: int = 240) -> dict:
    print("  Querying Overpass API...")
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=timeout, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def extract_outer_polygon(relation_el: dict, name: str, osm_id: int) -> dict | None:
    """Convert a relation element's outer members into a GeoJSON polygon feature."""
    outer_lines = []
    for member in relation_el.get("members", []):
        if member.get("role") == "outer" and "geometry" in member:
            coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
            if len(coords) >= 2:
                outer_lines.append(LineString(coords))
    if not outer_lines:
        return None
    merged = linemerge(outer_lines)
    try:
        polygon = unary_union([merged]).convex_hull
    except Exception:
        polygon = merged
    return {
        "type": "Feature",
        "geometry": mapping(polygon),
        "properties": {"name": name, "osm_id": osm_id},
    }


def download_one_boundary(selector: str, label: str) -> dict | None:
    """Fetch a single relation by selector and return a GeoJSON feature."""
    query = f"[out:json][timeout:120];\n{selector};\nout geom;"
    data = overpass_post(query)
    for el in data.get("elements", []):
        if el.get("type") != "relation":
            continue
        name = el.get("tags", {}).get("name", label)
        feature = extract_outer_polygon(el, name, el["id"])
        if feature:
            print(f"    + {name} (relation {el['id']})")
            return feature
    print(f"  WARNING: no data returned for {label}")
    return None


def download_boundaries() -> None:
    """Download park boundaries for all three units from OSM, one at a time."""
    parks = [
        ('relation(1453306)', "Yellowstone NP"),
        ('relation["boundary"="national_park"]["name"="Grand Teton National Park"]', "Grand Teton NP"),
        ('relation["name"="John D. Rockefeller, Jr. Memorial Parkway"]', "Rockefeller Parkway"),
    ]

    features = []
    for selector, label in parks:
        print(f"  Fetching {label}...")
        feature = download_one_boundary(selector, label)
        if feature:
            features.append(feature)
        time.sleep(2)

    if not features:
        print("  WARNING: no boundary data returned")
        return

    fc = {"type": "FeatureCollection", "features": features}
    out_path = DATA_DIR / "boundaries.geojson"
    with open(out_path, "w") as f:
        json.dump(fc, f, indent=2)
    print(f"  Saved {len(features)} park boundaries → {out_path}")


def download_waterways() -> None:
    """Download all waterways within the combined bounding box."""
    query = f"""
[out:json][timeout:180];
(
  way["waterway"]({COMBINED_BBOX});
);
out geom;
"""
    data = overpass_post(query)
    elements = data.get("elements", [])

    features = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        props = dict(el.get("tags", {}))
        props["osm_id"] = el["id"]
        props["paddling_status"] = None  # filled in by classify.py or web app
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": props,
        })

    fc = {"type": "FeatureCollection", "features": features}
    out_path = DATA_DIR / "waterways.geojson"
    with open(out_path, "w") as f:
        json.dump(fc, f, indent=2)
    print(f"  Saved {len(features)} waterway features → {out_path}")


def download_trails() -> None:
    """Download hiking trails within the combined bounding box."""
    query = f"""
[out:json][timeout:180];
(
  way["highway"="path"]({COMBINED_BBOX});
  way["highway"="footway"]({COMBINED_BBOX});
);
out geom;
"""
    data = overpass_post(query)
    elements = data.get("elements", [])

    features = []
    for el in elements:
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(pt["lon"], pt["lat"]) for pt in el["geometry"]]
        if len(coords) < 2:
            continue
        props = dict(el.get("tags", {}))
        props["osm_id"] = el["id"]
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": coords},
            "properties": props,
        })

    fc = {"type": "FeatureCollection", "features": features}
    out_path = DATA_DIR / "trails.geojson"
    with open(out_path, "w") as f:
        json.dump(fc, f, indent=2)
    print(f"  Saved {len(features)} trail features → {out_path}")


if __name__ == "__main__":
    print("=== Greater Yellowstone Ecosystem Data Download ===\n")

    print("1/3 Downloading park boundaries (YNP + Rockefeller Parkway + Grand Teton)...")
    download_boundaries()
    time.sleep(3)

    print("\n2/3 Downloading waterways...")
    download_waterways()
    time.sleep(3)

    print("\n3/3 Downloading hiking trails...")
    download_trails()

    print("\nDone. Files in data/:")
    for f in sorted(DATA_DIR.iterdir()):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name}  ({size_kb:.0f} KB)")
