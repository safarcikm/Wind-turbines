# 6 kW generator G6 (doc 29)

`python3 g6.py` (~10 s, needs numpy, matplotlib, ezdxf for the Rev C geometry import) reads the Rev C FEA and checks (`analysis/generator/results/`), the 6 kW rotor and stall-control results (`analysis/turbine_6kw/results/`), and writes `results/g6.json` and figures G6-01 to G6-04: candidate generators, electrical data and losses at 164 rpm, energy, braking resistor sweep and stop simulations, thermal (doc 06 network), demagnetisation, voltage and mechanical checks.

Isometric views: `cad/generator_g6/iso_g6.py --png`.
