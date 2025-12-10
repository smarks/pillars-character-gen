# Pillars: Combat and Movement Guide

---

## CORE CONCEPTS

### Attributes

| Attribute        | Abbreviation | Governs |
|------------------|--------------|---------|
| **Strength**     | ST           | Hit points, fatigue pool, carrying capacity |
| **Dexterity**    | DX           | Action order, success rolls, base movement, avoiding mishaps |
| **Intelligence** | IQ          | Number of skills/spells known, resistance to mental effects |
| **Wisdom**       | IQ          | Number of skills/spells known, resistance to mental effects |


## THE TURN

A turn represents approximately **five seconds** of action. Nothing happens simultaneously—each movement and action can affect what follows.

### Turn Sequence

| Phase | Name | Description                                                                                                                                                                                                      |
|-------|------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1 | **Initiative** | Players roll 1 d20 for each of their characters.                                                                                                                                                                 |
| 2 | **Renew Spells** | Pay ST to maintain continuing spells. Unrenewed spells end before movement.                                                                                                                                      |
| 3 | **Movement** | Character with the highest initiative moves or yields initiative. <br/>If a character yields they go last in order of initiative<br/>Movement stops upon engagement. <br/>Repeat for each character in order of initiative |
| 5 | **Actions** | All figures act in adjDX order (highest first). One action per character.                                                                                                                                        |
| 6 | **Forced Retreat** | Figures that dealt physical hits and took none may push enemies back 1 hex.                                                                                                                                      |
| 7 | **Cleanup** | Place dropped weapon counters. Flip slain/unconscious figures.                                                                                                                                                   |

---

## MOVEMENT

### Hex Size

A hex is approximately **4 feet (1.3 meters)** across—roughly the space one combatant controls in melee.
A mega hex is five adjunct hexes

![Mega hex](/images/megahex.png)
### Base Movement Allowance

**MA = DX − 2** (minimum 4)

| DX | Base MA |
|----|---------|
| 8  | 6 |
| 9  | 7 |
| 10 | 8 |
| 11 | 9 |
| 12 | 10 |
| 13 | 11 |
| 14 | 12 |

### Encumbrance

Encumbrance is based on weight carried compared to ST.

| Load Level | Weight Carried | MA Modifier | Restrictions |
|------------|----------------|-------------|--------------|
| Unencumbered | Up to ST lbs | 0 | — |
| Light | ST+1 to ST×1.5 lbs | −1 | — |
| Medium | ST×1.5+1 to ST×2 lbs | −2 | Cannot Run |
| Heavy | ST×2+1 to ST×2.5 lbs | −4 | Cannot Run or Jog |
| Overloaded | Over ST×2.5 lbs | Walk only, 1 hex max | — |

**Dropping a Pack:** Free action at the start of your movement. Recalculate encumbrance immediately. Picking up and securing a dropped pack takes one full turn (no other actions).

### Movement Speeds

| Speed | Distance | Fatigue Cost | Available Actions |
|-------|----------|--------------|-------------------|
| **Run** | Full MA | 1 per turn | None (movement only) |
| **Jog** | Half MA | 1 per 4 turns | Charge Attack, Dodge, Drop prone |
| **Walk** | Up to 2 hexes | None | Ready Weapon |
| **Walk (slow)** | Up to 1 hex | None | Cast Spell, Missile Attack, Disbelieve |
| **Stand Still** | 0 | None | Stand Up, Pick Up Weapon |

**Engaged figures** can only Shift (1 hex, stay adjacent) or Stand Still. Running and Jogging require being disengaged.

### Fatigue

**Fatigue Pool = ST**

| Activity | Fatigue Cost |
|----------|--------------|
| Running | 1 per turn |
| Jogging | 1 per 4 turns |
| Walking (combat) | None |
| Walking (travel) | Recover 1 per hour |
| Resting | Recover 1 per 10 minutes |

**Exhaustion:** When fatigue spent equals ST, you are **exhausted**:

- MA halved (round down)
- −2 DX on all rolls
- Cannot Run
- Must rest to recover

**Collapse:** If forced to spend fatigue beyond ST (e.g., spell casting, forced march), make a 3-dice save vs. ST or fall unconscious.

### Movement Example

A human with DX 10 and ST 10 carrying 18 lbs of gear:

- Base MA = 8 (DX 10 − 2)
- Encumbrance = Medium (18 lbs is between ST×1.5 and ST×2)
- MA Modifier = −2
- **Final MA = 6**
- Cannot Run (medium encumbrance)
- Jogging = 3 hexes, costs 1 fatigue per 4 turns

If they drop their pack (free action), they're now unencumbered:

- **MA = 8**
- Can Run at full MA, costing 1 fatigue per turn

---

## FACING

Each figure faces one hex side. This determines front, side, and rear hexes.

```
        [Front] [Front] [Front]
              \   |   /
               \  |  /
          [Side]--●--[Side]
                  |
               [Rear]
```

![Facing diagram](/images/facing.png)
- 
- **Physical attacks:** Only into your front hexes
- **Spells:** Your hex, adjacent hexes, or any hex "in front" of you
- **Prone/crawling figures:** All hexes count as rear (except for spell-casting direction)

---

## ENGAGEMENT

| Figure Type | Engaged When... |
|-------------|-----------------|
| One-hex figure | In an armed enemy's front hex |
| Giant or small dragon | In front hexes of 2+ one-hex figures (or 1 multi-hex figure) |
| 7-hex dragon | In front hexes of 3+ one-hex figures (or 1 multi-hex figure) |

- Figures **stop immediately** when they become engaged
- Multi-hex figures can push back smaller figures (combined ST of smaller figures must be less than pusher's ST)

---

## ACTIONS

### Disengaged Figure Actions

| Maximum Movement | Available Actions |
|------------------|-------------------|
| More than half MA | None (movement only) |
| Up to half MA | Charge Attack (melee or spell, not missiles), Dodge, Drop prone/kneeling |
| Up to 2 hexes | Ready New Weapon |
| Up to 1 hex | Cast Spell, Missile Attack, Disbelieve |
| Stand still | Stand Up (entire turn, no other action) |

### Engaged Figure Actions

| Maximum Movement | Available Actions |
|------------------|-------------------|
| Shift 1 hex (stay adjacent) | Melee Attack, Defend, Change Weapons, Attempt HTH, Cast Spell, Disbelieve, Disengage |
| Stand still | Last Missile Shot (must drop weapon next turn), Stand Up, Pick Up Weapon |

---

## ROLLING TO HIT

Roll **3 dice** and try to get your **adjusted DX or less**.

### DX Adjustments (Attacker)

| Situation | DX Adjustment |
|-----------|---------------|
| Striking from enemy's side hex | +2 |
| Striking from enemy's rear hex | +4 |
| Crossbowman firing from prone | +1 |
| Pole-weapon user standing still vs. charging opponent | +2 |
| Fighter striking with both hands (two weapons) | −4 on both attacks |

### DX Adjustments (Target)

| Target Situation | DX Adjustment |
|------------------|---------------|
| Target prone/kneeling (melee attack) | +4 |
| Target prone/kneeling (missile attack) | −4 |
| Flying 1-hex figure | −4 |
| Target in shadow | −2 |

### Automatic Results

| Roll | Result |
|------|--------|
| 3, 4, or 5 | Automatic hit (regardless of adjDX) |
| 16, 17, or 18 | Automatic miss |

---

## DAMAGE

### Taking Damage

- Damage is rolled on dice as specified by the weapon
- Protection (armor, natural armor) subtracts from each attack's damage
- **5+ hits in a turn:** −2 DX next turn
- **8+ hits in a turn:** Fall down immediately, lose your action if not yet taken

### Defending and Dodging

| Action | Effect |
|--------|--------|
| Defend (engaged) | Attacker must roll 4 dice instead of 3 |
| Dodge (disengaged) | Attacker must roll 4 dice instead of 3 |

On 4-dice rolls:

- 4–5 are automatic hits
- 20+ are automatic misses
- 21–22 dropped weapon
- 23–24 broken weapon

---

## SPECIAL MOVEMENT

### Forced Retreat

When you inflict physical damage and take none:

1. Push enemy back 1 hex in any direction
2. Choose to advance into vacated hex or stand still
3. If enemy has no hex to retreat to, they roll 3 dice vs. DX or fall

### Crawling and Prone

- Crawling MA = 2
- Crawling/prone figures have all rear hexes (cannot attack)
- Prone behind a body: missiles may hit the body instead (roll 1 die; 1–3 hits body if target prone, 1–4 if kneeling)

### Flight

- Half flying MA on takeoff turn
- Cannot move on landing turn
- Fliers don't engage ground figures unless they choose to
- Two fliers can pass at "different heights" if both agree

---

## QUICK REFERENCE SUMMARY

### Turn Order

1. Initiative (roll off, winner picks move order)
2. Renew Spells
3. Movement (by side, in initiative order)
4. Actions (by individual adjDX, highest first)
5. Forced Retreat

### Key Numbers

| Situation | Roll |
|-----------|------|
| To hit | 3 dice ≤ adjDX |
| Defending/Dodging target | 4 dice ≤ adjDX |
| Saving roll | 3 dice ≤ attribute (usually DX or IQ) |
| Auto-hit | 3, 4, or 5 |
| Auto-miss | 16, 17, or 18 |

### Movement Quick Reference

| DX | Base MA | Run (Full) | Jog (Half) |
|----|---------|------------|------------|
| 8  | 6 | 6 hexes | 3 hexes |
| 10 | 8 | 8 hexes | 4 hexes |
| 12 | 10 | 10 hexes | 5 hexes |
| 14 | 12 | 12 hexes | 6 hexes |

### Encumbrance Quick Reference

| Load | Weight | MA Mod | Can Run? | Can Jog? |
|------|--------|--------|----------|----------|
| Unencumbered | ≤ ST | 0 | Yes | Yes |
| Light | ≤ ST×1.5 | −1 | Yes | Yes |
| Medium | ≤ ST×2 | −2 | No | Yes |
| Heavy | ≤ ST×2.5 | −4 | No | No |
| Overloaded | > ST×2.5 | Walk only | No | No |

### Fatigue Quick Reference

### Fatigue Quick Reference

| Activity | Cost |
|----------|------|
| Run | 1 per turn |
| Jog (combat) | None |
| Jog (travel) | 1 per 10 min |
| Walk | None |
| Rest | Recover 1 per 10 min |
| Exhausted | −2 DX, half MA, no running |
