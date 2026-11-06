"""Build the interactive decision map page: results/map_data.json -> results/size_tsr_map.html"""
import json
from pathlib import Path
HERE = Path(__file__).parent
d = json.loads((HERE / "results" / "map_data.json").read_text())
d.pop("tables", None)
html = (HERE / "page_template.html").read_text().replace("/*DATA*/null", json.dumps(d, separators=(",", ":")))
(HERE / "results" / "size_tsr_map.html").write_text(html)
print(len(html))
