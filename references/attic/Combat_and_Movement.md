# Pillars: Combat and Movement Guide

*Updated to align with Handbook and The Weave*

---

## CORE CONCEPTS

### Attributes

| Attribute        | Abbreviation | Governs                                                      |
|------------------|--------------|--------------------------------------------------------------|
| **Strength**     | STR          | Weapon requirements, damage, carrying capacity               |
| **Dexterity**    | DEX          | Action order, to-hit rolls, base movement, avoiding mishaps  |
| **Intelligence** | INT          | Perception, arcane, learning skills, spell casting           |
| **Wisdom**       | WIS          | Insight, judgment, awareness, spell casting                  |
| **Constitution** | CON          | Health, endurance, damage capacity (add STR bonus/malus)     |
| **Charisma**     | CHR          | Influence, leadership, morale                                |

### Derived Pools

| Pool        | Formula                           | Governs                        |
|-------------|-----------------------------------|--------------------------------|
| **Fatigue** | CON + WIS + (DEX or STR) + 1d6    | Exhaustion, normal hit damage  |
| **Body**    | CON + (DEX or STR) + 1d6          | Wounds, critical hit damage    |
| **Mana**    | 3d6 (secret)                      | Spell casting (see The Weave)  |

---

## THE TURN

A turn represents approximately **five seconds** of action. Nothing happens simultaneously—each movement and action can affect what follows.

### Turn Sequence

| Phase | Name                 | Description                                                                 |
|-------|----------------------|-----------------------------------------------------------------------------|
| 1     | **Initiative**       | Each side rolls 1d6. Winner chooses to move first or second.                |
| 2     | **Renew Spells**     | Pay mana to maintain continuing spells. Unrenewed spells end before movement. |
| 3     | **Initial Movement** | Characters move by initiative order. Movement stops upon engagement.        |
| 4     | **Final Movement**   | Characters who yielded now move by initiative order.                        |
| 5     | **Actions**          | All figures act in adjDX order (highest first). One action per figure.      |
| 6     | **Forced Retreat**   | Figures that dealt damage and took none may push enemies back 1 hex.        |

### Available Actions 

#### Options for Disengaged Figures

| Option | Name              | Description                                                                                      |
|--------|-------------------|--------------------------------------------------------------------------------------------------|
| (a)    | **MOVE**          | Move up to full MA. No other action. Costs 1 fatigue per turn.                                   |
| (b)    | **CHARGE ATTACK** | Move up to ½ MA and attack with any weapon except missile, or attempt HTH.                      |
| (c)    | **DODGE**         | Move up to ½ MA. +1 die on to-hit roll if attacked by thrown/missile weapons or missile spells. |
| (d)    | **DROP**          | Move up to ½ MA and drop to prone or kneeling position.                                          |
| (e)    | **READY WEAPON**  | Move up to 2 hexes, re-sling weapon/shield, ready new weapon/shield or pick up dropped one.     |
| (f)    | **MISSILE ATTACK**| Move up to 1 hex and/or drop to prone/kneeling and/or fire missile weapon.                       |
| (g)    | **STAND UP**      | Rise from prone/kneeling, or crawl 2 hexes. No other action.                                     |
| (h)    | **CAST SPELL**    | Move 1 hex or stand still, and attempt any spell.                                                |
| (i)    | **DISBELIEVE**    | Move 1 hex or stand still, and attempt to disbelieve one illusion.                               |

#### Options for Engaged Figures

| Option | Name              | Description                                                                                      |
|--------|-------------------|--------------------------------------------------------------------------------------------------|
| (j)    | **SHIFT & ATTACK**| Shift 1 hex (or stand still) and attack with any non-missile weapon.                             |
| (k)    | **SHIFT & DEFEND**| Shift 1 hex (or stand still) and defend. +1 die on to-hit roll by melee/thrown attacks.         |
| (l)    | **ONE LAST SHOT** | Fire missile weapon if ready before engagement. Must drop bow next turn.                         |
| (m)    | **CHANGE WEAPONS**| Shift and drop ready weapon, ready a new non-missile weapon.                                     |
| (n)    | **DISENGAGE**     | Shift or stand still during movement. Move 1 hex any direction instead of attacking.            |
| (o)    | **ATTEMPT HTH**   | Move into adjacent enemy's hex with bare hands or dagger.                                        |
| (p)    | **STAND UP**      | Same as (g) above.                                                                               |
| (q)    | **PICK UP WEAPON**| Stand still, drop your weapon, pick up and ready a dropped weapon in your hex or adjacent.       |
| (r)    | **CAST SPELL**    | Shift 1 hex or stand still, and attempt any spell.                                               |
| (s)    | **DISBELIEVE**    | Same as (i) above.                                                                               |

#### Options for Figures in Hand-to-Hand Combat

| Option | Name              | Description                                                           |
|--------|-------------------|-----------------------------------------------------------------------|
| (t)    | **HTH ATTACK**    | Attempt to hit foe in same hex with bare hands or ready dagger.       |
| (u)    | **DRAW DAGGER**   | Requires successful 3d6 ≤ DEX roll.                                   |
| (v)    | **DISENGAGE**     | Roll 4d6 ≤ DEX. Success: stand up and move to adjacent empty hex.     |

---

## MOVEMENT

### Hex Size

A hex is approximately **4 feet (1.3 meters)** across—roughly the space one combatant controls in melee.

### Base Movement Allowance

**MA = DEX − 2** (minimum 4)

| DEX | Base MA |
|-----|---------|
| 8   | 6       |
| 9   | 7       |
| 10  | 8       |
| 11  | 9       |
| 12  | 10      |
| 13  | 11      |
| 14  | 12      |

### Encumbrance

Encumbrance is based on weight carried compared to STR.

| Load Level   | Weight Carried      | MA Modifier | Restrictions         |
|--------------|---------------------|-------------|----------------------|
| Unencumbered | Up to STR lbs       | 0           | —                    |
| Light        | STR+1 to STR×1.5    | −1          | —                    |
| Medium       | STR×1.5+1 to STR×2  | −2          | Cannot Run           |
| Heavy        | STR×2+1 to STR×2.5  | −4          | Cannot Run or Jog    |
| Overloaded   | Over STR×2.5        | Walk only   | 1 hex max            |

**Dropping a Pack:** Free action at the start of your movement. Picking up and securing a dropped pack takes one full turn.

### Movement Speeds

| Speed          | Distance   | Fatigue Cost                    | Available Actions              |
|----------------|------------|---------------------------------|--------------------------------|
| **Run**        | Full MA    | 1 per turn                      | None (movement only)           |
| **Jog**        | Half MA    | None (combat) / 1 per 10 min    | Charge Attack, Dodge, Drop     |
| **Walk**       | Up to 2 hex| None                            | Ready Weapon                   |
| **Walk (slow)**| Up to 1 hex| None                            | Cast Spell, Missile, Disbelieve|
| **Stand Still**| 0          | None                            | Stand Up, Pick Up Weapon       |

**Engaged figures** can only Shift (1 hex, stay adjacent) or Stand Still.

### Fatigue

**Fatigue Pool = CON + WIS + (DEX or STR) + 1d6**

| Activity           | Fatigue Cost         |
|--------------------|----------------------|
| Running            | 1 per turn           |
| Jogging (combat)   | None                 |
| Jogging (travel)   | 1 per 10 minutes     |
| Walking            | None                 |
| Walking (travel)   | Recover 1 per hour   |
| Resting            | Recover 1 per 10 min |

### Facing

Each figure faces one hex side. This determines front, side, and rear hexes.

- **Physical attacks:** Only into your front hexes
- **Spells:** Your hex, adjacent hexes, or any hex "in front" of you
- **Prone/crawling figures:** All hexes count as rear (except for spell-casting direction)

### Engagement

| Figure Type     | Engaged When...                                              |
|-----------------|--------------------------------------------------------------|
| One-hex figure  | In an armed enemy's front hex                                |
| 3–6 hex figure  | In front hexes of 2+ one-hex figures (or 1 multi-hex figure) |
| 7-hex figure    | In front hexes of 3+ one-hex figures (or 1 multi-hex figure) |

Figures **stop immediately** when they become engaged.

---

## ROLLING TO HIT

Roll **3d6** and try to get your **adjusted DEX or less**.

### Automatic Results

| Roll | Result                              |
|------|-------------------------------------|
| 3    | Automatic hit, **triple** damage    |
| 4    | Automatic hit, **double** damage, bleeding |
| 5    | Automatic hit                       |
| 16   | Automatic miss                      |
| 17   | Automatic miss, drop weapon         |
| 18   | Automatic miss, break weapon        |

### Damage Application

| Hit Type         | Damage Applied To        |
|------------------|--------------------------|
| Normal (5-15)    | Fatigue only             |
| Critical (3-4)   | Fatigue AND Body         |

### 4-Dice Results (vs Defending/Dodging)

| Roll  | Result                              |
|-------|-------------------------------------|
| 4-5   | Automatic hit                       |
| 20+   | Automatic miss                      |
| 21-22 | Automatic miss, drop weapon         |
| 23-24 | Automatic miss, break weapon        |

---

## DEX ADJUSTMENTS

All adjustments are cumulative.

### Positional Advantage (Physical Attacks)

| Situation                              | Adjustment |
|----------------------------------------|------------|
| Striking from enemy's side hex         | +2         |
| Striking from enemy's rear hex         | +4         |
| Pole-weapon vs. charging opponent      | +2         |
| Crossbow fired from prone              | +1         |
| Waiting for an opening (1 turn)        | +1         |
| Waiting for an opening (2+ turns)      | +2         |

### Target Conditions

| Condition                              | Adjustment |
|----------------------------------------|------------|
| Target is invisible                    | −6         |
| Target is in a shadow hex              | −4         |
| Target is a one-hex figure in flight   | −4         |
| Target is a giant snake                | −3         |
| Target is a multi-hex figure in flight | −1         |

### Your Conditions

| Condition                              | Adjustment |
|----------------------------------------|------------|
| In shadow hex or firing through shadow | −6         |
| Two-weapon fighting                    | −4 on both |
| Sweeping blow (all 3 front hexes)      | −4         |
| Standing in fire                       | −2         |
| Standing on a body                     | −2         |
| Moving over broken ground              | −2         |

### Range Adjustments

**Thrown Weapons:** −1 per hex to target

**Missile Weapons:**

| Range (Megahexes) | Adjustment |
|-------------------|------------|
| 0–2 MH            | 0          |
| 3–4 MH            | −1         |
| 5–6 MH            | −2         |
| 7–8 MH            | −3         |
| (continues)       | −1 per 2 MH|

### Armor and Shield Adjustments

| Equipment          | Adjustment |
|--------------------|------------|
| Small/spike shield | 0          |
| Large shield       | −1         |
| Tower shield       | −2         |
| Cloth armor        | −1         |
| Leather armor      | −2         |
| Chainmail          | −3         |
| Half-plate armor   | −4         |
| Plate armor        | −5         |

---

## INJURY & DEATH

### Injury Thresholds

These penalties apply based on your current Fatigue OR Body (whichever is worse):

| Condition                          | Effect                           |
|------------------------------------|----------------------------------|
| ½ Fatigue or Body (above 5)        | −1 to all rolls                  |
| 0-5 Fatigue or Body                | −2 to all rolls                  |
| 0 Fatigue or Body                  | Unconscious                      |
| Negative starting Fatigue or Body  | Saving throw vs death each turn  |
| Negative 2× starting value         | Dead                             |

### Protection

Armor and natural protection subtract hits **from each attack**.

---

## SPECIAL SITUATIONS

### Disengaging

**From Engaged (option n):**

- Shift 1 hex or stand still during movement phase
- Move 1 hex in any direction instead of attacking when your turn comes
- Faster enemies (higher adjDEX) can still strike you
- Slower enemies attack at penalty = difference in adjDEX

**From Hand-to-Hand (option v):**

- Roll 4d6 ≤ DEX
- Success: immediately stand up and move to adjacent empty hex
- Failure: remain in HTH

### Hand-to-Hand Combat

A figure may move into an enemy's hex if:

- Enemy has their back to the wall
- Enemy is down, prone, or kneeling
- Enemy has a lower MA
- Attacker comes in from the rear
- Enemy agrees to HTH combat

**HTH gives both combatants +4 DEX adjustment.**

**Bare-Handed Damage by STR:**

| STR       | Damage | STR       | Damage |
|-----------|--------|-----------|--------|
| 8 or less | 1d−4   | 17–20     | 1d+1   |
| 9–10      | 1d−3   | 21–24     | 1d+2   |
| 11–12     | 1d−2   | 25–30     | 1d+3   |
| 13–14     | 1d−1   | 31–40     | 2d+1   |
| 15–16     | 1d     | 41–50     | 3d+1   |

### Defending and Dodging

| Action  | Usable By         | Defends Against              | Effect              |
|---------|-------------------|------------------------------|---------------------|
| Dodge   | Disengaged figures| Missiles and thrown only     | Attacker rolls 4d6  |
| Defend  | Engaged figures   | Melee and non-missile only   | Attacker rolls 4d6  |

### Forced Retreat

If you dealt physical hits and took none:

1. Push enemy back 1 hex in any direction
2. Choose to advance into vacated hex or stand still
3. If enemy has no hex to retreat to, they roll 3d6 ≤ DEX or fall

---

## QUICK REFERENCE

### Key Formulas

| Calculation       | Formula                          |
|-------------------|----------------------------------|
| Movement          | MA = DEX − 2 (min 4)             |
| Fatigue           | CON + WIS + (DEX or STR) + 1d6   |
| Body              | CON + (DEX or STR) + 1d6         |
| To Hit            | 3d6 ≤ adjDEX                     |
| vs Defend/Dodge   | 4d6 ≤ adjDEX                     |

### Auto-Results (3d6)

| Roll | Result                    |
|------|---------------------------|
| 3    | Triple damage             |
| 4    | Double damage + bleeding  |
| 5    | Auto-hit                  |
| 16   | Auto-miss                 |
| 17   | Drop weapon               |
| 18   | Break weapon              |

### Encumbrance Quick Reference

| Load         | Weight     | MA Mod | Run? | Jog? |
|--------------|------------|--------|------|------|
| Unencumbered | ≤ STR      | 0      | Yes  | Yes  |
| Light        | ≤ STR×1.5  | −1     | Yes  | Yes  |
| Medium       | ≤ STR×2    | −2     | No   | Yes  |
| Heavy        | ≤ STR×2.5  | −4     | No   | No   |
| Overloaded   | > STR×2.5  | Walk   | No   | No   |

### Injury Quick Reference

| Condition     | Effect              |
|---------------|---------------------|
| ½ pool        | −1 to rolls         |
| 0-5 pool      | −2 to rolls         |
| 0 pool        | Unconscious         |
| Negative      | Save vs death/turn  |
| Negative 2×   | Dead                |

---

*Pillars Combat Guide v2 — Aligned with Handbook and The Weave*