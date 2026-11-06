# Size × TSR decision map (doc 27)

Run order:

1. `python3 cp_tables.py` – BEM tables per design TSR with the doc 03 model (~5 min) → `results/rotor_tables.json`
2. `python3 model.py` – sizes and evaluates 9 ratings × 9 TSRs × 7 rated winds, checks calibration against the current and V5 designs → `results/grid.csv`, `results/map_data.json`, `results/calibration.json`
3. `python3 build_page.py` – embeds the data in `page_template.html` → `results/size_tsr_map.html` (open in a browser)

Assumptions are in `docs/27-size-tsr-decision-map.md`.
