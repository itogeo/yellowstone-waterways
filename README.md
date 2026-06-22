# Yellowstone River Paddling Inventory

A digital recreation of the **YGTNP River Paddling Inventory** map — all waterways in Yellowstone National Park classified by paddling access and management priority.

## What This Is

The source map (see `images/`) was printed by the park and classifies every river and stream into one of five categories:

| Color  | Classification |
|--------|---------------|
| Orange | Park boundary |
| Green  | Open to paddling |
| Blue   | Priority 1 — closed, few known issues |
| Cyan   | Priority 2 — closed, some known issues |
| Yellow | Priority 3 — recommend continued closure |
| Red    | Hiking trails |

This project builds a web map that replicates that classification system with live, queryable data.

## Project Structure

```
yellowstone/
├── README.md         — this file
├── GOALS.md          — goals tracker and phase checklist
├── images/           — reference photos of the original printed map
├── data/             — raw + processed geodata
│   ├── ynp_boundary.geojson
│   └── waterways.geojson
└── src/
    └── download_data.py   — fetches OSM data via Overpass API
```

## Data Sources

- **Park boundary**: OpenStreetMap relation 1453306 (Yellowstone NP) via Overpass API
- **Waterways**: OSM `waterway=*` tags within YNP bounding box via Overpass API
- **Classification**: Will be applied manually or from NPS source data in a later phase

## Quickstart

```bash
# Download base data
/Users/ianvandusen/anaconda3/envs/geodata/bin/python src/download_data.py
```
