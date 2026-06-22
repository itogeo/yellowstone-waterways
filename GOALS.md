# Yellowstone Paddling Inventory — Goals Tracker

## Phase 0: Data Foundation
- [ ] Download YNP park boundary (OSM relation 1453306)
- [ ] Download all OSM waterways within YNP bbox
- [ ] Validate geometry coverage against reference map
- [ ] Identify any major rivers missing from OSM

## Phase 1: Classification
- [ ] Audit which YNP waterways NPS lists as open to paddling
- [ ] Apply Priority 1 / 2 / 3 closed classification to each segment
- [ ] Decide: manual classification in GeoJSON properties vs. external spreadsheet
- [ ] Source or request NPS paddling inventory data (may be FOIA or public GIS)

## Phase 2: Web Map
- [ ] Stand up Mapbox GL JS map centered on YNP
- [ ] Load waterways layer styled by `paddling_status` property
- [ ] Load park boundary as orange outline
- [ ] Add hiking trails layer (red) from OSM `highway=path` + trail tags
- [ ] Legend matching the reference map
- [ ] Deploy to Cloudflare Pages

## Phase 3: Polish
- [ ] Satellite basemap matching the original printed map aesthetic
- [ ] Click-to-inspect panel showing river name, classification, notes
- [ ] Filter toggles by classification tier
- [ ] Export-to-PDF or print layout option

## Open Questions
- Does NPS publish the paddling inventory as GIS data, or is it only on the printed map?
- Are "Priority" closures seasonal or permanent? That changes how we model the data.
- Is this for internal use (planning paddling trips) or public-facing?
