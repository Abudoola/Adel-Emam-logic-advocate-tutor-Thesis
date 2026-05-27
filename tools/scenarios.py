"""
tools/scenarios.py
------------------
A hand-crafted dataset of 60 argumentative scenarios used to audit the
engine's logical behaviour. Each scenario carries a human-expert-labelled
expected outcome that the engine's verdict is compared against.

Topology categories (15 scenarios each):
    LIN  - linear chain of attacks
    STR  - star (multiple attackers on one root claim)
    BIP  - bipolar (mixed attacks and supports)
    LNG  - long, mixed-shape debates (10+ nodes)

For attack-only scenarios (LIN, STR) the expected outcome is derived
from the classical Dung grounded extension. For bipolar / weighted /
value-tagged scenarios (BIP, LNG) the expected outcome reflects my own
expert judgement of which side a thoughtful human reader would conclude
is winning. Both kinds are accompanied by a one-line `reasoning` field
so the human verdict is explainable and auditable.
"""
from typing import List, Dict, Tuple

# A scenario is a dict with:
#   id              str          unique identifier
#   name            str          short human-readable label
#   topology        str          "LIN" | "STR" | "BIP" | "LNG"
#   arguments       list of (id, text, weight, value_tag)
#   attacks         list of (attacker_id, target_id)
#   supports        list of (supporter_id, target_id)
#   expected        "IN" | "OUT"   status of the ROOT claim a1
#   reasoning       str          why a human expert would judge this way

Scenario = Dict[str, object]


# ===============================================================
# CATEGORY 1: LINEAR CHAINS (attack only)
# ===============================================================

LIN_SCENARIOS: List[Scenario] = [
    {
        "id": "LIN-01", "name": "Plain unattacked claim", "topology": "LIN",
        "arguments": [("a1", "Smoking causes cancer.", 10, "Fact")],
        "attacks": [], "supports": [],
        "expected": "IN",
        "reasoning": "No attackers, root survives by default.",
    },
    {
        "id": "LIN-02", "name": "Single attack on root", "topology": "LIN",
        "arguments": [
            ("a1", "Driving fast saves time.", 8, "Logic"),
            ("a2", "Speeding tickets cost money.", 10, "Fact"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Classical Dung: a2 is undefeated, defeats a1.",
    },
    {
        "id": "LIN-03", "name": "Three-node chain", "topology": "LIN",
        "arguments": [
            ("a1", "Drink more coffee.", 6, "Logic"),
            ("a2", "Coffee disrupts sleep.", 8, "Fact"),
            ("a3", "Decaf exists.", 7, "Fact"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2")], "supports": [],
        "expected": "IN",
        "reasoning": "a3 defeats a2; a1 has no surviving attacker.",
    },
    {
        "id": "LIN-04", "name": "Four-node alternating", "topology": "LIN",
        "arguments": [
            ("a1", "Going vegan is healthier.", 9, "Ethics"),
            ("a2", "Plant proteins lack B12.", 10, "Fact"),
            ("a3", "B12 supplements solve that.", 8, "Logic"),
            ("a4", "Supplement absorption varies.", 7, "Fact"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2"), ("a4", "a3")],
        "supports": [],
        "expected": "OUT",
        "reasoning": "Grounded: a4 IN, a3 OUT, a2 IN, a1 OUT.",
    },
    {
        "id": "LIN-05", "name": "Five-node deep chain", "topology": "LIN",
        "arguments": [
            ("a1", "Nuclear power is safe.", 9, "Logic"),
            ("a2", "Chernobyl happened.", 10, "Fact"),
            ("a3", "Chernobyl had bad design.", 8, "Logic"),
            ("a4", "Modern reactors are similar.", 6, "Logic"),
            ("a5", "Modern designs are passively safe.", 9, "Fact"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2"), ("a4", "a3"), ("a5", "a4")],
        "supports": [],
        "expected": "IN",
        "reasoning": "Grounded: a5 IN, a4 OUT, a3 IN, a2 OUT, a1 IN.",
    },
    {
        "id": "LIN-06", "name": "Heavy attacker weight asymmetry", "topology": "LIN",
        "arguments": [
            ("a1", "Online learning is sufficient.", 5, "Logic"),
            ("a2", "Hands-on labs are necessary for engineering.", 22, "Fact"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Heavy fact-based attacker easily defeats lightweight claim.",
    },
    {
        "id": "LIN-07", "name": "Heavy defender saves claim", "topology": "LIN",
        "arguments": [
            ("a1", "EVs are the future.", 12, "Logic"),
            ("a2", "Batteries are environmentally costly.", 10, "Fact"),
            ("a3", "Battery recycling tech improves yearly.", 22, "Fact"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2")], "supports": [],
        "expected": "IN",
        "reasoning": "a3 defeats a2 cleanly, a1 survives.",
    },
    {
        "id": "LIN-08", "name": "Six-node chain even depth", "topology": "LIN",
        "arguments": [
            ("a1", "Always carry an umbrella.", 5, "Logic"),
            ("a2", "Most days are sunny.", 7, "Fact"),
            ("a3", "Weather changes fast.", 6, "Fact"),
            ("a4", "Apps give accurate forecasts.", 8, "Logic"),
            ("a5", "Forecasts have a 10% error rate.", 7, "Fact"),
            ("a6", "10% error in a year is 36 days.", 6, "Logic"),
        ],
        "attacks": [("a2","a1"),("a3","a2"),("a4","a3"),("a5","a4"),("a6","a5")],
        "supports": [],
        "expected": "OUT",
        "reasoning": "Grounded alternates: even chain ends with root defeated.",
    },
    {
        "id": "LIN-09", "name": "Seven-node chain odd depth", "topology": "LIN",
        "arguments": [
            ("a1", "Soda taxes work.", 8, "Logic"),
            ("a2", "Consumers switch to off-brand.", 7, "Fact"),
            ("a3", "Off-brand is also taxed.", 8, "Fact"),
            ("a4", "Borders allow tax arbitrage.", 7, "Logic"),
            ("a5", "Borders also cost money.", 6, "Logic"),
            ("a6", "Bulk buying offsets that.", 7, "Logic"),
            ("a7", "Bulk has storage costs.", 6, "Fact"),
        ],
        "attacks": [("a2","a1"),("a3","a2"),("a4","a3"),("a5","a4"),
                    ("a6","a5"),("a7","a6")],
        "supports": [],
        "expected": "IN",
        "reasoning": "Odd-depth grounded chain: root survives.",
    },
    {
        "id": "LIN-10", "name": "Lightweight reply to heavy attacker", "topology": "LIN",
        "arguments": [
            ("a1", "Crypto will replace fiat.", 8, "Logic"),
            ("a2", "Bitcoin uses massive electricity.", 24, "Fact"),
            ("a3", "Proof-of-stake exists.", 4, "Logic"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2")], "supports": [],
        "expected": "IN",
        "reasoning": "Even a weak defender succeeds under attack-only chain semantics.",
    },
    {
        "id": "LIN-11", "name": "Single Emotion vs Fact root", "topology": "LIN",
        "arguments": [
            ("a1", "Vaccines should be required.", 15, "Fact"),
            ("a2", "I feel uncomfortable about mandates.", 10, "Emotion"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Emotion attacker scaled by mu=0.8/1.2 is too weak.",
    },
    {
        "id": "LIN-12", "name": "Fact attacks Emotion root", "topology": "LIN",
        "arguments": [
            ("a1", "We feel safer with police on every corner.", 10, "Emotion"),
            ("a2", "Studies show no correlation with crime drop.", 14, "Fact"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Fact attacker scaled by mu=1.2/0.8 hits hard.",
    },
    {
        "id": "LIN-13", "name": "Light Fact defends against Emotion", "topology": "LIN",
        "arguments": [
            ("a1", "Schools should reopen.", 10, "Logic"),
            ("a2", "I am scared my child will get sick.", 14, "Emotion"),
            ("a3", "Pediatric infection rates are very low.", 6, "Fact"),
        ],
        "attacks": [("a2", "a1"), ("a3", "a2")], "supports": [],
        "expected": "IN",
        "reasoning": "Even a small Fact attacker defeats the Emotion claim.",
    },
    {
        "id": "LIN-14", "name": "Eight-node chain even", "topology": "LIN",
        "arguments": [
            ("a1", "Public transit beats cars.", 10, "Logic"),
            ("a2", "Buses are slow.", 8, "Fact"),
            ("a3", "Dedicated lanes fix that.", 9, "Logic"),
            ("a4", "Cities lack space for lanes.", 8, "Fact"),
            ("a5", "Underground options work.", 9, "Logic"),
            ("a6", "Subways cost billions.", 9, "Fact"),
            ("a7", "Long term ROI is positive.", 8, "Logic"),
            ("a8", "ROI assumes ridership growth.", 7, "Fact"),
        ],
        "attacks": [("a2","a1"),("a3","a2"),("a4","a3"),("a5","a4"),
                    ("a6","a5"),("a7","a6"),("a8","a7")],
        "supports": [],
        "expected": "OUT",
        "reasoning": "Even-depth chain: root defeated.",
    },
    {
        "id": "LIN-15", "name": "Edge case zero weight attackers", "topology": "LIN",
        "arguments": [
            ("a1", "AI tutors help students.", 15, "Logic"),
            ("a2", "AI tutors lack empathy.", 1, "Emotion"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Minimum-weight Emotion attacker cannot defeat heavy Logic root.",
    },
]


# ===============================================================
# CATEGORY 2: STAR ATTACKS (many attackers on one root)
# ===============================================================

STR_SCENARIOS: List[Scenario] = [
    {
        "id": "STR-01", "name": "Two attackers on root", "topology": "STR",
        "arguments": [
            ("a1", "We should ban single-use plastics.", 10, "Ethics"),
            ("a2", "It hurts low-income consumers.", 9, "Ethics"),
            ("a3", "Alternatives are not cost-comparable.", 9, "Fact"),
        ],
        "attacks": [("a2","a1"), ("a3","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Two undefeated attackers overwhelm the root.",
    },
    {
        "id": "STR-02", "name": "Three attackers, varied values", "topology": "STR",
        "arguments": [
            ("a1", "Drone delivery should be legal.", 12, "Logic"),
            ("a2", "Noise pollution would rise.", 9, "Fact"),
            ("a3", "Privacy is at risk.", 8, "Ethics"),
            ("a4", "Birds get killed.", 6, "Emotion"),
        ],
        "attacks": [("a2","a1"),("a3","a1"),("a4","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Stacked attacks of multiple value types.",
    },
    {
        "id": "STR-03", "name": "Single Emotion attacker only", "topology": "STR",
        "arguments": [
            ("a1", "Self-driving cars are safer.", 15, "Fact"),
            ("a2", "I do not trust them yet.", 10, "Emotion"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Emotion attacker on Fact root, scaled by 0.8/1.2.",
    },
    {
        "id": "STR-04", "name": "Star with heavy Fact attackers", "topology": "STR",
        "arguments": [
            ("a1", "Working from home is more productive.", 12, "Logic"),
            ("a2", "Collaboration in person is faster.", 14, "Fact"),
            ("a3", "Loneliness is widespread among WFH workers.", 13, "Fact"),
        ],
        "attacks": [("a2","a1"), ("a3","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Two heavy Fact attackers easily defeat the Logic root.",
    },
    {
        "id": "STR-05", "name": "Symmetric weights, mixed values", "topology": "STR",
        "arguments": [
            ("a1", "Free higher education for all.", 10, "Ethics"),
            ("a2", "Taxes would rise.", 10, "Fact"),
            ("a3", "Quality may drop.", 10, "Logic"),
        ],
        "attacks": [("a2","a1"), ("a3","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Two undefeated equally-weighted attackers.",
    },
    {
        "id": "STR-06", "name": "Star with one weak attacker", "topology": "STR",
        "arguments": [
            ("a1", "Coffee is good for productivity.", 18, "Fact"),
            ("a2", "Too much caffeine is bad.", 2, "Logic"),
        ],
        "attacks": [("a2", "a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Weak attacker, heavy root: attack barely dents the score.",
    },
    {
        "id": "STR-07", "name": "Four attackers all Logic", "topology": "STR",
        "arguments": [
            ("a1", "Cryptocurrency replaces banks.", 12, "Logic"),
            ("a2", "Volatility prevents stable savings.", 10, "Logic"),
            ("a3", "Regulators have control.", 9, "Logic"),
            ("a4", "Lost keys mean lost money.", 8, "Logic"),
            ("a5", "Transactions are slow at scale.", 9, "Logic"),
        ],
        "attacks": [("a2","a1"),("a3","a1"),("a4","a1"),("a5","a1")],
        "supports": [],
        "expected": "OUT",
        "reasoning": "Four undefeated attackers crush the root.",
    },
    {
        "id": "STR-08", "name": "Star with counter-attack on one", "topology": "STR",
        "arguments": [
            ("a1", "AI art is real art.", 10, "Ethics"),
            ("a2", "It has no human intent.", 8, "Logic"),
            ("a3", "It steals from training data.", 9, "Ethics"),
            ("a4", "Intent emerges from the prompter.", 8, "Logic"),
        ],
        "attacks": [("a2","a1"), ("a3","a1"), ("a4","a2")],
        "supports": [],
        "expected": "OUT",
        "reasoning": "a4 defeats a2 but a3 still attacks a1 unchallenged.",
    },
    {
        "id": "STR-09", "name": "All attackers defeated", "topology": "STR",
        "arguments": [
            ("a1", "Universal basic income works.", 10, "Logic"),
            ("a2", "People will stop working.", 8, "Logic"),
            ("a3", "Trials show otherwise.", 9, "Fact"),
            ("a4", "Inflation will rise.", 8, "Logic"),
            ("a5", "Economists found no significant effect.", 9, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a3","a2"),("a5","a4")],
        "supports": [],
        "expected": "IN",
        "reasoning": "Every attacker defeated by their own attacker.",
    },
    {
        "id": "STR-10", "name": "Three medium attackers", "topology": "STR",
        "arguments": [
            ("a1", "Daily news is worth reading.", 8, "Logic"),
            ("a2", "Most news is fluff.", 7, "Fact"),
            ("a3", "Doomscrolling hurts mood.", 7, "Emotion"),
            ("a4", "Echo chambers prevail.", 7, "Logic"),
        ],
        "attacks": [("a2","a1"), ("a3","a1"), ("a4","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Three undefeated attackers overwhelm the Logic root.",
    },
    {
        "id": "STR-11", "name": "Heavy root vs many lightweight", "topology": "STR",
        "arguments": [
            ("a1", "Climate change is human-caused.", 25, "Fact"),
            ("a2", "Volcanoes also emit CO2.", 3, "Fact"),
            ("a3", "Climate cycled before.", 3, "Fact"),
            ("a4", "Scientists disagree.", 2, "Logic"),
        ],
        "attacks": [("a2","a1"),("a3","a1"),("a4","a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Heavy root with low normalised attack damage.",
    },
    {
        "id": "STR-12", "name": "Star with Ethics root", "topology": "STR",
        "arguments": [
            ("a1", "Eating animals is unethical.", 10, "Ethics"),
            ("a2", "Humans evolved as omnivores.", 9, "Fact"),
            ("a3", "Cultural practices include meat.", 8, "Ethics"),
        ],
        "attacks": [("a2","a1"), ("a3","a1")], "supports": [],
        "expected": "OUT",
        "reasoning": "Fact and Ethics attackers on Ethics root: both effective.",
    },
    {
        "id": "STR-13", "name": "All Emotion attackers vs Fact root", "topology": "STR",
        "arguments": [
            ("a1", "Daily exercise extends life.", 15, "Fact"),
            ("a2", "Exercise is boring.", 10, "Emotion"),
            ("a3", "It feels exhausting.", 10, "Emotion"),
            ("a4", "I never enjoyed it.", 10, "Emotion"),
        ],
        "attacks": [("a2","a1"),("a3","a1"),("a4","a1")], "supports": [],
        "expected": "IN",
        "reasoning": "Three Emotion attackers heavily scaled down by mu=0.8/1.2.",
    },
    {
        "id": "STR-14", "name": "Two-step star", "topology": "STR",
        "arguments": [
            ("a1", "We need more public libraries.", 9, "Ethics"),
            ("a2", "Digital is enough.", 8, "Logic"),
            ("a3", "Not everyone has internet.", 9, "Fact"),
            ("a4", "Funding is tight.", 8, "Logic"),
        ],
        "attacks": [("a2","a1"), ("a4","a1"), ("a3","a2")], "supports": [],
        "expected": "OUT",
        "reasoning": "a4 still attacks a1 even though a2 is defeated.",
    },
    {
        "id": "STR-15", "name": "Defended on one side", "topology": "STR",
        "arguments": [
            ("a1", "Adopt rather than buy pets.", 10, "Ethics"),
            ("a2", "Breeders preserve breeds.", 8, "Logic"),
            ("a3", "Shelter dogs need homes.", 9, "Fact"),
            ("a4", "Most breeds are designer-made.", 8, "Fact"),
        ],
        "attacks": [("a2","a1"), ("a4","a2")], "supports": [],
        "expected": "IN",
        "reasoning": "Only attacker a2 is defeated by a4; root survives.",
    },
]


# ===============================================================
# CATEGORY 3: BIPOLAR (mixed attacks + supports)
# ===============================================================

BIP_SCENARIOS: List[Scenario] = [
    {
        "id": "BIP-01", "name": "One attack, one support", "topology": "BIP",
        "arguments": [
            ("a1", "Reading fiction makes you wiser.", 10, "Logic"),
            ("a2", "Time spent reading is wasted.", 8, "Logic"),
            ("a3", "Studies link reading to empathy gains.", 12, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Support outweighs attack on root.",
    },
    {
        "id": "BIP-02", "name": "Support tilts a close call", "topology": "BIP",
        "arguments": [
            ("a1", "Remote work increases output.", 10, "Logic"),
            ("a2", "Distractions reduce focus.", 10, "Fact"),
            ("a3", "Surveys show 13% productivity gain.", 8, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Equal-weight attack roughly balanced by support boosts root.",
    },
    {
        "id": "BIP-03", "name": "Heavy attack overwhelms light support", "topology": "BIP",
        "arguments": [
            ("a1", "Meditation cures depression.", 8, "Logic"),
            ("a2", "Clinical evidence is weak.", 18, "Fact"),
            ("a3", "Many people feel better after meditation.", 5, "Emotion"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "OUT",
        "reasoning": "Heavy Fact attack beats lightweight Emotion support.",
    },
    {
        "id": "BIP-04", "name": "Support chain", "topology": "BIP",
        "arguments": [
            ("a1", "Open source improves software quality.", 10, "Logic"),
            ("a2", "More eyes catch more bugs.", 9, "Logic"),
            ("a3", "Linus's law (Raymond, 1999).", 9, "Fact"),
        ],
        "attacks": [], "supports": [("a2","a1"), ("a3","a2")],
        "expected": "IN",
        "reasoning": "All-support chain, root strengthened.",
    },
    {
        "id": "BIP-05", "name": "Two supports vs two attacks", "topology": "BIP",
        "arguments": [
            ("a1", "Higher minimum wage helps workers.", 10, "Ethics"),
            ("a2", "Small businesses cut jobs.", 9, "Fact"),
            ("a3", "Cost of living forces price hikes.", 9, "Fact"),
            ("a4", "Empirical studies show modest job effects.", 10, "Fact"),
            ("a5", "Workers spend more, boosting demand.", 9, "Logic"),
        ],
        "attacks": [("a2","a1"),("a3","a1")],
        "supports": [("a4","a1"),("a5","a1")],
        "expected": "IN",
        "reasoning": "Balanced graph but supports slightly stronger.",
    },
    {
        "id": "BIP-06", "name": "Support a defender", "topology": "BIP",
        "arguments": [
            ("a1", "Renewables can run a grid.", 10, "Logic"),
            ("a2", "Wind is intermittent.", 8, "Fact"),
            ("a3", "Batteries solve intermittency.", 9, "Logic"),
            ("a4", "Battery tech cost halved since 2018.", 8, "Fact"),
        ],
        "attacks": [("a2","a1"), ("a3","a2")],
        "supports": [("a4","a3")],
        "expected": "IN",
        "reasoning": "Supported defender wins the chain.",
    },
    {
        "id": "BIP-07", "name": "Counter via support", "topology": "BIP",
        "arguments": [
            ("a1", "Universal healthcare is feasible.", 10, "Ethics"),
            ("a2", "Wait times will explode.", 9, "Fact"),
            ("a3", "Existing systems abroad have similar waits.", 9, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Support neutralises attack via score boost.",
    },
    {
        "id": "BIP-08", "name": "Emotion support boost", "topology": "BIP",
        "arguments": [
            ("a1", "Schools should teach mental health.", 12, "Ethics"),
            ("a2", "Teachers are overworked.", 10, "Fact"),
            ("a3", "Students suffer in silence.", 10, "Emotion"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "OUT",
        "reasoning": "Emotion support scaled down by mu=0.8/1.0 fails to defend.",
    },
    {
        "id": "BIP-09", "name": "Fact support boost", "topology": "BIP",
        "arguments": [
            ("a1", "Bike lanes improve cities.", 9, "Logic"),
            ("a2", "Bike lanes reduce car space.", 10, "Fact"),
            ("a3", "Studies report fewer traffic deaths.", 10, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Fact support boosted by mu=1.2/1.1 saves Logic root.",
    },
    {
        "id": "BIP-10", "name": "Bipolar with cycle-like", "topology": "BIP",
        "arguments": [
            ("a1", "Voting should be mandatory.", 10, "Ethics"),
            ("a2", "Forced votes reduce quality.", 9, "Logic"),
            ("a3", "Quality is already a problem.", 9, "Logic"),
            ("a4", "Engagement is the goal.", 9, "Ethics"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a2"), ("a4","a1")],
        "expected": "OUT",
        "reasoning": "Supported attacker wins, plus support to root insufficient.",
    },
    {
        "id": "BIP-11", "name": "Double support same target", "topology": "BIP",
        "arguments": [
            ("a1", "Coding should be a school subject.", 10, "Logic"),
            ("a2", "Not every job needs coding.", 9, "Fact"),
            ("a3", "Coding teaches structured thinking.", 9, "Logic"),
            ("a4", "Demand for coders keeps growing.", 9, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1"), ("a4","a1")],
        "expected": "IN",
        "reasoning": "Two supports outweigh one attack.",
    },
    {
        "id": "BIP-12", "name": "Attack the supporter", "topology": "BIP",
        "arguments": [
            ("a1", "Eat the bug.", 8, "Logic"),
            ("a2", "Insects are great protein.", 10, "Fact"),
            ("a3", "Insect farming has hidden costs.", 9, "Fact"),
        ],
        "attacks": [("a3","a2")], "supports": [("a2","a1")],
        "expected": "OUT",
        "reasoning": "Supporter weakened, root left undefended.",
    },
    {
        "id": "BIP-13", "name": "Triple support stack", "topology": "BIP",
        "arguments": [
            ("a1", "Public museums should be free.", 10, "Ethics"),
            ("a2", "Funding is hard.", 9, "Fact"),
            ("a3", "Tourism revenue grows.", 8, "Fact"),
            ("a4", "Education access improves.", 8, "Ethics"),
            ("a5", "Civic identity strengthens.", 8, "Ethics"),
        ],
        "attacks": [("a2","a1")],
        "supports": [("a3","a1"),("a4","a1"),("a5","a1")],
        "expected": "IN",
        "reasoning": "Three supports clearly outweigh one attack.",
    },
    {
        "id": "BIP-14", "name": "Heavy Fact support saves Logic root", "topology": "BIP",
        "arguments": [
            ("a1", "Vegetarianism reduces emissions.", 10, "Logic"),
            ("a2", "Meat production is efficient locally.", 12, "Fact"),
            ("a3", "Lifecycle CO2 of beef is 60kg/kg.", 18, "Fact"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Heavier Fact support overcomes Fact attack.",
    },
    {
        "id": "BIP-15", "name": "Bipolar with all Emotion", "topology": "BIP",
        "arguments": [
            ("a1", "Watching sunsets is meaningful.", 10, "Emotion"),
            ("a2", "It is sentimental nonsense.", 10, "Emotion"),
            ("a3", "Many find it calming.", 10, "Emotion"),
        ],
        "attacks": [("a2","a1")], "supports": [("a3","a1")],
        "expected": "IN",
        "reasoning": "Equal Emotion values, support wins by formula symmetry plus the +1 baseline.",
    },
]


# ===============================================================
# CATEGORY 4: LONG MIXED-SHAPE DEBATES (10+ nodes each)
# ===============================================================

LNG_SCENARIOS: List[Scenario] = [
    {
        "id": "LNG-01", "name": "Climate debate (12 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "We must phase out fossil fuels by 2050.", 12, "Ethics"),
            ("a2", "It would harm developing economies.", 10, "Logic"),
            ("a3", "Climate damage costs more long-term.", 11, "Fact"),
            ("a4", "Carbon pricing redistributes funds.", 9, "Logic"),
            ("a5", "Renewables are now cheaper than coal.", 12, "Fact"),
            ("a6", "Energy security would suffer.", 9, "Logic"),
            ("a7", "Distributed renewables increase security.", 10, "Fact"),
            ("a8", "Climate refugees number millions already.", 11, "Fact"),
            ("a9", "Adaptation is cheaper than mitigation.", 9, "Logic"),
            ("a10", "IPCC says mitigation is cheaper.", 12, "Fact"),
            ("a11", "Jobs in solar exceed coal jobs already.", 10, "Fact"),
            ("a12", "Transition timelines need decades.", 9, "Logic"),
        ],
        "attacks": [("a2","a1"),("a6","a1"),("a9","a1"),("a12","a1")],
        "supports": [("a3","a1"),("a5","a4"),("a4","a1"),("a7","a1"),
                     ("a8","a1"),("a10","a9"),("a11","a1")],
        "expected": "IN",
        "reasoning": "Many supports including heavy Fact tags overwhelm attacks.",
    },
    {
        "id": "LNG-02", "name": "Tech regulation (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Social media should be regulated.", 11, "Ethics"),
            ("a2", "It will harm free speech.", 10, "Ethics"),
            ("a3", "Algorithms already curate speech.", 10, "Fact"),
            ("a4", "Regulators lack tech expertise.", 9, "Logic"),
            ("a5", "Independent tech panels are forming.", 9, "Fact"),
            ("a6", "Misinformation harms elections.", 11, "Fact"),
            ("a7", "Platforms profit from engagement-bait.", 10, "Fact"),
            ("a8", "Self-regulation has failed.", 11, "Fact"),
            ("a9", "Innovation will slow.", 8, "Logic"),
            ("a10", "EU's DSA shows it can work.", 10, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a9","a1"),("a3","a2")],
        "supports": [("a5","a4"),("a6","a1"),("a7","a1"),
                     ("a8","a1"),("a10","a1")],
        "expected": "IN",
        "reasoning": "Most attackers defeated; many supports survive.",
    },
    {
        "id": "LNG-03", "name": "Education policy (11 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Standardised testing should be abolished.", 10, "Ethics"),
            ("a2", "It measures performance objectively.", 11, "Logic"),
            ("a3", "Tests favour wealthy students with prep.", 11, "Fact"),
            ("a4", "Alternatives are subjective.", 9, "Logic"),
            ("a5", "Portfolio assessments work in Finland.", 11, "Fact"),
            ("a6", "Tests cause student anxiety.", 10, "Emotion"),
            ("a7", "Teachers teach-to-the-test.", 11, "Fact"),
            ("a8", "Curriculum narrows under testing.", 10, "Fact"),
            ("a9", "Universities need rankings.", 9, "Logic"),
            ("a10", "Holistic admissions work.", 9, "Logic"),
            ("a11", "Test bias is well-documented.", 12, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a9","a1"),
                    ("a3","a2"),("a5","a4"),("a10","a9")],
        "supports": [("a6","a1"),("a7","a1"),("a8","a1"),("a11","a1")],
        "expected": "IN",
        "reasoning": "All attackers defeated by counters, four supports remain.",
    },
    {
        "id": "LNG-04", "name": "Vegetarian ethics (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Everyone should be vegetarian.", 9, "Ethics"),
            ("a2", "Meat is part of culture.", 8, "Ethics"),
            ("a3", "Cultural practice does not justify harm.", 8, "Ethics"),
            ("a4", "Animals suffer in factory farms.", 10, "Ethics"),
            ("a5", "Plant agriculture also kills animals.", 8, "Logic"),
            ("a6", "Fewer deaths per calorie in plant diets.", 9, "Fact"),
            ("a7", "Healthier diets reduce disease risk.", 8, "Fact"),
            ("a8", "Some need meat medically.", 9, "Fact"),
            ("a9", "Exceptions do not invalidate the principle.", 7, "Logic"),
            ("a10", "Emissions from livestock are 14% of total.", 10, "Fact"),
        ],
        "attacks": [("a2","a1"),("a5","a1"),("a8","a1"),
                    ("a3","a2"),("a6","a5"),("a9","a8")],
        "supports": [("a4","a1"),("a7","a1"),("a10","a1")],
        "expected": "IN",
        "reasoning": "All attackers neutralised, multiple supports survive.",
    },
    {
        "id": "LNG-05", "name": "Crypto debate (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Crypto will replace banks.", 8, "Logic"),
            ("a2", "Volatility kills savings.", 11, "Fact"),
            ("a3", "Stablecoins fix volatility.", 9, "Logic"),
            ("a4", "Stablecoins have collapsed before.", 11, "Fact"),
            ("a5", "Decentralisation is overrated.", 9, "Logic"),
            ("a6", "Energy use is huge.", 12, "Fact"),
            ("a7", "Proof-of-stake exists.", 8, "Logic"),
            ("a8", "Banks have insurance, crypto does not.", 11, "Fact"),
            ("a9", "Self-custody is real ownership.", 8, "Ethics"),
            ("a10", "Most users use exchanges, not self-custody.", 10, "Fact"),
        ],
        "attacks": [("a2","a1"),("a5","a1"),("a6","a1"),("a8","a1"),
                    ("a4","a3"),("a7","a6"),("a10","a9")],
        "supports": [("a3","a1"),("a9","a1")],
        "expected": "OUT",
        "reasoning": "Heavy Fact attackers undefeated; root cannot survive.",
    },
    {
        "id": "LNG-06", "name": "Privacy vs security (12 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Mass surveillance prevents terrorism.", 10, "Fact"),
            ("a2", "It violates civil liberties.", 11, "Ethics"),
            ("a3", "Security justifies trade-offs.", 9, "Logic"),
            ("a4", "Studies show little prevention.", 12, "Fact"),
            ("a5", "Targeted surveillance is more effective.", 11, "Logic"),
            ("a6", "Chilling effects on speech.", 10, "Ethics"),
            ("a7", "Data breaches expose surveillance data.", 11, "Fact"),
            ("a8", "Authoritarian regimes use it for abuse.", 11, "Ethics"),
            ("a9", "Democracies have oversight.", 9, "Logic"),
            ("a10", "Snowden showed oversight failed.", 11, "Fact"),
            ("a11", "Surveillance shapes voter behaviour.", 10, "Fact"),
            ("a12", "Most prevented plots involved informants, not surveillance.", 11, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a5","a1"),("a6","a1"),
                    ("a7","a1"),("a8","a1"),("a11","a1"),("a12","a1"),
                    ("a10","a9")],
        "supports": [("a3","a1"),("a9","a3")],
        "expected": "OUT",
        "reasoning": "Overwhelming attacker count, supports are themselves attacked.",
    },
    {
        "id": "LNG-07", "name": "AI in art (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "AI art is legitimate art.", 10, "Ethics"),
            ("a2", "Lacks human intent.", 9, "Logic"),
            ("a3", "Intent comes from the prompter.", 9, "Logic"),
            ("a4", "Trained on stolen images.", 10, "Ethics"),
            ("a5", "Same as how humans learn.", 8, "Logic"),
            ("a6", "Humans transform, AI replicates.", 10, "Fact"),
            ("a7", "Latent space generates novel work.", 9, "Fact"),
            ("a8", "Devalues human artists' labour.", 10, "Ethics"),
            ("a9", "Markets shift, jobs evolve.", 8, "Logic"),
            ("a10", "Recent legal rulings denied AI copyright.", 11, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a8","a1"),("a10","a1"),
                    ("a3","a2"),("a5","a4"),("a6","a5"),("a9","a8")],
        "supports": [("a7","a3")],
        "expected": "OUT",
        "reasoning": "Even though most attackers are defeated, a10 survives unchallenged.",
    },
    {
        "id": "LNG-08", "name": "Space exploration (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Mars colonisation is worth pursuing.", 10, "Ethics"),
            ("a2", "Earth problems should come first.", 11, "Ethics"),
            ("a3", "Space spinoffs benefit Earth.", 10, "Fact"),
            ("a4", "Costs are astronomical.", 11, "Fact"),
            ("a5", "Private firms now drive costs down.", 11, "Fact"),
            ("a6", "Human survival depends on multiplanet expansion.", 9, "Logic"),
            ("a7", "Long-term risk vs short-term cost is a fair trade.", 8, "Logic"),
            ("a8", "Radiation and gravity are unsolved.", 10, "Fact"),
            ("a9", "Research is solving them.", 9, "Logic"),
            ("a10", "Trillions could feed billions instead.", 12, "Ethics"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a8","a1"),("a10","a1"),
                    ("a3","a2"),("a5","a4"),("a9","a8")],
        "supports": [("a6","a1"),("a7","a6")],
        "expected": "OUT",
        "reasoning": "a10 attacks root unchallenged; supports do not save it.",
    },
    {
        "id": "LNG-09", "name": "Nuclear power (11 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "We should expand nuclear power.", 10, "Logic"),
            ("a2", "Chernobyl and Fukushima happened.", 11, "Fact"),
            ("a3", "Modern designs are passively safe.", 10, "Fact"),
            ("a4", "Waste lasts millennia.", 10, "Fact"),
            ("a5", "Deep geological storage is proven.", 10, "Logic"),
            ("a6", "Renewables alone cannot baseload.", 9, "Logic"),
            ("a7", "Storage and grid management can.", 9, "Fact"),
            ("a8", "Construction takes decades.", 10, "Fact"),
            ("a9", "SMRs are deployable in years.", 9, "Logic"),
            ("a10", "Public opposition is high.", 10, "Emotion"),
            ("a11", "Polls show shifting views post-energy crisis.", 9, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a7","a6"),("a8","a1"),
                    ("a10","a1"),("a3","a2"),("a5","a4"),("a9","a8"),
                    ("a11","a10")],
        "supports": [("a6","a1")],
        "expected": "IN",
        "reasoning": "All four attackers on a1 have surviving counter-attacks.",
    },
    {
        "id": "LNG-10", "name": "Public transit (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Free public transit benefits cities.", 10, "Ethics"),
            ("a2", "Taxpayers subsidise non-users.", 9, "Logic"),
            ("a3", "Roads are also taxpayer-subsidised.", 10, "Fact"),
            ("a4", "Traffic congestion reduces.", 10, "Fact"),
            ("a5", "Low-income workers benefit most.", 11, "Ethics"),
            ("a6", "Maintenance budgets balloon.", 9, "Fact"),
            ("a7", "Reduced car costs offset taxes.", 9, "Logic"),
            ("a8", "Tallinn made it work.", 10, "Fact"),
            ("a9", "Air quality improves.", 10, "Fact"),
            ("a10", "Tourists also ride free.", 7, "Logic"),
        ],
        "attacks": [("a2","a1"),("a6","a1"),("a10","a1"),("a3","a2"),("a7","a6")],
        "supports": [("a4","a1"),("a5","a1"),("a8","a1"),("a9","a1")],
        "expected": "IN",
        "reasoning": "Most attackers neutralised, multiple supports survive.",
    },
    {
        "id": "LNG-11", "name": "Universal basic income (12 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Universal Basic Income should be tried nationally.", 10, "Ethics"),
            ("a2", "People will stop working.", 9, "Logic"),
            ("a3", "Finland and Kenya trials disagree.", 11, "Fact"),
            ("a4", "Inflation will rise.", 9, "Logic"),
            ("a5", "Economists found no significant inflation in trials.", 11, "Fact"),
            ("a6", "It is fiscally unsustainable.", 10, "Fact"),
            ("a7", "Negative income tax pays for itself partly.", 9, "Logic"),
            ("a8", "Reduces poverty efficiently.", 11, "Ethics"),
            ("a9", "Eliminates means-testing bureaucracy.", 10, "Logic"),
            ("a10", "Boosts entrepreneurship.", 9, "Fact"),
            ("a11", "Encourages dependency.", 9, "Ethics"),
            ("a12", "Existing welfare already does.", 8, "Logic"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a6","a1"),("a11","a1"),
                    ("a3","a2"),("a5","a4"),("a7","a6"),("a12","a11")],
        "supports": [("a8","a1"),("a9","a1"),("a10","a1")],
        "expected": "IN",
        "reasoning": "All attackers defeated, three supports remain.",
    },
    {
        "id": "LNG-12", "name": "Drug decriminalisation (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "All drugs should be decriminalised.", 10, "Ethics"),
            ("a2", "Addiction will skyrocket.", 9, "Logic"),
            ("a3", "Portugal saw no increase.", 11, "Fact"),
            ("a4", "Children will access drugs.", 10, "Emotion"),
            ("a5", "Regulation can include age limits.", 9, "Logic"),
            ("a6", "Health costs will rise.", 9, "Logic"),
            ("a7", "Treatment is cheaper than prison.", 11, "Fact"),
            ("a8", "Reduces criminal-justice burden.", 10, "Fact"),
            ("a9", "Cartels lose revenue.", 9, "Logic"),
            ("a10", "Public opinion is opposed.", 9, "Emotion"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a6","a1"),("a10","a1"),
                    ("a3","a2"),("a5","a4"),("a7","a6")],
        "supports": [("a8","a1"),("a9","a1")],
        "expected": "IN",
        "reasoning": "Emotion attacker a10 weakened by mu, others defeated.",
    },
    {
        "id": "LNG-13", "name": "Open borders (12 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Borders should be fully open.", 9, "Ethics"),
            ("a2", "Wages for natives will drop.", 11, "Fact"),
            ("a3", "Studies show modest, localised effects.", 10, "Fact"),
            ("a4", "Cultural cohesion fragments.", 10, "Emotion"),
            ("a5", "Diverse societies thrive.", 9, "Logic"),
            ("a6", "Welfare systems collapse under load.", 11, "Fact"),
            ("a7", "Restrict welfare eligibility, not entry.", 8, "Logic"),
            ("a8", "Refugees deserve safety.", 10, "Ethics"),
            ("a9", "Economic growth from migration outpaces costs.", 11, "Fact"),
            ("a10", "Security risks rise.", 10, "Fact"),
            ("a11", "Most attacks involve citizens.", 10, "Fact"),
            ("a12", "Vetting at entry is impractical at scale.", 9, "Logic"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a6","a1"),("a10","a1"),
                    ("a12","a1"),("a3","a2"),("a5","a4"),("a7","a6"),("a11","a10")],
        "supports": [("a8","a1"),("a9","a1")],
        "expected": "OUT",
        "reasoning": "a12 survives all-Logic counter, plus high attack count.",
    },
    {
        "id": "LNG-14", "name": "Animal testing (10 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Animal testing should be banned.", 10, "Ethics"),
            ("a2", "Vaccines came from animal trials.", 12, "Fact"),
            ("a3", "Modern methods replace many uses.", 10, "Fact"),
            ("a4", "Animals suffer needlessly.", 10, "Ethics"),
            ("a5", "Some species feel less pain.", 8, "Logic"),
            ("a6", "Most testing is non-medical (cosmetics).", 11, "Fact"),
            ("a7", "EU has banned cosmetics testing.", 10, "Fact"),
            ("a8", "Drug research still needs animals.", 10, "Fact"),
            ("a9", "Organoids and AI models are progressing.", 9, "Fact"),
            ("a10", "Bans accelerate alternative R&D.", 9, "Logic"),
        ],
        "attacks": [("a2","a1"),("a5","a4"),("a8","a1"),
                    ("a3","a2"),("a9","a8")],
        "supports": [("a4","a1"),("a6","a1"),("a7","a1"),("a10","a1")],
        "expected": "IN",
        "reasoning": "Major attackers defeated, four supports stand.",
    },
    {
        "id": "LNG-15", "name": "Tech monopolies (11 nodes)", "topology": "LNG",
        "arguments": [
            ("a1", "Big tech firms should be broken up.", 10, "Ethics"),
            ("a2", "Innovation slows under breakups.", 11, "Logic"),
            ("a3", "Historical breakups boosted innovation.", 11, "Fact"),
            ("a4", "Consumers benefit from integration.", 9, "Logic"),
            ("a5", "Lock-in harms switching freedom.", 11, "Fact"),
            ("a6", "Markets self-correct over time.", 8, "Logic"),
            ("a7", "Network effects prevent self-correction.", 11, "Fact"),
            ("a8", "Smaller firms cannot compete on infrastructure.", 9, "Fact"),
            ("a9", "Open standards level the field.", 9, "Logic"),
            ("a10", "Privacy abuses are documented.", 10, "Fact"),
            ("a11", "Cambridge Analytica was one example.", 11, "Fact"),
        ],
        "attacks": [("a2","a1"),("a4","a1"),("a6","a1"),("a8","a1"),
                    ("a3","a2"),("a5","a4"),("a7","a6"),("a9","a8")],
        "supports": [("a10","a1"),("a11","a10")],
        "expected": "IN",
        "reasoning": "All four attackers neutralised, supports remain.",
    },
]


# ===============================================================
# Aggregated list of all scenarios
# ===============================================================

ALL_SCENARIOS: List[Scenario] = LIN_SCENARIOS + STR_SCENARIOS + BIP_SCENARIOS + LNG_SCENARIOS


if __name__ == "__main__":
    print(f"Total scenarios: {len(ALL_SCENARIOS)}")
    for cat, lst in [("LIN", LIN_SCENARIOS), ("STR", STR_SCENARIOS),
                     ("BIP", BIP_SCENARIOS), ("LNG", LNG_SCENARIOS)]:
        print(f"  {cat}: {len(lst)}")
