# Wind Turbines

Development of a 12 kW wind turbine designed for Icelandic conditions (high
winds, strong gusts, icing, cold, salt air and volcanic ash), with as much as
possible manufactured in-house.

## Documents

- [01 – Project categories](docs/01-project-categories.md): work breakdown,
  Iceland-specific challenges, in-house feasibility and dependencies.
- [02 – Design basis and requirements](docs/02-design-basis.md): Icelandic
  design envelope, IEC Class S parameters, design load cases and
  requirements for every category.
- [03 – Rotor concept study](docs/03-rotor-concept.md): rotor diameter,
  tip speed, blade shape, aerofoils and pitch schedule
  (model in [analysis/rotor](analysis/rotor/)).
- [04 – Generator concept study](docs/04-generator-concept.md): topology,
  size, poles/slots, magnets and Iceland-specific protection
  (model in [analysis/generator](analysis/generator/)).
- [05 – Generator FEA and thermal check](docs/05-generator-fea-thermal.md):
  2D finite element results (back-EMF, cogging, torque, demagnetisation) and
  thermal network; leads to N40UH magnets and a mandatory cooling package.
- [06 – Generator simulation round 2](docs/06-generator-round2.md): confirms
  the fixes (all checks pass) and freezes the generator concept data.
- [07 – Nacelle, spindle and bearings](docs/07-nacelle-spindle-bearings.md):
  layout, concept loads, main bearings, spindle, generator cooling path,
  brake and yaw (model in [analysis/nacelle](analysis/nacelle/)).
- [08 – Load verification](docs/08-load-verification.md): IEC 61400-2
  Simplified Load Model and a 94-case aeroelastic simulation; design load
  recommendation, design overspeed 250 rpm, tower frequency and parked
  stability findings (models in [analysis/loads](analysis/loads/)).
