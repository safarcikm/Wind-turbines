# Power electronics sizing

Used for [docs/12-power-electronics.md](../../docs/12-power-electronics.md).

```
pip install numpy matplotlib
python3 sizing.py     # seconds; writes results/power_summary.json and results/power_envelope.png
```

Generator terminal envelope with an active rectifier (id = 0), DC link window,
current ratings, dump load energy and resistance, an efficiency chain with a
simple loss model (to be replaced by device datasheet losses), and net annual
energy.
