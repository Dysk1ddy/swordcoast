# Damage Reduction Formula with Strong Level Scaling

## Purpose

This formula calculates **Damage Reduction (DR)** for an RPG combat system using two main factors:

- **Defense**: The defender's armor, toughness, or defensive stat.
- **Level Difference**: Whether the defender is higher or lower level than the enemy.

The formula is designed so that:

- Defense has a logarithmic curve.
- Defense gives strong early gains but slows down near the cap.
- Equal-level enemies use the normal defense curve.
- Higher-level enemies make DR weaker.
- Lower-level enemies make DR stronger.
- DR is clamped so it cannot become negative or too close to full immunity.

---

## Base Damage Reduction Formula

This is the baseline formula when the player and enemy are the same level:

```text
DR_base = 80 * ln(1 + 0.18 * (Defense - 10)) / ln(3.16)
```

Where:

- `Defense` is the defender's defense stat.
- `ln` is the natural logarithm.
- `10` is the minimum defense value where DR starts at 0.
- `22` is the defense value where DR reaches 80.
- `80` is the base DR cap before level scaling.
- `0.18` controls the steepness of the curve.
- `ln(3.16)` normalizes the curve so Defense 22 equals 80 DR.

---

## Base DR Table at Equal Level

| Defense | Base DR |
|---:|---:|
| 10 | 0.00 |
| 11 | 12.06 |
| 12 | 21.73 |
| 13 | 30.16 |
| 14 | 37.63 |
| 15 | 44.39 |
| 16 | 50.55 |
| 17 | 56.23 |
| 18 | 61.49 |
| 19 | 66.36 |
| 20 | 70.91 |
| 21 | 75.18 |
| 22 | 80.00 |

---

## Level Scaling

Level scaling changes how effective defense is based on the difference between the player and enemy level.

```text
level_diff = player_level - enemy_level
```

Then:

```text
level_multiplier = 1 + 0.08 * level_diff
```

This means each level difference changes DR by **8%**.

| Level Situation | Level Difference | Multiplier | Effect |
|---|---:|---:|---|
| Enemy is 3 levels higher | -3 | 0.76 | DR is 24% weaker |
| Enemy is 2 levels higher | -2 | 0.84 | DR is 16% weaker |
| Enemy is 1 level higher | -1 | 0.92 | DR is 8% weaker |
| Equal level | 0 | 1.00 | Normal DR |
| Enemy is 1 level lower | 1 | 1.08 | DR is 8% stronger |
| Enemy is 2 levels lower | 2 | 1.16 | DR is 16% stronger |
| Enemy is 3 levels lower | 3 | 1.24 | DR is 24% stronger |

---

## Final Recommended Formula

```text
DR = clamp(
    80 * ln(1 + 0.18 * (Defense - 10)) / ln(3.16)
    * (1 + 0.08 * (player_level - enemy_level)),
    0,
    90
)
```

Where:

- `clamp(value, 0, 90)` prevents DR from going below 0 or above 90.
- `player_level - enemy_level` controls whether defense becomes stronger or weaker.
- A higher-level enemy reduces the effectiveness of defense.
- A lower-level enemy increases the effectiveness of defense.

---

## Example at 18 Defense

At equal level, 18 Defense gives:

```text
DR_base = 61.49
```

After level scaling:

| Enemy Level Compared to Player | Level Difference | Multiplier | Final DR |
|---|---:|---:|---:|
| 3 levels higher | -3 | 0.76 | 46.72 |
| 2 levels higher | -2 | 0.84 | 51.65 |
| 1 level higher | -1 | 0.92 | 56.57 |
| Equal level | 0 | 1.00 | 61.49 |
| 1 level lower | 1 | 1.08 | 66.41 |
| 2 levels lower | 2 | 1.16 | 71.33 |
| 3 levels lower | 3 | 1.24 | 76.25 |

---

## Design Notes

This formula is useful for an RPG system where defense should remain important without becoming overpowered.

The logarithmic curve means each additional point of Defense gives less benefit than the previous one. This prevents high-defense builds from scaling too aggressively from the stat alone.

The level multiplier makes enemy level matter. Fighting stronger enemies weakens the player's DR, while fighting weaker enemies makes the player's DR more effective. This helps higher-level enemies feel threatening even if the player has strong defense.

The final clamp of 90 prevents extreme cases where DR becomes too high and turns into near-total immunity.

---

## Implementation Notes

If the game engine does not have a built-in `clamp` function, it can be implemented like this:

```text
clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    if value > max_value:
        return max_value
    return value
```

In Python-style pseudocode:

```python
import math

def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def calculate_dr(defense, player_level, enemy_level):
    base_dr = 80 * math.log(1 + 0.18 * (defense - 10)) / math.log(3.16)
    level_multiplier = 1 + 0.08 * (player_level - enemy_level)
    final_dr = base_dr * level_multiplier
    return clamp(final_dr, 0, 90)
```
