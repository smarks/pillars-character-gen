# Magic Mechanics (GM Reference)

This chapter contains the specific mechanical details players don't see. The [public rulebook](/html/public-rulebook/#magic) describes magic in general terms; here are the exact numbers.

### Contents

- [Mana Pool](#mana-pool)
- [Casting Roll](#casting-roll)
- [Special Casting Rolls](#special-casting-rolls)
- [Push](#push)
- [Control Results](#control-results)
- [Borrowing Mechanics](#borrowing-mechanics)
- [Channel](#channel)
- [Runaway](#runaway)
- [Counterspell Mechanics](#counterspell-mechanics)

---

## Mana Pool

**Roll:** 3d6 at character creation (secret from player)

## Casting Roll

**Casting Roll:** 3d6 ≤ adjINT or adjWIS (depending on the spell). Rolls of 3-5 and 16-18 have special effects per the table below.

## Special Casting Rolls

| Roll | Result                                             |
| ---- | -------------------------------------------------- |
| 3    | Critical success—GM determines bonus effect        |
| 4    | Strong success—minor bonus                         |
| 5    | Clean success                                      |
| 16   | Fumble—spell fails, minor consequence              |
| 17   | Bad fumble—spell fails, mana lost, negative effect |
| 18   | Catastrophic—triggers Runaway                      |

## Push

If you push, it makes it harder to succeed but the resulting spell is more powerful. 

Control Roll: 3d6 ≤ INT, with penalty equal to total mana invested.
Penalty = −(total mana invested)

Example: A mage with INT 12 pushes 4 mana into a spell. Their Control Roll is 3d6 ≤ 8 (12 − 4). If they pushed 7 mana, they'd need 3d6 ≤ 5.

The effects of pushing mana varies based on spell. See GM 

## Control Results

| Result      | Outcome                  |
| ----------- | ------------------------ |
| Success     | Spell works as intended  |
| Fail by 1-3 | Minor deviation          |
| Fail by 4-6 | Significant deviation    |
| Fail by 7+  | **RUNAWAY**              |
| Natural 18  | **RUNAWAY** (regardless) |

## Borrowing Mechanics

1. Spend all remaining mana
2. Borrow remainder → becomes Debt
3. Debt Roll after spell: 3d6 ≤ (INT + WIS − Debt)
4. Channel is hard cap—can't exceed even by Borrowing

## Channel

Channel represents how much mana a caster can safely control at once.

- **Recipe Magic:** Channel equals the caster's skill level in that specific spell.
- **True Magic:** Channel equals the caster's Arcane skill level (which costs double skill points to advance).

Channel is the hard cap—you cannot exceed it even by Borrowing.

## Runaway

When a caster loses control, the spell begins feeding on them.

**Each turn:**

- Spell drains mana equal to original casting cost
- Spell effect grows unpredictably (GM determines)

**At 0 mana:** Caster falls unconscious. Spell drains Body instead.

**Death:** When Body reaches negative full starting value.

**Anchoring:**

- **Conscious caster:** 3d6 ≤ WIS to regain control
- **Third party mage:** Invest mana equal to original spell cost, roll 3d6 ≤ INT. Failure = both caught in Runaway.

**Once anchored:** Controller may continue the spell normally or end it.

## Counterspell Mechanics

**Initial Counter:**
1. Higher adjDEX defender: declare counter + commit mana (their action)
2. Caster's action: declare spell, pay mana
3. Lower adjDEX defender: may counter when action comes
4. Opposed INT roll: +1 per 3 mana invested
5. Ties: caster wins

**Resolution:**
- Caster wins: Spell goes off
- Defender wins: Spell countered; caster may escalate next turn

**Escalation (Turn 2+):**
- Only caster can escalate—defender gets one shot
- Caster's action: pay mana again, new opposed INT roll
- Defender chooses: oppose (pay mana again) or let spell succeed
- Ends when: caster succeeds, caster stops, defender stops, or Runaway


