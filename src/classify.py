"""
Apply initial paddling_status rankings to waterways.geojson.
Outputs data/waterways_classified.geojson.

Rankings (matching reference map):
  open       - Open to paddling (green)
  priority_1 - Closed, few known issues (blue)
  priority_2 - Closed, some known issues (cyan)
  priority_3 - Recommend continued closure (yellow)
  skip       - Not paddleable (ditches, dams, etc.) — excluded from output

Logic:
  Named rivers/streams are matched by name first, then fall back to type.
  Thermal/geyser drainages → priority_3.
  Unnamed small streams → priority_3.
  Named streams not listed → priority_2 (worth looking at but issues likely).
  Named rivers not listed → priority_1 (probably fine, needs eval).

Usage:
    /Users/ianvandusen/anaconda3/envs/geodata/bin/python src/classify.py
"""

import json
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

NON_PADDLEABLE = {"ditch", "drain", "dam", "weir", "link", "flowline", "canal"}

# Snake River through GTNP is the primary open float corridor.
# Buffalo Fork and Pacific Creek lower sections are also accessible.
OPEN = {
    "Snake River",
    "Pacific Creek",
    "Buffalo Fork",
    "North Buffalo Fork",
    "South Buffalo Fork",
}

# Good river character, minimal documented issues — worth opening with evaluation.
PRIORITY_1 = {
    "Yellowstone River",      # below Grand Canyon of YNP and in Gardner area
    "Lamar River",            # excellent river, wolf country, accessible
    "Slough Creek",           # meadow float, classic YNP
    "Soda Butte Creek",       # good gradient, Lamar Valley tributary
    "Pebble Creek",           # small but clean, northern YNP
    "Bechler River",          # remote SW corner, thermal-free lower sections
    "Fall River",             # Bechler region, strong flow
    "Gallatin River",         # NW YNP, river canyon, well-known floater
    "Gardner River",          # Gardiner area, known whitewater
    "Gardner RIver",          # OSM typo variant
    "Gros Ventre River",      # GTNP, popular float below Slide Lake
    "Spread Creek",           # GTNP, open valley float
    "Flat Creek",             # NWR area south of GTNP
    "Teton River",            # west side of Tetons
    "Teton Creek",
    "Granite Creek",          # south GTNP, canyon float
    "Middle Fork Granite Creek",
    "Death Canyon Creek",     # GTNP, accessible
    "Crystal Creek",
    "Cascade Creek",
    "Clarks Fork Yellowstone River",  # east of YNP, well-known kayak run
    "North Fork Shoshone River",      # east approach corridor
    "Shoshone River",
    "Brooks Lake Creek",
    "Broadwater River",
    "Eagle Creek",
    "Grizzly Creek",
    "Atlantic Creek",
}

# Known issues: thermal proximity, cold spawning runs, access difficulty,
# or sensitive wildlife corridors.
PRIORITY_2 = {
    "Madison River",          # world-class trout fishery — spawning closure concern
    "Firehole River",         # thermal inputs, temperature issues for fish
    "Little Firehole River",  # same drainage, thermal
    "Gibbon River",           # thermal influences, YNP core
    "Lewis River",            # critical lake-trout spawning channel (Lewis→Shoshone)
    "Hellroaring Creek",      # remote, requires suspension bridge crossing
    "Thorofare Creek",        # most remote section of YNP, grizzly core
    "Fan Creek",              # remote NW, difficult access
    "Nez Perce Creek",        # thermal outflow area
    "Alum Creek",             # mineral thermal drainage
    "Arnica Creek",           # near thermal fields
    "Buffalo Creek",
    "Cottonwood Creek",
    "Middle Creek",
    "South Fork Fish Creek",
    "North Fork Fish Creek",
    "Fox Creek",
    "Grinnell Creek",
    "Lake Creek",
    "Mormon Creek",
    "Spring Creek",
    "Stillwater River",
    "Wind River",
    "Green River",
    "Fish Creek",
    "Leigh Canyon",
    "Moran Canyon",
    "Big Elk Creek",
    "Blackrock Creek",
    "Boone Creek",
    "East Rosebud Creek",
    "Fishhawk Creek",
    "Gunbarrel Creek",
    "Kaufmann Creek",
    "North Moran Creek",
}

# Thermal streams, very small drainages, named but clearly non-navigable.
PRIORITY_3 = {
    "Boiling river",          # literally boiling — thermal
    "Black Sand Spring",      # geyser drainage
    "Astringent Creek",       # thermal area
    "Alkali Creek",
    "Alluvium Creek",
    "Amethyst Creek",
    "Big Thumb Creek",        # Yellowstone Lake thermal thumb
}


def classify(feature: dict) -> str:
    props = feature["properties"]
    wtype = props.get("waterway", "")
    name = (props.get("name") or "").strip()

    if wtype in NON_PADDLEABLE:
        return "skip"

    if name in PRIORITY_3:
        return "priority_3"
    if name in OPEN:
        return "open"
    if name in PRIORITY_1:
        return "priority_1"
    if name in PRIORITY_2:
        return "priority_2"

    # Fall-through logic by type + name presence
    if wtype == "river":
        return "priority_1" if name else "priority_2"
    if wtype == "stream":
        return "priority_2" if name else "priority_3"

    return "priority_3"


def main():
    with open(DATA_DIR / "waterways.geojson") as f:
        ww = json.load(f)

    counts = Counter()
    for feat in ww["features"]:
        status = classify(feat)
        feat["properties"]["paddling_status"] = status
        counts[status] += 1

    # Drop non-paddleable features from the output file
    ww["features"] = [f for f in ww["features"] if f["properties"]["paddling_status"] != "skip"]

    out_path = DATA_DIR / "waterways_classified.geojson"
    with open(out_path, "w") as f:
        json.dump(ww, f)

    print("Classification summary:")
    for status in ["open", "priority_1", "priority_2", "priority_3", "skip"]:
        print(f"  {status:12}  {counts[status]:5} features")
    print(f"\nSaved {len(ww['features'])} paddling features → {out_path}")


if __name__ == "__main__":
    main()
