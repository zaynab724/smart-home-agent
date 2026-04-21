"""
CSC-3309 Fundamentals of Artificial Intelligence
Mini Project 3 - Smart Home Knowledge-Based Agent
Forward Chaining Inference Engine
"""

import copy
import logging
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s"
)
log = logging.getLogger("SmartHome")

# Stores facts as (predicate, room, value) triples. Example fact: ("motion_detected", "living_room", True)
class KnowledgeBase:

    def __init__(self):
        self.facts: dict[tuple, object] = {}

    def tell(self, predicate: str, room: str, value=True):
        self.facts[(predicate, room)] = value

    def ask(self, predicate: str, room: str):
        return self.facts.get((predicate, room), None)

    def retract(self, predicate: str, room: str):
        self.facts.pop((predicate, room), None)

    def snapshot(self):
        return copy.deepcopy(self.facts)

    def rooms(self):
        """Return all unique room names currently in KB."""
        return set(room for (_, room) in self.facts.keys())

    def display(self):
        log.info("  ── KB State ──────────────────────────────")
        grouped = {}
        for (pred, room), val in sorted(self.facts.items()):
            grouped.setdefault(room, []).append(f"{pred}={val}")
        for room, items in sorted(grouped.items()):
            log.info(f"    [{room}]: {', '.join(items)}")
        log.info("  ─────────────────────────────────────────")


class Rule:
    """
    A generic if-then rule evaluated per room.
    conditions: list of (predicate, expected_value) pairs
    action    : callable(kb, room) that modifies KB and returns an explanation string
    name      : human-readable rule name
    priority  : higher = evaluated first (conflict resolution strategy)
    """

    def __init__(self, name: str, conditions: list, action, priority: int = 5):
        self.name = name
        self.conditions = conditions
        self.action = action
        self.priority = priority

    def is_applicable(self, kb: KnowledgeBase, room: str) -> bool:
        for predicate, expected in self.conditions:
            actual = kb.ask(predicate, room)
            if actual != expected:
                return False
        return True

    def fire(self, kb: KnowledgeBase, room: str) -> str:
        return self.action(kb, room)


def make_rules() -> list[Rule]:
    """
    Returns a list of at least 10 rules:
      - ≥ 2 lighting rules
      - ≥ 2 temperature rules
      - ≥ 2 ventilation rules
      - ≥ 4 rules with 2+ conditions
    """

    rules = []

    # LIGHTING RULES 

    # R1 – Turn on lights when motion is detected and it is dark (2 conditions)
    def r1_action(kb, room):
        kb.tell("light_on", room, True)
        return f"Turned ON light in {room}: motion detected + dark"

    rules.append(Rule(
        name="R1_LightOnMotionDark",
        conditions=[("motion_detected", True), ("is_dark", True)],
        action=r1_action,
        priority=8
    ))

    # R2 – Turn off lights when no motion detected (room is empty)
    def r2_action(kb, room):
        kb.tell("light_on", room, False)
        return f"Turned OFF light in {room}: no motion detected"

    rules.append(Rule(
        name="R2_LightOffNoMotion",
        conditions=[("motion_detected", False), ("light_on", True)],
        action=r2_action,
        priority=7
    ))

    # R3 – Dim lights in sleeping mode (2 conditions)
    def r3_action(kb, room):
        kb.tell("light_dimmed", room, True)
        kb.tell("light_on", room, True)
        return f"Dimmed lights in {room}: sleeping mode + light was on"

    rules.append(Rule(
        name="R3_DimLightSleeping",
        conditions=[("sleeping_mode", True), ("light_on", True)],
        action=r3_action,
        priority=9
    ))

    # TEMPERATURE RULES

    # R4 – Activate AC when temperature is high and someone is present (2 conditions)
    def r4_action(kb, room):
        kb.tell("ac_on", room, True)
        kb.tell("heater_on", room, False)
        return f"AC activated in {room}: high temperature + occupant present"

    rules.append(Rule(
        name="R4_ACOnHotOccupied",
        conditions=[("temp_high", True), ("occupant_present", True)],
        action=r4_action,
        priority=8
    ))

    # R5 – Activate heater when temperature is low and someone is present (2 conditions)
    def r5_action(kb, room):
        kb.tell("heater_on", room, True)
        kb.tell("ac_on", room, False)
        return f"Heater activated in {room}: low temperature + occupant present"

    rules.append(Rule(
        name="R5_HeaterOnColdOccupied",
        conditions=[("temp_low", True), ("occupant_present", True)],
        action=r5_action,
        priority=8
    ))

    # R6 – Turn off AC/heater when room is empty
    def r6_action(kb, room):
        kb.tell("ac_on", room, False)
        kb.tell("heater_on", room, False)
        return f"AC and heater turned OFF in {room}: room is empty"

    rules.append(Rule(
        name="R6_ClimateOffEmpty",
        conditions=[("occupant_present", False)],
        action=r6_action,
        priority=6
    ))

    # VENTILATION RULES 

    # R7 – Open window/fan when CO2 is high and AC is not on (2 conditions)
    def r7_action(kb, room):
        kb.tell("fan_on", room, True)
        return f"Fan activated in {room}: high CO2 + AC not running"

    rules.append(Rule(
        name="R7_FanOnHighCO2",
        conditions=[("co2_high", True), ("ac_on", False)],
        action=r7_action,
        priority=7
    ))

    # R8 – Activate ventilation when humidity is high
    def r8_action(kb, room):
        kb.tell("ventilation_on", room, True)
        return f"Ventilation activated in {room}: high humidity detected"

    rules.append(Rule(
        name="R8_VentilationOnHighHumidity",
        conditions=[("humidity_high", True)],
        action=r8_action,
        priority=7
    ))

    # R9 – Turn off fan when CO2 returns to normal
    def r9_action(kb, room):
        kb.tell("fan_on", room, False)
        return f"Fan turned OFF in {room}: CO2 level normalised"

    rules.append(Rule(
        name="R9_FanOffNormalCO2",
        conditions=[("co2_high", False), ("fan_on", True)],
        action=r9_action,
        priority=6
    ))

    # SECURITY / SAFETY RULES 

    # R10 – Activate alarm when door is open at night (2 conditions)
    def r10_action(kb, room):
        kb.tell("alarm_on", room, True)
        return f"ALARM triggered in {room}: door open + night time"

    rules.append(Rule(
        name="R10_AlarmDoorOpenNight",
        conditions=[("door_open", True), ("is_night", True)],
        action=r10_action,
        priority=10
    ))

    # R11 – Send alert when smoke is detected and window is closed (2 conditions)
    def r11_action(kb, room):
        kb.tell("window_open", room, True)
        kb.tell("alert_sent", room, True)
        return f"Alert sent + window opened in {room}: smoke detected + window was closed"

    rules.append(Rule(
        name="R11_SmokeAlert",
        conditions=[("smoke_detected", True), ("window_open", False)],
        action=r11_action,
        priority=10
    ))

    # R12 – Enter energy saving mode when no occupant and not night (2 conditions)
    def r12_action(kb, room):
        kb.tell("energy_saving_mode", room, True)
        kb.tell("light_on", room, False)
        kb.tell("ac_on", room, False)
        kb.tell("heater_on", room, False)
        return f"Energy saving mode activated in {room}: empty + daytime"

    rules.append(Rule(
        name="R12_EnergySavingEmptyDay",
        conditions=[("occupant_present", False), ("is_night", False)],
        action=r12_action,
        priority=5
    ))

    # Sort by priority descending – conflict resolution: priority-based
    rules.sort(key=lambda r: r.priority, reverse=True)
    return rules


class ForwardChainingEngine:
    """
    Generic forward chaining engine.
    - Scans all rules for all rooms
    - Fires applicable rules
    - Repeats until fixpoint (no new facts added)
    Conflict resolution: priority-based ordering (higher priority rules fire first)
    """

    def __init__(self, kb: KnowledgeBase, rules: list[Rule]):
        self.kb = kb
        self.rules = rules  # already sorted by priority
        self.fired_log: list[dict] = []  # explanation log

    def run(self, timestep: int):
        """Execute forward chaining until fixpoint."""
        log.info(f"\n  ▶ Forward Chaining – Timestep {timestep}")
        iteration = 0
        while True:
            iteration += 1
            before = self.kb.snapshot()
            fired_this_round = []

            for rule in self.rules:
                for room in self.kb.rooms():
                    if rule.is_applicable(self.kb, room):
                        explanation = rule.fire(self.kb, room)
                        entry = {
                            "timestep": timestep,
                            "rule": rule.name,
                            "room": room,
                            "conditions": rule.conditions,
                            "action": explanation,
                        }
                        self.fired_log.append(entry)
                        fired_this_round.append(entry)
                        log.info(
                            f"    [FIRED] {rule.name} | {room} | "
                            f"Conditions: {[c[0] for c in rule.conditions]} | "
                            f"→ {explanation}"
                        )

            after = self.kb.snapshot()
            if before == after:
                log.info(
                    f"    Fixpoint reached after {iteration} iteration(s). "
                    f"{len(fired_this_round)} rule(s) fired."
                )
                break


def simulate():
    kb = KnowledgeBase()
    rules = make_rules()
    engine = ForwardChainingEngine(kb, rules)

    rooms = ["living_room", "bedroom", "kitchen", "bathroom", "office"]

    # ── Initial KB setup ──────────────────────────────────────────────────
    for room in rooms:
        kb.tell("occupant_present", room, False)
        kb.tell("motion_detected", room, False)
        kb.tell("light_on", room, False)
        kb.tell("is_dark", room, False)
        kb.tell("is_night", room, False)
        kb.tell("temp_high", room, False)
        kb.tell("temp_low", room, False)
        kb.tell("ac_on", room, False)
        kb.tell("heater_on", room, False)
        kb.tell("co2_high", room, False)
        kb.tell("humidity_high", room, False)
        kb.tell("fan_on", room, False)
        kb.tell("ventilation_on", room, False)
        kb.tell("door_open", room, False)
        kb.tell("window_open", room, True)
        kb.tell("smoke_detected", room, False)
        kb.tell("sleeping_mode", room, False)
        kb.tell("alarm_on", room, False)
        kb.tell("alert_sent", room, False)
        kb.tell("energy_saving_mode", room, False)
        kb.tell("light_dimmed", room, False)

    # ── Timestep scenarios ───────────────────────────────────────────────────
    scenarios = [
        {
            "description": "Morning – motion in living room & kitchen, it is dark, cold outside",
            "changes": {
                "living_room": [("motion_detected", True), ("is_dark", True), ("occupant_present", True), ("temp_low", True)],
                "kitchen":     [("motion_detected", True), ("is_dark", True), ("occupant_present", True), ("co2_high", True)],
            }
        },
        {
            "description": "Afternoon – house occupied, temperature rises, CO2 normalises",
            "changes": {
                "living_room": [("is_dark", False), ("temp_high", True), ("temp_low", False)],
                "kitchen":     [("is_dark", False), ("co2_high", False), ("humidity_high", True)],
                "office":      [("occupant_present", True), ("motion_detected", True), ("temp_high", True)],
            }
        },
        {
            "description": "Evening – night falls, bedroom occupied, sleeping mode activated",
            "changes": {
                "bedroom":     [("occupant_present", True), ("motion_detected", True), ("is_night", True), ("sleeping_mode", True), ("light_on", True)],
                "living_room": [("is_night", True), ("light_on", True)],
                "office":      [("occupant_present", False), ("motion_detected", False), ("is_night", True)],
            }
        },
        {
            "description": "Night – security check, kitchen door left open",
            "changes": {
                "kitchen": [("door_open", True), ("is_night", True), ("occupant_present", False)],
                "bedroom": [("temp_low", True), ("temp_high", False)],
            }
        },
        {
            "description": "Emergency – smoke detected in kitchen, CO2 spike in office",
            "changes": {
                "kitchen": [("smoke_detected", True), ("window_open", False)],
                "office":  [("co2_high", True), ("occupant_present", True), ("motion_detected", True)],
            }
        },
    ]

    log.info("=" * 60)
    log.info(" SMART HOME KB AGENT – SIMULATION")
    log.info("=" * 60)

    for step, scenario in enumerate(scenarios, start=1):
        log.info(f"\n{'='*60}")
        log.info(f" TIMESTEP {step}: {scenario['description']}")
        log.info(f"{'='*60}")

        # Apply environment changes
        log.info("\n  ── Environment Changes ──────────────────────────────────")
        for room, changes in scenario["changes"].items():
            for pred, val in changes:
                kb.tell(pred, room, val)
                log.info(f"    {room}.{pred} = {val}")

        log.info("\n  ── KB Before Inference ──────────────────────────────────")
        kb.display()

        # Run forward chaining
        engine.run(step)

        log.info("\n  ── KB After Inference ───────────────────────────────────")
        kb.display()

    # Explanation Summary
    log.info(f"\n{'='*60}")
    log.info(" EXPLANATION LOG – All Fired Rules")
    log.info(f"{'='*60}")
    for entry in engine.fired_log:
        cond_str = ", ".join(f"{c[0]}={c[1]}" for c in entry["conditions"])
        log.info(
            f"  [T{entry['timestep']}] Rule={entry['rule']} | Room={entry['room']}\n"
            f"    Conditions satisfied: {cond_str}\n"
            f"    Action: {entry['action']}\n"
        )

    log.info(f"\nTotal rules fired across all timesteps: {len(engine.fired_log)}")


if __name__ == "__main__":
    simulate()
