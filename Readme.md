# Smart Home Knowledge-Based Agent

A knowledge-based intelligent agent that autonomously manages a smart home environment using a **forward-chaining inference engine** and **priority-based conflict resolution**. Built entirely from scratch in Python — no external AI libraries.

---

## How It Works

The agent uses three core components:

- **Knowledge Base (KB)** — stores facts as `(predicate, room)` key-value pairs (e.g., `motion_detected=True` in `living_room`)
- **Rule Engine** — 12 if-then rules covering lighting, temperature, ventilation, and security
- **Forward Chaining** — iterates until a fixpoint: fires all applicable rules, derives new facts, repeats until no changes occur

---

## Rule Set

| ID | Rule | Conditions | Action | Priority |
|----|------|-----------|--------|----------|
| R1 | LightOnMotionDark | motion_detected=T, is_dark=T | Turn on light | 8 |
| R2 | LightOffNoMotion | motion_detected=F, light_on=T | Turn off light | 7 |
| R3 | DimLightSleeping | sleeping_mode=T, light_on=T | Dim the light | 9 |
| R4 | ACOnHotOccupied | temp_high=T, occupant_present=T | Activate AC | 8 |
| R5 | HeaterOnColdOccupied | temp_low=T, occupant_present=T | Activate heater | 8 |
| R6 | ClimateOffEmpty | occupant_present=F | Turn off AC & heater | 6 |
| R7 | FanOnHighCO2 | co2_high=T, ac_on=F | Activate fan | 7 |
| R8 | VentilationOnHighHumidity | humidity_high=T | Activate ventilation | 7 |
| R9 | FanOffNormalCO2 | co2_high=F, fan_on=T | Turn off fan | 6 |
| R10 | AlarmDoorOpenNight | door_open=T, is_night=T | Trigger alarm | 10 |
| R11 | SmokeAlert | smoke_detected=T, window_open=F | Open window + alert | 10 |
| R12 | EnergySavingEmptyDay | occupant_present=F, is_night=F | Energy saving mode | 5 |

---

## Project Structure

```
smart-home-agent/
├── smart_home_agent.py   # Main agent: KB, rules, inference engine, simulation
└── README.md
```

### Key Classes

| Class | Responsibility |
|-------|---------------|
| `KnowledgeBase` | Stores and queries facts via `tell()`, `ask()`, `retract()` |
| `Rule` | Encapsulates conditions, action, name, and priority |
| `ForwardChainingEngine` | Runs the fixpoint inference loop across all rooms |

---

## Getting Started

**Requirements:** Python 3.10+

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/smart-home-agent.git
cd smart-home-agent

# Run the simulation
python smart_home_agent.py
```

No dependencies to install — pure Python standard library only.

---

## Rooms Modeled

`living_room` · `bedroom` · `kitchen` · `bathroom` · `office`

---

## Simulation Scenarios

The simulation runs 5 timesteps representing a full day:

| Timestep | Scenario | Key Rules Fired |
|----------|----------|----------------|
| 1 | 🌅 Morning — motion + dark + cold | R1 (lights on), R5 (heater), R7 (fan) |
| 2 | ☀️ Afternoon — hot, CO2 normalizes | R4 (AC on), R8 (ventilation), R9 (fan off) |
| 3 | 🌆 Evening — night, sleeping mode | R3 (dim lights), R6 (climate off empty rooms) |
| 4 | 🌙 Night — door left open | R10 (alarm!), R5 (heater in bedroom) |
| 5 | 🚨 Emergency — smoke + CO2 spike | R11 (window + alert), R10 (alarm) |

---

## Conflict Resolution

When multiple rules could fire simultaneously, **priority-based ordering** is used:
- Safety-critical rules (alarm, smoke — priority 10) always fire first
- Comfort rules (energy saving — priority 5) fire last
- Higher-priority conclusions are never overwritten by lower-priority rules in the same iteration

---

## Sample Output

```
============================================================
 TIMESTEP 5: Emergency – smoke detected in kitchen, CO2 spike in office
============================================================
  [FIRED] R11_SmokeAlert | kitchen | → Alert sent + window opened in kitchen
  [FIRED] R10_AlarmDoorOpenNight | kitchen | → ALARM triggered in kitchen
  [FIRED] R4_ACOnHotOccupied | office | → AC activated in office
  Fixpoint reached after 2 iteration(s). 3 rule(s) fired.
```

---

## License

Academic project — CSC-3309, Al Akhawayn University.
