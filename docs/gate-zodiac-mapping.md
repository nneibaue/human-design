# Human Design: Gates and Zodiac Degree Mapping

## Overview

In Human Design, the **64 I Ching hexagrams (gates)** are mapped onto the **360° tropical zodiac circle** through a structure called the **Rave Mandala Wheel**. This document explains how this mapping works and provides references for further study.

## The Mathematical Foundation

### Basic Calculation

- **360° zodiac ÷ 64 gates = 5.625° per gate**
- Each gate spans exactly **5°37'30"** (5 degrees, 37 minutes, 30 seconds)
- Each gate contains **6 lines**, with each line spanning **56'15"** (56 minutes, 15 seconds)

### Zodiac Sign Bases

The tropical zodiac is divided into 12 signs of 30° each:

| Sign | Abbreviation | Start Degree |
|------|--------------|--------------|
| Aries | AR | 0° |
| Taurus | TA | 30° |
| Gemini | GE | 60° |
| Cancer | CA | 90° |
| Leo | LE | 120° |
| Virgo | VI | 150° |
| Libra | LI | 180° |
| Scorpio | SC | 210° |
| Sagittarius | SG | 240° |
| Capricorn | CP | 270° |
| Aquarius | AQ | 300° |
| Pisces | PI | 330° |

## Gate Sequence Around the Wheel

The gates are **not** arranged in numerical order around the zodiac. Instead, they follow a specific sequence established by Ra Uru Hu (the founder of Human Design) that is unique to this system.

### Example: Gate 25 (Aries Boundary)

Gate 25 demonstrates the wrap-around principle:

```
Gate 25: 28°15' Pisces → 3°52'30" Aries
```

This gate spans the **0° Aries point** (vernal equinox), so in code it's represented as two segments:
- Pisces portion: 358°15' to 360° (358.25° to 360°)
- Aries portion: 0° to 3°52'30" (0° to 3.875°)

### Gates by Zodiac Sign

Each zodiac sign contains approximately 5-6 gates (since 30° ÷ 5.625° ≈ 5.33 gates per sign).

#### Aries (0° - 30°)
| Gate | Start | End |
|------|-------|-----|
| 25 | 0°00'00" | 3°52'30" |
| 17 | 3°52'30" | 9°30'00" |
| 21 | 9°30'00" | 15°07'30" |
| 51 | 15°07'30" | 20°45'00" |
| 42 | 20°45'00" | 26°22'30" |
| 3 | 26°22'30" | (continues into Taurus) |

*Note: Gate 25 begins in late Pisces (28°15') and wraps into early Aries.*

## Key Concepts

### 1. Tropical vs Sidereal Zodiac

Human Design uses the **tropical zodiac**, which is based on the seasons (vernal equinox = 0° Aries). This differs from Vedic/Jyotish astrology, which uses the sidereal zodiac based on fixed star positions.

### 2. The Rave Mandala

The Rave Mandala is the circular diagram that shows:
- The 12 zodiac signs (outer ring)
- The 64 gates positioned at their specific degrees
- The I Ching hexagram symbols
- The relationship between planetary positions and gate activations

### 3. Gate-to-Hexagram Correspondence

Each of the 64 gates corresponds to one of the 64 I Ching hexagrams. However, the arrangement around the wheel does **not** follow the traditional King Wen sequence used in the I Ching book. Ra Uru Hu's arrangement is specific to Human Design.

### 4. Lines Within Gates

Each gate is subdivided into 6 lines:
- **Line 1**: Foundation/Investigator
- **Line 2**: Hermit/Natural
- **Line 3**: Martyr/Adaptation
- **Line 4**: Opportunist/Network
- **Line 5**: Heretic/Projection
- **Line 6**: Role Model/Transition

Each line spans 56'15" of zodiacal arc.

## How Planetary Activations Work

When calculating a Human Design chart:

1. **Calculate planetary longitude** using ephemeris data (Swiss Ephemeris)
2. **Find the gate** that contains that longitude
3. **Calculate the line** based on position within the gate
4. **Record as Gate.Line** (e.g., "25.3" = Gate 25, Line 3)

This is done for:
- **Personality (Conscious)**: Planetary positions at birth time
- **Design (Unconscious)**: Planetary positions when Sun was 88° earlier

## Implementation Notes

The code in `calculatebackup.py` implements this mapping:

```python
def _d(sign_base: float, deg: int, minutes: int = 0, seconds: int = 0) -> float:
    """Convert sign-relative position to absolute degrees."""
    return sign_base + deg + minutes / 60.0 + seconds / 3600.0

def _add(gate: int, start: float, end: float) -> None:
    """Add a gate range to the lookup table."""
    GATE_RANGES.append((gate, start, end))
```

---

## References

### Primary Sources

1. **Jovian Archive** - Official custodian of Ra Uru Hu's Human Design work
   - Website: https://jovianarchive.com
   - Contains original teachings and certified educational materials

2. **Ra Uru Hu** - Founder of Human Design (1948-2011)
   - Received the "transmission" on January 3, 1987 in Ibiza, Spain
   - Developed the system over 25 years

### Software & Tools

3. **Genetic Matrix** - Human Design charting software
   - Website: https://www.geneticmatrix.com
   - Provides gates-by-degree charts and tropical/sidereal options
   - One of the most comprehensive HD software platforms

4. **Swiss Ephemeris** - Astronomical calculation library
   - Website: https://www.astro.com/swisseph/
   - Used for planetary longitude calculations
   - Python binding: `pyswisseph`

### I Ching Background

5. **King Wen Sequence** - Traditional I Ching hexagram ordering
   - Wikipedia: https://en.wikipedia.org/wiki/King_Wen_sequence
   - Note: Human Design uses a different arrangement

6. **I Ching (Book of Changes)** - Ancient Chinese divination text
   - The 64 hexagrams form the basis of HD gates
   - Each hexagram has 6 lines, corresponding to gate lines

### Educational Resources

7. **Human Design America**
   - Website: https://www.humandesignamerica.com
   - Offers educational programs and professional training

8. **International Human Design School (IHDS)**
   - Official certification body for HD professionals
   - Maintains standards for HD education

### Technical References

9. **Tropical Zodiac**
   - Based on Earth's relationship to the Sun
   - 0° Aries = Vernal Equinox (Northern Hemisphere Spring)
   - Seasons-based, not star-based

10. **Ephemeris Data**
    - JPL (Jet Propulsion Laboratory) planetary data
    - Swiss Ephemeris implementation: most accurate available

---

## Further Reading

### Books
- *The Definitive Book of Human Design* by Lynda Bunnell and Ra Uru Hu
- *Human Design: The Revolutionary System* by Chetan Parkyn
- *Understanding Human Design* by Karen Curry Parker

### Online Courses
- Jovian Archive certification programs
- Genetic Matrix tutorials and webinars
- BG5 (Business applications of Human Design)

### Community Resources
- Human Design forums and Facebook groups
- Professional analyst directories
- Regional Human Design organizations

---

## Notes on Data Accuracy

When comparing HD calculations across different software:

1. **Ephemeris differences** - Some use Swiss Ephemeris, others use JPL directly
2. **Node calculation** - True Node vs Mean Node can differ
3. **Boundary rounding** - Exact gate boundaries may vary slightly
4. **Timezone handling** - Critical for accurate birth time conversion

The gate degree mapping in this project follows the standard tropical zodiac positions as documented by Genetic Matrix and other major HD software providers.

---

*Document created: December 31, 2025*
*Related code: calculatebackup.py, calculate.py*
