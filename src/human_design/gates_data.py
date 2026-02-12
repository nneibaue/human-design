"""Gate, channel, and circuit data for the 64 Gates flash card learning system.

Data sourced from memorize-the-64-gates-revised.md and bodygraph.yaml.
Uses 64keys naming conventions with Ra names stored alongside for dual-mode display.
"""

from __future__ import annotations

# Center name mapping between systems
CENTER_NAMES_64KEYS = {
    "INSPIRATION": "Inspiration",
    "MIND": "Mind",
    "EXPRESSION": "Expression",
    "IDENTITY": "Identity",
    "WILLPOWER": "Willpower",
    "EMOTION": "Emotion",
    "DRIVE": "Drive",
    "LIFEFORCE": "Life Force",
    "INTUITION": "Intuition",
}

CENTER_NAMES_RA = {
    "INSPIRATION": "Head",
    "MIND": "Ajna",
    "EXPRESSION": "Throat",
    "IDENTITY": "G Center",
    "WILLPOWER": "Heart/Ego",
    "EMOTION": "Solar Plexus",
    "DRIVE": "Root",
    "LIFEFORCE": "Sacral",
    "INTUITION": "Spleen",
}

# All 64 gates with metadata for flash cards
GATES: dict[int, dict] = {
    1: {
        "name_64keys": "Originality",
        "name_ra": "The Creative",
        "center": "Identity",
        "partner_gates": [8],
        "channel_names": ["Inspiration"],
        "circuits": ["Individual Knowing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 1 (Originality) is a painter alone in a studio, brush flying. "
            "Gate 8 (Promotion) is the gallery owner who bursts through the door. "
            "Together: Inspiration — creative originality gets promoted into the world."
        ),
    },
    2: {
        "name_64keys": "Orientation",
        "name_ra": "The Receptive",
        "center": "Identity",
        "partner_gates": [14],
        "channel_names": ["The Beat"],
        "circuits": ["Individual Knowing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 2 (Orientation) is a compass needle. Gate 14 (Capacity) is a drum. "
            "The compass listens for direction, the drum provides driving energy. "
            "Together: The Beat — the pulse of resources flowing in the right direction."
        ),
    },
    3: {
        "name_64keys": "Mutation",
        "name_ra": "Difficulty at the Beginning",
        "center": "Life Force",
        "partner_gates": [60],
        "channel_names": ["Mutation"],
        "circuits": ["Individual Centering"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 3 IS Mutation. Gate 60 (Realism) provides the limitation that makes "
            "mutation possible. A caterpillar enters a chrysalis — constraints enable transformation."
        ),
    },
    4: {
        "name_64keys": "Theses",
        "name_ra": "Youthful Folly",
        "center": "Mind",
        "partner_gates": [63],
        "channel_names": ["Logic"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "A courtroom. The Verification officer (63) slams a giant rubber stamp "
            "onto a PhD thesis (4). STAMP: 'LOGIC APPROVED.' Thesis + verification = logic."
        ),
    },
    5: {
        "name_64keys": "Rhythm",
        "name_ra": "Waiting",
        "center": "Life Force",
        "partner_gates": [15],
        "channel_names": ["Rhythm"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 5 IS Rhythm. Gate 15 is Flexibility — the love of extremes, of all "
            "of humanity's rhythms. Natural rhythm meets universal flexibility."
        ),
    },
    6: {
        "name_64keys": "Diplomacy",
        "name_ra": "Conflict",
        "center": "Emotion",
        "partner_gates": [59],
        "channel_names": ["Mating"],
        "circuits": ["Tribal Defense"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 6 (Diplomacy) is a door. Gate 59 (Intimacy) is someone knocking. "
            "Diplomacy decides whether to open. If it does: Mating. "
            "The fertility channel — Diplomacy + Intimacy."
        ),
    },
    7: {
        "name_64keys": "Strategy",
        "name_ra": "The Army",
        "center": "Identity",
        "partner_gates": [31],
        "channel_names": ["The Alpha"],
        "circuits": ["Collective Understanding"],
        "difficulty": 2,
        "memory_hook": (
            "A wolf pack: Gate 7 (Strategy) knows WHERE to go. Gate 31 (Influence) "
            "knows HOW to get others to follow. Strategy + Influence = The Alpha."
        ),
    },
    8: {
        "name_64keys": "Promotion",
        "name_ra": "Holding Together",
        "center": "Expression",
        "partner_gates": [1],
        "channel_names": ["Inspiration"],
        "circuits": ["Individual Knowing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 8 (Promotion) champions ideas. Gate 1 (Originality) creates them. "
            "Without promotion, originality stays hidden; without originality, promotion has nothing to sell."
        ),
    },
    9: {
        "name_64keys": "Focussing",
        "name_ra": "The Taming Power of the Small",
        "center": "Life Force",
        "partner_gates": [52],
        "channel_names": ["Concentration"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Focussing (9) meets Stillness (52). A laser beam hits a perfectly still pond. "
            "The beam doesn't scatter — it penetrates straight down. Concentration."
        ),
    },
    10: {
        "name_64keys": "Authenticity",
        "name_ra": "Treading",
        "center": "Identity",
        "partner_gates": [20, 34, 57],
        "channel_names": ["Awakening", "Exploration", "Perfected Form"],
        "circuits": ["Integration"],
        "difficulty": 2,
        "memory_hook": (
            "Integration mega-hub. 'Authentic Present Strength through Intuition.' "
            "Gate 10 connects to 20, 34, and 57 — every pair of the four Integration gates connects."
        ),
    },
    11: {
        "name_64keys": "Ideas",
        "name_ra": "Peace",
        "center": "Mind",
        "partner_gates": [56],
        "channel_names": ["Curiosity"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "A child with 11 on their jersey bursts with ideas, tugging at a campfire "
            "storyteller (56, Stimulation). 'Tell me another one!' Pure curiosity."
        ),
    },
    12: {
        "name_64keys": "Appropriateness",
        "name_ra": "Standstill",
        "center": "Expression",
        "partner_gates": [22],
        "channel_names": ["Openness"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "An actor (12, Appropriateness — knowing when to speak) walks onto a stage. "
            "The audience member's mood (22) shifts with every word. When truly open, "
            "timing and emotion align. Openness."
        ),
    },
    13: {
        "name_64keys": "Mindfulness",
        "name_ra": "Fellowship of Man",
        "center": "Identity",
        "partner_gates": [33],
        "channel_names": ["The Prodigal"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "A traveler returns home. Gate 13 (Mindfulness — the listener, keeper of secrets) "
            "sits by the hearth. Gate 33 (Prudence — wisdom of retreat) is the prodigal son "
            "who returned with stories. Prudence and mindfulness make wisdom from experience."
        ),
    },
    14: {
        "name_64keys": "Capacity",
        "name_ra": "Possession in Great Measure",
        "center": "Life Force",
        "partner_gates": [2],
        "channel_names": ["The Beat"],
        "circuits": ["Individual Knowing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 14 (Capacity — resources, fuel, power to manifest) is a drum. "
            "Gate 2 (Orientation — the compass) listens for direction. "
            "The Beat: the pulse of resources flowing in the right direction."
        ),
    },
    15: {
        "name_64keys": "Flexibility",
        "name_ra": "Modesty",
        "center": "Identity",
        "partner_gates": [5],
        "channel_names": ["Rhythm"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 15 (Flexibility — love of extremes, all of humanity's rhythms) meets "
            "Gate 5 (Rhythm). Natural rhythm meets universal flexibility."
        ),
    },
    16: {
        "name_64keys": "Identification",
        "name_ra": "Enthusiasm",
        "center": "Expression",
        "partner_gates": [48],
        "channel_names": ["The Wave Length"],
        "circuits": ["Collective Understanding"],
        "difficulty": 3,
        "memory_hook": (
            "Two musicians. Gate 16 (Identification — the enthusiastic practicer) plays guitar. "
            "Gate 48 (Depth — deep knowledge) plays cello. They lock into the same Wave Length."
        ),
    },
    17: {
        "name_64keys": "Opinions",
        "name_ra": "Following",
        "center": "Mind",
        "partner_gates": [62],
        "channel_names": ["Acceptance"],
        "circuits": ["Collective Understanding"],
        "difficulty": 2,
        "memory_hook": (
            "A debate stage. Gate 17 (Opinions) shouts from a bullhorn. "
            "Gate 62 (Precision) demands facts. When Opinion speaks with Precision, "
            "the audience nods. Acceptance."
        ),
    },
    18: {
        "name_64keys": "Judgment",
        "name_ra": "Work on What Has Been Spoiled",
        "center": "Intuition",
        "partner_gates": [58],
        "channel_names": ["Judgment"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 18 IS Judgment. Gate 58 (Joyfulness) provides the vitality behind "
            "the drive to correct and improve. Judgment + Joyfulness = the joy of making things better."
        ),
    },
    19: {
        "name_64keys": "Needs",
        "name_ra": "Approach",
        "center": "Drive",
        "partner_gates": [49],
        "channel_names": ["Synthesis"],
        "circuits": ["Tribal Defense"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 49 (Principles — the tribal judge) sits in robes. Gate 19 (Needs) is a crowd "
            "of hungry villagers. When Principles meets Needs: Synthesis — tribal revolution or acceptance."
        ),
    },
    20: {
        "name_64keys": "Presentness",
        "name_ra": "Contemplation",
        "center": "Expression",
        "partner_gates": [10, 34, 57],
        "channel_names": ["Awakening", "Charisma", "The Brain Wave"],
        "circuits": ["Integration"],
        "difficulty": 2,
        "memory_hook": (
            "Integration mega-hub. Gate 20 connects to 10, 34, and 57. "
            "Present strength is magnetic (Charisma). Present intuition = a flash of knowing (The Brain Wave)."
        ),
    },
    21: {
        "name_64keys": "Authority",
        "name_ra": "Biting Through",
        "center": "Willpower",
        "partner_gates": [45],
        "channel_names": ["Money"],
        "circuits": ["Tribal Ego"],
        "difficulty": 1,
        "memory_hook": (
            "'SHOW ME THE MONEY!' Gate 21 (Authority — will to control resources) is Jerry Maguire. "
            "Gate 45 (Accumulation — gathering wealth) is the king. Together: Money."
        ),
    },
    22: {
        "name_64keys": "Mood",
        "name_ra": "Grace",
        "center": "Emotion",
        "partner_gates": [12],
        "channel_names": ["Openness"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 22 (Mood — unpredictable emotional shifts) in the audience. "
            "Gate 12 (Appropriateness) on stage. When the actor is authentic and open, "
            "the moody audience member melts. Openness."
        ),
    },
    23: {
        "name_64keys": "Clarity",
        "name_ra": "Splitting Apart",
        "center": "Expression",
        "partner_gates": [43],
        "channel_names": ["Structuring"],
        "circuits": ["Individual Knowing"],
        "difficulty": 3,
        "memory_hook": (
            "A lightning bolt (43, Insight) strikes a glass prism (23, Clarity), "
            "refracting it into a perfectly organized rainbow. Raw flash to clean structure. Structuring."
        ),
    },
    24: {
        "name_64keys": "Introspection",
        "name_ra": "Return",
        "center": "Mind",
        "partner_gates": [61],
        "channel_names": ["Awareness"],
        "circuits": ["Individual Knowing"],
        "difficulty": 3,
        "memory_hook": (
            "A lighthouse (61) beams into infinite darkness — exploring the unknown. "
            "Below it, a hamster on a wheel (24) runs in circles — lost in introspection. "
            "When the beam hits the hamster wheel, the hamster stops and looks up. Awareness."
        ),
    },
    25: {
        "name_64keys": "Naturalness",
        "name_ra": "Innocence",
        "center": "Identity",
        "partner_gates": [51],
        "channel_names": ["Initiation"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "A child (25, natural innocence) at the edge of a cliff. A thunderbolt (51, courage) "
            "strikes behind them. The child doesn't run — they jump. Initiation: innocence meets "
            "shock and transforms."
        ),
    },
    26: {
        "name_64keys": "Tactic",
        "name_ra": "The Taming Power of the Great",
        "center": "Willpower",
        "partner_gates": [44],
        "channel_names": ["Surrender"],
        "circuits": ["Tribal Ego"],
        "difficulty": 3,
        "memory_hook": (
            "A poker player (26, Tactic) going all-in, face down, sliding cards to their "
            "opponent (44, Collaboration). The tactic must surrender to genuine collaboration. "
            "Surrender."
        ),
    },
    27: {
        "name_64keys": "Caring",
        "name_ra": "Nourishment",
        "center": "Life Force",
        "partner_gates": [50],
        "channel_names": ["Preservation"],
        "circuits": ["Tribal Defense"],
        "difficulty": 2,
        "memory_hook": (
            "A parent (27, Caring) cooking a massive pot of soup. The family rulebook (50, Values) "
            "hangs on the wall: 'We eat together. We waste nothing.' Caring + Values = Preservation."
        ),
    },
    28: {
        "name_64keys": "Risk",
        "name_ra": "Preponderance of the Great",
        "center": "Intuition",
        "partner_gates": [38],
        "channel_names": ["Struggle"],
        "circuits": ["Individual Centering"],
        "difficulty": 2,
        "memory_hook": (
            "A cliff-diver (28, Risk) stands at the edge. Gate 38 (Tenacity) is the voice "
            "saying 'AGAIN.' Together: Struggle — purposeful struggle. The cliff-diver isn't scared. "
            "They're alive."
        ),
    },
    29: {
        "name_64keys": "Commitment",
        "name_ra": "The Abysmal",
        "center": "Life Force",
        "partner_gates": [46],
        "channel_names": ["Discovery"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 29 (Commitment — saying YES) shakes hands with Gate 46 (Dedication — love of the body). "
            "When committed AND dedicated, you stumble into Discovery."
        ),
    },
    30: {
        "name_64keys": "Feelings",
        "name_ra": "The Clinging",
        "center": "Emotion",
        "partner_gates": [41],
        "channel_names": ["Recognition"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "A bonfire (30, Feelings — the fire of desire). A dreamer (41, Hope) lying in grass, "
            "watching clouds. When Feelings gets ignited by Hope, you recognize what you truly desire. Recognition."
        ),
    },
    31: {
        "name_64keys": "Influence",
        "name_ra": "Influence",
        "center": "Expression",
        "partner_gates": [7],
        "channel_names": ["The Alpha"],
        "circuits": ["Collective Understanding"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 31 (Influence — democratic leadership, the voice people follow) meets "
            "Gate 7 (Strategy — knowing WHERE to go). Strategy + Influence = The Alpha."
        ),
    },
    32: {
        "name_64keys": "Continuity",
        "name_ra": "Duration",
        "center": "Intuition",
        "partner_gates": [54],
        "channel_names": ["Transformation"],
        "circuits": ["Tribal Defense"],
        "difficulty": 3,
        "memory_hook": (
            "A quality inspector (32, Continuity — will this endure?). An employee (54, Ambition) "
            "eyes burning to become CEO. When continuity says 'yes' to ambition, Transformation happens."
        ),
    },
    33: {
        "name_64keys": "Prudence",
        "name_ra": "Retreat",
        "center": "Expression",
        "partner_gates": [13],
        "channel_names": ["The Prodigal"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 33 (Prudence — wisdom of retreat) is the prodigal traveler who returns home. "
            "Gate 13 (Mindfulness — the listener) sits by the hearth. The Prodigal: "
            "going out, gathering experience, then returning with stories."
        ),
    },
    34: {
        "name_64keys": "Strength",
        "name_ra": "The Power of the Great",
        "center": "Life Force",
        "partner_gates": [10, 20, 57],
        "channel_names": ["Exploration", "Charisma", "Power"],
        "circuits": ["Integration"],
        "difficulty": 2,
        "memory_hook": (
            "Integration mega-hub. 'Authentic Present Strength through Intuition.' "
            "Gate 34 connects to 10, 20, and 57. Strength guided by intuition = true Power."
        ),
    },
    35: {
        "name_64keys": "Progress",
        "name_ra": "Progress",
        "center": "Expression",
        "partner_gates": [36],
        "channel_names": ["Transitoriness"],
        "circuits": ["Collective Sensing"],
        "difficulty": 3,
        "memory_hook": (
            "A bus labeled '35-36.' The driver (35, Progress) always moves forward. "
            "At the back, Gate 36 (Compassion) weeps for everything left behind. "
            "The bus never stops. Everything is transitory. Transitoriness."
        ),
    },
    36: {
        "name_64keys": "Compassion",
        "name_ra": "Darkening of the Light",
        "center": "Emotion",
        "partner_gates": [35],
        "channel_names": ["Transitoriness"],
        "circuits": ["Collective Sensing"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 36 (Compassion — emotional inexperience driving the need for new experiences) "
            "pairs with Gate 35 (Progress). Life as a journey that never pauses. Transitoriness."
        ),
    },
    37: {
        "name_64keys": "Loyalty",
        "name_ra": "The Family",
        "center": "Emotion",
        "partner_gates": [40],
        "channel_names": ["Community"],
        "circuits": ["Tribal Ego"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 37 (Loyalty — warmth of the hearth) is a fireplace. "
            "Gate 40 (Determination — the breadwinner coming home from a long day). "
            "Loyalty + Determination = Community. 'I'll work for you if you keep the fire burning.'"
        ),
    },
    38: {
        "name_64keys": "Tenacity",
        "name_ra": "Opposition",
        "center": "Drive",
        "partner_gates": [28],
        "channel_names": ["Struggle"],
        "circuits": ["Individual Centering"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 38 (Tenacity — stubbornness to keep fighting) says 'AGAIN' to the "
            "cliff-diver (28, Risk). Together: Struggle — purposeful, meaning-seeking persistence."
        ),
    },
    39: {
        "name_64keys": "Liberation",
        "name_ra": "Obstruction",
        "center": "Drive",
        "partner_gates": [55],
        "channel_names": ["Emoting"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 39 (Liberation — the provocateur) walks into a room where Gate 55 (Abundance) "
            "sits alone. Liberation taps Abundance: 'FEEL something.' Abundance erupts — "
            "tears, laughter, rage, joy. That eruption IS Emoting."
        ),
    },
    40: {
        "name_64keys": "Determination",
        "name_ra": "Deliverance",
        "center": "Willpower",
        "partner_gates": [37],
        "channel_names": ["Community"],
        "circuits": ["Tribal Ego"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 40 (Determination — the will to work alone for the family's benefit) "
            "is the breadwinner. Gate 37 (Loyalty) is the fireplace. "
            "Determination + Loyalty = Community."
        ),
    },
    41: {
        "name_64keys": "Hope",
        "name_ra": "Decrease",
        "center": "Drive",
        "partner_gates": [30],
        "channel_names": ["Recognition"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 41 (Hope — the daydream, imagining new possibilities) lies in grass watching clouds. "
            "Gate 30 (Feelings — the fire of desire) ignites the dream. "
            "You recognize what you truly desire. Recognition."
        ),
    },
    42: {
        "name_64keys": "Increase",
        "name_ra": "Increase",
        "center": "Life Force",
        "partner_gates": [53],
        "channel_names": ["Maturation"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 42 (Increase — growth, completion, fullness of a cycle) is a fruit tree heavy "
            "with ripe apples. Gate 53 (Readiness — pressure to start new) is a seed eager to sprout. "
            "Maturation: seed to tree to fruit to seed again."
        ),
    },
    43: {
        "name_64keys": "Insight",
        "name_ra": "Breakthrough",
        "center": "Mind",
        "partner_gates": [23],
        "channel_names": ["Structuring"],
        "circuits": ["Individual Knowing"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 43 (Insight — sudden flash, the 'aha!') is a lightning bolt. "
            "Gate 23 (Clarity — ability to explain simply) is a glass prism. "
            "Lightning strikes prism, refracts into organized rainbow. Structuring."
        ),
    },
    44: {
        "name_64keys": "Collaboration",
        "name_ra": "Coming to Meet",
        "center": "Intuition",
        "partner_gates": [26],
        "channel_names": ["Surrender"],
        "circuits": ["Tribal Ego"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 44 (Collaboration — the nose for talent, pattern recognition). "
            "Gate 26 (Tactic — the trickster). The tactic must surrender to genuine collaboration. "
            "Surrender."
        ),
    },
    45: {
        "name_64keys": "Accumulation",
        "name_ra": "Gathering Together",
        "center": "Expression",
        "partner_gates": [21],
        "channel_names": ["Money"],
        "circuits": ["Tribal Ego"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 45 (Accumulation — gathering the tribe's wealth) is the king on the throne. "
            "Gate 21 (Authority) decides how resources flow. Together: Money."
        ),
    },
    46: {
        "name_64keys": "Dedication",
        "name_ra": "Pushing Upward",
        "center": "Identity",
        "partner_gates": [29],
        "channel_names": ["Discovery"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 46 (Dedication — love of the body, being in the right place). "
            "Gate 29 (Commitment — saying YES). When committed AND dedicated, "
            "you stumble into Discovery."
        ),
    },
    47: {
        "name_64keys": "Interpretation",
        "name_ra": "Oppression",
        "center": "Mind",
        "partner_gates": [64],
        "channel_names": ["Abstraction"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "A person in a lab coat (47) tries to interpret the kaleidoscopic patterns "
            "on the walls, reflected from a massive Rubik's Cube (64). The patterns are "
            "completely abstract — shifting, dissolving. Abstraction."
        ),
    },
    48: {
        "name_64keys": "Depth",
        "name_ra": "The Well",
        "center": "Intuition",
        "partner_gates": [16],
        "channel_names": ["The Wave Length"],
        "circuits": ["Collective Understanding"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 48 (Depth — deep knowledge, the well of talent) plays cello. "
            "Gate 16 (Identification — the enthusiastic practicer) plays guitar. "
            "They find the same Wave Length — mastery meets enthusiasm."
        ),
    },
    49: {
        "name_64keys": "Principles",
        "name_ra": "Revolution",
        "center": "Emotion",
        "partner_gates": [19],
        "channel_names": ["Synthesis"],
        "circuits": ["Tribal Defense"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 49 (Principles — the tribal judge) in robes. "
            "Gate 19 (Needs — hungry villagers banging on the door). "
            "Principles + Needs: the volatile Synthesis of survival and justice."
        ),
    },
    50: {
        "name_64keys": "Values",
        "name_ra": "The Cauldron",
        "center": "Intuition",
        "partner_gates": [27],
        "channel_names": ["Preservation"],
        "circuits": ["Tribal Defense"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 50 (Values — tribal laws, what's acceptable) is the family rulebook. "
            "Gate 27 (Caring — nourishment) is the parent cooking soup. "
            "Values + Caring = Preservation."
        ),
    },
    51: {
        "name_64keys": "Courage",
        "name_ra": "The Arousing",
        "center": "Willpower",
        "partner_gates": [25],
        "channel_names": ["Initiation"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 51 (Courage — competitive spirit, the jolt) is a thunderbolt striking "
            "behind a child (25, Naturalness). The child jumps. "
            "Initiation: the only channel that can initiate spiritual awakening through shock."
        ),
    },
    52: {
        "name_64keys": "Stillness",
        "name_ra": "Keeping Still",
        "center": "Drive",
        "partner_gates": [9],
        "channel_names": ["Concentration"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 52 (Stillness) is a perfectly still pond. Gate 9 (Focussing) is a laser beam. "
            "The beam hits the still pond and penetrates straight down. Concentration."
        ),
    },
    53: {
        "name_64keys": "Readiness",
        "name_ra": "Development",
        "center": "Drive",
        "partner_gates": [42],
        "channel_names": ["Maturation"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 53 (Readiness — pressure to start something new) is a seed eager to sprout. "
            "Gate 42 (Increase — growth, completion) is the fruit tree. "
            "Maturation: seed to tree to fruit to seed again."
        ),
    },
    54: {
        "name_64keys": "Ambition",
        "name_ra": "The Marrying Maiden",
        "center": "Drive",
        "partner_gates": [32],
        "channel_names": ["Transformation"],
        "circuits": ["Tribal Defense"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 54 (Ambition — drive to rise, transform social standing) is an employee "
            "on the factory floor, eyes burning to become CEO. Gate 32 (Continuity) checks: "
            "'Will this last?' When continuity says 'yes,' Transformation happens."
        ),
    },
    55: {
        "name_64keys": "Abundance",
        "name_ra": "Abundance",
        "center": "Emotion",
        "partner_gates": [39],
        "channel_names": ["Emoting"],
        "circuits": ["Individual Centering"],
        "difficulty": 3,
        "memory_hook": (
            "Gate 55 (Abundance — melancholy spirit, ecstasy and emptiness) sits alone. "
            "Gate 39 (Liberation — the provocateur) taps their shoulder: 'FEEL something.' "
            "Abundance erupts. Emoting."
        ),
    },
    56: {
        "name_64keys": "Stimulation",
        "name_ra": "The Wanderer",
        "center": "Expression",
        "partner_gates": [11],
        "channel_names": ["Curiosity"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 56 (Stimulation — the storyteller by the campfire). "
            "Gate 11 (Ideas — bursting with questions). "
            "'Tell me another one!' Pure Curiosity."
        ),
    },
    57: {
        "name_64keys": "Intuition",
        "name_ra": "The Gentle",
        "center": "Intuition",
        "partner_gates": [10, 20, 34],
        "channel_names": ["Perfected Form", "The Brain Wave", "Power"],
        "circuits": ["Integration"],
        "difficulty": 2,
        "memory_hook": (
            "Integration mega-hub. Gate 57 connects to 10, 20, and 34. "
            "Authentic intuition = Perfected Form. Strength guided by intuition = true Power."
        ),
    },
    58: {
        "name_64keys": "Joyfulness",
        "name_ra": "The Joyous",
        "center": "Drive",
        "partner_gates": [18],
        "channel_names": ["Judgment"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 58 (Joyfulness — vitality that fuels improvement). "
            "Gate 18 (Judgment — the drive to correct). "
            "Judgment + Joyfulness = the joy of making things better."
        ),
    },
    59: {
        "name_64keys": "Intimacy",
        "name_ra": "Dispersion",
        "center": "Life Force",
        "partner_gates": [6],
        "channel_names": ["Mating"],
        "circuits": ["Tribal Defense"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 59 (Intimacy — Sacral power to break through barriers). "
            "Gate 6 (Diplomacy — the door). "
            "Intimacy knocks; Diplomacy opens. Mating."
        ),
    },
    60: {
        "name_64keys": "Realism",
        "name_ra": "Limitation",
        "center": "Drive",
        "partner_gates": [3],
        "channel_names": ["Mutation"],
        "circuits": ["Individual Centering"],
        "difficulty": 1,
        "memory_hook": (
            "Gate 60 (Realism — limitation, constraints). Gate 3 IS Mutation. "
            "A caterpillar enters a chrysalis (60, the realistic limitation). "
            "Constraints enable transformation. Mutation."
        ),
    },
    61: {
        "name_64keys": "Exploration",
        "name_ra": "Inner Truth",
        "center": "Inspiration",
        "partner_gates": [24],
        "channel_names": ["Awareness"],
        "circuits": ["Individual Knowing"],
        "difficulty": 3,
        "memory_hook": (
            "A lighthouse (61) beaming into infinite darkness — exploring the unknown. "
            "Below, a hamster on a wheel (24, Introspection) running in circles. "
            "When the beam hits the wheel, the hamster stops. Awareness."
        ),
    },
    62: {
        "name_64keys": "Precision",
        "name_ra": "Preponderance of the Small",
        "center": "Expression",
        "partner_gates": [17],
        "channel_names": ["Acceptance"],
        "circuits": ["Collective Understanding"],
        "difficulty": 2,
        "memory_hook": (
            "Gate 62 (Precision — the accountant with a ruler) demands facts. "
            "Gate 17 (Opinions) shouts from a bullhorn. "
            "When Opinion speaks with Precision, the audience accepts. Acceptance."
        ),
    },
    63: {
        "name_64keys": "Verification",
        "name_ra": "After Completion",
        "center": "Inspiration",
        "partner_gates": [4],
        "channel_names": ["Logic"],
        "circuits": ["Collective Understanding"],
        "difficulty": 1,
        "memory_hook": (
            "The Verification officer (63) stamps a PhD thesis (4). "
            "'LOGIC APPROVED.' Thesis + verification = Logic."
        ),
    },
    64: {
        "name_64keys": "Reflection",
        "name_ra": "Before Completion",
        "center": "Inspiration",
        "partner_gates": [47],
        "channel_names": ["Abstraction"],
        "circuits": ["Collective Sensing"],
        "difficulty": 2,
        "memory_hook": (
            "The number 64 as a massive Rubik's Cube reflecting light onto the walls. "
            "A person (47) in a lab coat tries to interpret the kaleidoscopic patterns. "
            "The patterns are completely abstract. Abstraction."
        ),
    },
}


# All 36 channels with dual naming
CHANNELS: dict[str, dict] = {
    "Abstraction": {
        "gates": [47, 64],
        "centers": ["Mind", "Inspiration"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "name_ra": "[Ra name for 47-64 channel - TBD]",
        "memory_hook": (
            "A massive Rubik's Cube (64, Reflection) projects kaleidoscopic patterns. "
            "A scientist (47, Interpretation) tries to make sense of completely abstract patterns."
        ),
    },
    "Acceptance": {
        "gates": [17, 62],
        "centers": ["Mind", "Expression"],
        "circuit": "Collective Understanding",
        "difficulty": 2,
        "name_ra": "[Ra name for 17-62 channel - TBD]",
        "memory_hook": (
            "On a debate stage, Opinions (17) shouts passionately from a bullhorn. "
            "Precision (62) demands facts. When both align, the audience nods. Accepted."
        ),
    },
    "Awakening": {
        "gates": [10, 20],
        "centers": ["Identity", "Expression"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Being authentically present = waking up.",
    },
    "Awareness": {
        "gates": [24, 61],
        "centers": ["Mind", "Inspiration"],
        "circuit": "Individual Knowing",
        "difficulty": 3,
        "memory_hook": (
            "A lighthouse (61, Exploration) beaming into darkness. "
            "A hamster on a wheel (24, Introspection) running in circles. "
            "Beam hits wheel; hamster stops and looks up. Awareness."
        ),
    },
    "Charisma": {
        "gates": [20, 34],
        "centers": ["Expression", "Life Force"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Present strength is magnetic — charisma.",
    },
    "Community": {
        "gates": [37, 40],
        "centers": ["Emotion", "Willpower"],
        "circuit": "Tribal Ego",
        "difficulty": 2,
        "memory_hook": (
            "Loyalty (37) is the fireplace. Determination (40) is the breadwinner coming home. "
            "'I'll work for you if you keep the fire burning.' Community."
        ),
    },
    "Concentration": {
        "gates": [9, 52],
        "centers": ["Life Force", "Drive"],
        "circuit": "Collective Understanding",
        "difficulty": 1,
        "memory_hook": (
            "A laser beam (9, Focussing) hits a perfectly still pond (52, Stillness). "
            "The beam penetrates straight down. Concentration."
        ),
    },
    "Curiosity": {
        "gates": [11, 56],
        "centers": ["Mind", "Expression"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "memory_hook": (
            "A child (11, Ideas) tugging at a campfire storyteller (56, Stimulation). "
            "'Tell me another one!' Pure curiosity."
        ),
    },
    "Discovery": {
        "gates": [29, 46],
        "centers": ["Life Force", "Identity"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "memory_hook": (
            "Someone who says 'yes' to every door (29, Commitment) and trusts their "
            "body to lead them (46, Dedication) — they find things others walk past. Discovery."
        ),
    },
    "Emoting": {
        "gates": [39, 55],
        "centers": ["Drive", "Emotion"],
        "circuit": "Individual Centering",
        "difficulty": 3,
        "memory_hook": (
            "Liberation (39) taps Abundance (55) on the shoulder: 'FEEL something.' "
            "Abundance erupts — tears, laughter, rage, joy. That eruption IS Emoting."
        ),
    },
    "Exploration": {
        "gates": [10, 34],
        "centers": ["Identity", "Life Force"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Authentic strength explores fearlessly.",
    },
    "Initiation": {
        "gates": [25, 51],
        "centers": ["Identity", "Willpower"],
        "circuit": "Individual Centering",
        "difficulty": 3,
        "memory_hook": (
            "A child (25, Naturalness) at a cliff's edge. A thunderbolt (51, Courage) "
            "strikes behind them. The child jumps. Initiation: innocence meets shock."
        ),
    },
    "Inspiration": {
        "gates": [1, 8],
        "centers": ["Identity", "Expression"],
        "circuit": "Individual Knowing",
        "difficulty": 2,
        "memory_hook": (
            "A painter alone in a studio (1, Originality). "
            "A gallery owner bursts through the door (8, Promotion). "
            "Creative originality gets promoted. Inspiration."
        ),
    },
    "Judgment": {
        "gates": [18, 58],
        "centers": ["Intuition", "Drive"],
        "circuit": "Collective Understanding",
        "difficulty": 1,
        "memory_hook": "Gate 18 IS Judgment. Gate 58 (Joyfulness) fuels the drive to improve. The joy of making things better.",
    },
    "Logic": {
        "gates": [4, 63],
        "centers": ["Mind", "Inspiration"],
        "circuit": "Collective Understanding",
        "difficulty": 1,
        "memory_hook": "Verification (63) stamps a PhD thesis (4). 'LOGIC APPROVED.'",
    },
    "Maturation": {
        "gates": [42, 53],
        "centers": ["Life Force", "Drive"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "memory_hook": (
            "A fruit tree heavy with apples (42, Increase). A seed eager to sprout (53, Readiness). "
            "Maturation: seed to tree to fruit to seed again."
        ),
    },
    "Mating": {
        "gates": [6, 59],
        "centers": ["Emotion", "Life Force"],
        "circuit": "Tribal Defense",
        "difficulty": 1,
        "memory_hook": "Diplomacy (6) is the door. Intimacy (59) is someone knocking. Open the door: Mating.",
    },
    "Money": {
        "gates": [21, 45],
        "centers": ["Willpower", "Expression"],
        "circuit": "Tribal Ego",
        "difficulty": 1,
        "memory_hook": "'SHOW ME THE MONEY!' Authority (21) + Accumulation (45) = Money.",
    },
    "Mutation": {
        "gates": [3, 60],
        "centers": ["Life Force", "Drive"],
        "circuit": "Individual Centering",
        "difficulty": 1,
        "memory_hook": "Gate 3 IS Mutation. Gate 60 (Realism) is the chrysalis. Constraints enable transformation.",
    },
    "Openness": {
        "gates": [12, 22],
        "centers": ["Expression", "Emotion"],
        "circuit": "Individual Centering",
        "difficulty": 3,
        "memory_hook": (
            "An actor (12, Appropriateness) on stage. A moody audience member (22, Mood). "
            "When the actor is authentic and open, timing and emotion align. Openness."
        ),
    },
    "Perfected Form": {
        "gates": [10, 57],
        "centers": ["Identity", "Intuition"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Authentic intuition = the perfected form of being.",
    },
    "Power": {
        "gates": [34, 57],
        "centers": ["Life Force", "Intuition"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Strength guided by intuition = true power.",
    },
    "Preservation": {
        "gates": [27, 50],
        "centers": ["Life Force", "Intuition"],
        "circuit": "Tribal Defense",
        "difficulty": 2,
        "memory_hook": (
            "A parent cooking soup (27, Caring). The family rulebook on the wall (50, Values). "
            "'We eat together. We waste nothing.' Preservation."
        ),
    },
    "Recognition": {
        "gates": [30, 41],
        "centers": ["Emotion", "Drive"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "memory_hook": (
            "A bonfire (30, Feelings). A dreamer watching clouds (41, Hope). "
            "When Feelings gets ignited by Hope, you recognize what you truly desire. Recognition."
        ),
    },
    "Rhythm": {
        "gates": [5, 15],
        "centers": ["Life Force", "Identity"],
        "circuit": "Collective Understanding",
        "difficulty": 1,
        "memory_hook": "Gate 5 IS Rhythm. Gate 15 (Flexibility). Natural rhythm meets universal flexibility.",
    },
    "Struggle": {
        "gates": [28, 38],
        "centers": ["Intuition", "Drive"],
        "circuit": "Individual Centering",
        "difficulty": 2,
        "memory_hook": (
            "A cliff-diver (28, Risk) at the edge. The voice (38, Tenacity) says 'AGAIN.' "
            "Purposeful struggle. Not suffering — alive."
        ),
    },
    "Structuring": {
        "gates": [23, 43],
        "centers": ["Expression", "Mind"],
        "circuit": "Individual Knowing",
        "difficulty": 3,
        "memory_hook": (
            "A lightning bolt (43, Insight) strikes a glass prism (23, Clarity). "
            "Refracts into a perfectly organized rainbow. Raw flash to clean structure."
        ),
    },
    "Surrender": {
        "gates": [26, 44],
        "centers": ["Willpower", "Intuition"],
        "circuit": "Tribal Ego",
        "difficulty": 3,
        "memory_hook": (
            "A poker player (26, Tactic) going all-in, sliding cards face-down to the "
            "talent scout (44, Collaboration). The tactic must surrender."
        ),
    },
    "Synthesis": {
        "gates": [19, 49],
        "centers": ["Drive", "Emotion"],
        "circuit": "Tribal Defense",
        "difficulty": 3,
        "memory_hook": (
            "A courtroom judge (49, Principles) in robes. Hungry villagers (19, Needs) "
            "bang on the door. Needs + Principles: the volatile synthesis of survival and justice."
        ),
    },
    "The Alpha": {
        "gates": [7, 31],
        "centers": ["Identity", "Expression"],
        "circuit": "Collective Understanding",
        "difficulty": 2,
        "memory_hook": (
            "A wolf pack: the alpha (7, Strategy) chooses the direction. "
            "The pack (31, Influence) trusts its call. Strategy + Influence = The Alpha."
        ),
    },
    "The Beat": {
        "gates": [2, 14],
        "centers": ["Identity", "Life Force"],
        "circuit": "Individual Knowing",
        "difficulty": 2,
        "memory_hook": (
            "A compass needle (2, Orientation) listens for direction. "
            "A drum (14, Capacity) provides driving energy. "
            "The Beat: the pulse of resources flowing the right way."
        ),
    },
    "The Brain Wave": {
        "gates": [20, 57],
        "centers": ["Expression", "Intuition"],
        "circuit": "Integration",
        "difficulty": 1,
        "memory_hook": "Present intuition = a flash of knowing — brain wave.",
    },
    "The Prodigal": {
        "gates": [13, 33],
        "centers": ["Identity", "Expression"],
        "circuit": "Collective Sensing",
        "difficulty": 2,
        "memory_hook": (
            "A traveler (33, Prudence) returns home after hard lessons abroad. "
            "The listener (13, Mindfulness) sits by the hearth. "
            "The Prodigal: going out, gathering experience, returning with stories."
        ),
    },
    "The Wave Length": {
        "gates": [16, 48],
        "centers": ["Expression", "Intuition"],
        "circuit": "Collective Understanding",
        "difficulty": 3,
        "memory_hook": (
            "Two musicians: guitar (16, Identification) and cello (48, Depth). "
            "They can't play together until they find the same Wave Length."
        ),
    },
    "Transformation": {
        "gates": [32, 54],
        "centers": ["Intuition", "Drive"],
        "circuit": "Tribal Defense",
        "difficulty": 3,
        "memory_hook": (
            "A quality inspector (32, Continuity) at a factory. An employee (54, Ambition) "
            "wants to become CEO. When continuity says 'yes' to ambition: Transformation."
        ),
    },
    "Transitoriness": {
        "gates": [35, 36],
        "centers": ["Expression", "Emotion"],
        "circuit": "Collective Sensing",
        "difficulty": 3,
        "memory_hook": (
            "A bus labeled '35-36.' The driver (35, Progress) always moves forward. "
            "At the back, Compassion (36) weeps for everything left behind. "
            "The bus never stops. Everything is transitory."
        ),
    },
}


# Gates that are easily confused with each other
CONFUSABLE_CLUSTERS: dict[str, list[dict]] = {
    "Deep Thinking Gates": [
        {"gate": 24, "name": "Introspection", "distinction": "Mental looping — the hamster wheel. Repetitive."},
        {"gate": 47, "name": "Interpretation", "distinction": "Translating confusion into meaning. Translating."},
        {"gate": 43, "name": "Insight", "distinction": "Sudden breakthrough knowing — the 'aha!' Instantaneous."},
        {"gate": 61, "name": "Exploration", "distinction": "Pressure to know the unknowable. Mystical. Staring into the void."},
        {"gate": 64, "name": "Reflection", "distinction": "Mental review — replaying past images. Retrospective."},
    ],
    "Commitment Gates": [
        {"gate": 29, "name": "Commitment", "distinction": "Saying YES before knowing where it leads."},
        {"gate": 46, "name": "Dedication", "distinction": "Bodily trust — being in the right place."},
        {"gate": 40, "name": "Determination", "distinction": "Solitary work for the tribal bargain."},
        {"gate": 32, "name": "Continuity", "distinction": "Viability check — will this last?"},
    ],
    "Emotional Gates": [
        {"gate": 30, "name": "Feelings", "distinction": "Burning desire — can't let go. Burns."},
        {"gate": 22, "name": "Mood", "distinction": "Unpredictable shifts in emotional tone. Shifts."},
        {"gate": 36, "name": "Compassion", "distinction": "Naive yearning — the crisis-seeker. Yearns."},
        {"gate": 55, "name": "Abundance", "distinction": "Depth spectrum — ecstasy to despair. Depths."},
        {"gate": 58, "name": "Joyfulness", "distinction": "Root fuel vitality, NOT an emotion. Fuels."},
    ],
    "Power/Force Gates": [
        {"gate": 34, "name": "Strength", "distinction": "Pure Sacral energy — the workhorse. Works."},
        {"gate": 51, "name": "Courage", "distinction": "Shock, competitive spirit — the jolt. Shocks."},
        {"gate": 21, "name": "Authority", "distinction": "Control over resources and processes. Controls."},
        {"gate": 28, "name": "Risk", "distinction": "Finding meaning through danger. Gambles."},
        {"gate": 38, "name": "Tenacity", "distinction": "Stubborn persistence — won't quit. Refuses to stop."},
    ],
}


# Circuit group metadata
CIRCUIT_GROUPS: dict[str, dict] = {
    "Individual": {
        "theme": "Mutation, uniqueness, empowerment",
        "keyword": "I know / I feel",
        "feel": "Different, sudden, deaf to others",
        "sub_circuits": {
            "Individual Knowing": [
                "Awareness", "Structuring", "Inspiration", "The Beat",
            ],
            "Individual Centering": [
                "Mutation", "Openness", "Initiation", "Struggle", "Emoting",
            ],
            "Integration": [
                "Awakening", "Exploration", "Perfected Form",
                "Charisma", "The Brain Wave", "Power",
            ],
        },
    },
    "Collective": {
        "theme": "Sharing, patterns, experience",
        "keyword": "We think / We feel",
        "feel": "Social, cyclical, for the group",
        "sub_circuits": {
            "Collective Understanding": [
                "Logic", "Acceptance", "The Alpha", "Rhythm",
                "Concentration", "The Wave Length", "Judgment",
            ],
            "Collective Sensing": [
                "Abstraction", "Curiosity", "The Prodigal", "Discovery",
                "Maturation", "Transitoriness", "Recognition",
            ],
        },
    },
    "Tribal": {
        "theme": "Resources, loyalty, bargains",
        "keyword": "Our family",
        "feel": "Warm, bonded, deal-making",
        "sub_circuits": {
            "Tribal Ego": [
                "Money", "Surrender", "Community",
            ],
            "Tribal Defense": [
                "Mating", "Synthesis", "Preservation", "Transformation",
            ],
        },
    },
}
