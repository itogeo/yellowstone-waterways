"""
Re-download park boundaries (with correct polygon reconstruction) + major roads.
Run this after download_data.py.

Usage:
    /Users/ianvandusen/anaconda3/envs/geodata/bin/python src/download_extras.py
"""

import json
import time
import requests
from pathlib import Path
from shapely.geometry import LineString, mapping
from shapely.ops import linemerge, polygonize, unary_union

DATA_DIR = Path(__file__).parent.parent / "data"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
HEADERS = {"User-Agent": "YellowstoneWaterwayMapper/1.0 (itogeospatial@gmail.com)"}
COMBINED_BBOX = "43.35,-111.25,45.15,-109.75"


def overpass_post(query: str, timeout: int = 180) -> dict:
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=timeout, headers=HEADERS)
    resp.raise_for_status()
    return resp.json()


def relation_to_polygon(el: dict) -> object | None:
    """Convert a relation's outer members to a proper shapely polygon using polygonize."""
    outer_lines = []
    for member in el.get("members", []):
        if member.get("role") == "outer" and "geometry" in member:
            coords = [(pt["lon"], pt["lat"]) for pt in member["geometry"]]
            if len(coords) >= 2:
                outer_lines.append(LineString(coords))
    if not outer_lines:
        return None
    merged = linemerge(outer_lines)
    polys = list(polygonize(merged))
    if polys:
        return max(polys, key=lambda p: p.area)
    # fallback: buffer the merged lines slightly to close small gaps
    polys = list(polygonize(unary_union(outer_lines)))
    if polys:
        return max(polys, key=lambda p: p.area)
    return None


def download_boundaries() -> None:
    parks = [
        ("Yellowstone NP",       'relation(1453306)'),
        ("Grand Teton NP",       'relation["name"="Grand Teton National Park"]["boundary"="national_park"]'),
        ("Rockefeller Parkway",  'relation["name"="John D. Rockefeller, Jr. Memorial Parkway"]'),
    ]

    features = []
    for label, selector in parks:
        print(f"  Fetching {label}...")
        query = f"[out:json][timeout:120];\n{selector};\nout geom;"
        data = overpass_post(query)
        found = False
        for el in data.get("elements", []):
            if el.get("type") != "relation":
                continue
            name = el.get("tags", {}).get("name", label)
            poly = relation_to_polygon(el)
            if poly:
                features.append({
                    "type": "Feature",
                    "geometry": mapping(poly),
                    "properties": {"name": name, "osm_id": el["id"]},
                })
                print(f"    ✓ {name}  (relation {el['id']}, {poly.geom_type})")
                found = True
                break
        if not found:
            # Try searching by name only (no boundary filter)
            print(f"    Retrying {label} without boundary filter...")
            fallback_selectors = {
                "Grand Teton NP": 'relation["name"="Grand Teton National Park"]',
            }
            fb = fallback_selectors.get(label)
            if fb:
                data2 = overpass_post(f"[out:json][timeout:120];\n{fb};\nout geom;")
                for el in data2.get("elements", []):
                    if el.get("type") != "relation":
                        continue
                    name = el.get("tags", {}).get("name", label)
                    poly = relation_to_polygon(el)
                    if poly:
                        features.append({
                            "type": "Feature",
                            "geometry": mapping(poly),
                            "properties": {"name": name, "osm_id": el["id"]},
                        })
                        print(f"    ✓ {name}  (relation {el['id']}, fallback)")
                        break
                else:
                    print(f"    ✗ No data for {label}")
        time.sleep(2)

    out = DATA_DIR / "boundaries.geojson"
    with open(out, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
    print(f"\n  Saved {len(features)} boundaries → {out}")


def download_roads() -> None:
    print("\n  Fetching major roads...")
    query = f"""
[out:json][timeout:120];
(
  way["highway"="primary"]({COMBINED_BBOX});
  way["highway"="secondary"]({COMBINED_BBOX});
  way["highway"="trunk"]({COMBINED_BBOX});
);
out geom;
"""
    data = overpass_post(query)
    features = []
    for el in data.get("elements", []):
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
    out = DATA_DIR / "roads.geojson"
    with open(out, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f)
    print(f"  Saved {len(features)} road features → {out}")


if __name__ == "__main__":
    print("=== Downloading boundaries + roads ===\n")
    download_boundaries()
    download_roads()
    print("\nDone.")
