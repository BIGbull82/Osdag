# Osdag Screening Task: Draft IS 800:2025 Implementation

**Name:** _<your name>_  **Repository / branch:** _<link>_  **Video:** _<unlisted link>_

## 1. Scope and approach

I read the existing `is800_2007.py` first and copied its structure: one class (`IS800_2025`), every function a `@staticmethod`, `cl_<clause>_<description>` naming, `Args / Return / Note: Reference` docstrings with units, and partial safety factors read from a class-level dictionary rather than hard-coded. I chose a focused scope, **partial safety factors and tension member design (Chapter 13)**, and aimed for correct, documented, tested code rather than breadth.

## 2. Clauses and functions implemented

| Draft IS 800:2025 clause | Function | Corresponds to IS 800:2007 |
|---|---|---|
| 12.4.1, Table 5 | `cl_12_4_1_Table_5` (dict) | cl. 5.4.1, Table 5 |
| 13.2 Yielding of gross section | `cl_13_2_tension_yielding_strength` | cl. 6.2 |
| 13.3.1 Rupture, plates | `cl_13_3_1_net_area_plate`, `cl_13_3_1_tension_rupture_strength` | cl. 6.3.1 |
| 13.3.2 Rupture, threaded rods | `cl_13_3_2_threaded_rod_rupture_strength` | cl. 6.3.2 |
| 13.3.3 Rupture, single angles (shear lag) | `cl_13_3_3_shear_lag_factor_beta`, `cl_13_3_3_single_angle_rupture_strength` | cl. 6.3.3 |
| 13.4.1 Block shear, bolted | `cl_13_4_1_block_shear_strength` | cl. 6.4.1 |

Not implemented: 13.3.4 (other sections; it reuses the 13.3.3 equation with a different definition of `b_s`) and 13.4.2 (welded block shear; the draft gives no equation, only that the designer must choose the section).

## 3. Comparison: IS 800:2007 vs Draft IS 800:2025

| Provision | Change | Notes |
|---|---|---|
| Table 5 partial safety factors | **Renumbered only** (5.4.1 → 12.4.1) | All values identical: γm0 = 1.10, γm1 = 1.25, γmf/γmb/γmr = 1.25, γmw = 1.25 (shop) / 1.50 (field). |
| Tension yielding | **Renumbered only** (6.2 → 13.2) | T_dg = A_g f_y / γm0, unchanged. |
| Plate rupture | **Renumbered only** (6.3.1 → 13.3.1) | T_dn = 0.9 A_n f_u / γm1; net area expression unchanged, including the +2 mm allowance for directly punched holes. |
| Threaded rods | Renumbered (6.3.2 → 13.3.2) | T_dn = 0.9 A_n f_u / γm1. Not implemented in the Osdag 2007 module, so added here. |
| Single angles, shear lag | Renumbered (6.3.3 → 13.3.3); **no technical change relative to the amended 2007** | Draft: β ≤ 0.9 f_u γm0 / (f_y γm1), β ≥ 0.7. The original IS 800:2007 (Dec 2007) had no 0.9 in this limit; Amendment No. 1 (Jan 2012) to IS 800:2007 substituted "0.9 fu γm0/fy γm1" for "fu γm0/fy γm1" in cl. 6.3.3, so the draft carries the amendment forward. Not in the Osdag 2007 module, so added here. |
| Block shear (bolted) | **Renumbered only** (6.4.1 → 13.4.1) | Both failure-mode equations unchanged. |
| Welded block shear | Renumbered (13.4.2) | Descriptive only; no equation. |

**Basis of comparison.** "2007" in this comparison means IS 800:2007 as amended by Amendment No. 1 (January 2012). For the provisions implemented, the draft's technical content is the same as the amended 2007; the visible changes are the renumbering (and the consolidation of the 2012 amendment into the main text).

Chapter numbering moved overall (Tension Members: Section 6 → Chapter 13; Limit State Design: Section 5 → Chapter 12), so the function names carry the new clause numbers.

## 4. Assumptions and interpretations

1. **Draft status.** The source is a draft for comments; clause numbers and values may change in the final standard.
2. **Hole diameter `d_h`.** `cl_13_3_1_net_area_plate` takes `d_h` as the hole diameter itself (supplied by the caller). If `directly_punched=True`, 2 mm is added, per the clause.
3. **Staggered holes.** Each inclined leg is passed as a `(p_s, g)` pair, and the term p_s² / 4g is summed over all legs.
4. **β limits.** The draft states β ≤ upper limit and β ≥ 0.7 without an order of application. I apply the upper limit first and the 0.7 minimum last.
5. **Units.** N, mm and MPa throughout, as in the 2007 module.
6. **Safety factors** are read from `cl_12_4_1_Table_5` so a future change needs editing in one place.

## 5. Challenges

- The draft is renumbered, so 2007 clause numbers could not be used to locate provisions; I located them through the draft's contents page.
- The 2007 Osdag module does not implement 6.3.2 to 6.3.4, so for those provisions the comparison relies on the standard's text rather than existing code.
- Ambiguities in the β limits and in the meaning of `d_h` (assumptions 2 and 4) had to be resolved by interpretation.
- Osdag's `Common.py`, which the IS 800 modules import for the fabrication constants, cannot be imported in isolation: it has a circular import with `component.py` (importing `osdag.Common` first fails with a `NameError`, even for the existing 2007 module) and it queries a database table (`Bolt`) at import time. The unit tests therefore register a minimal stand-in for `osdag.Common` (just `KEY_DP_FAB_SHOP` and `KEY_DP_FAB_FIELD`) so the pure calculations are tested independently of the database. I did not change Osdag's own files.
- Observations on the 2007 module (not changed): the docstring of `cl_6_2_tension_yielding_strength` says "rupture ... clause 6.3.1" (a copy-paste slip), and `cl_10_3_3_bolt_shear_capacity` accepts `safety_factor_parameter` but always uses the shop factor.

## 6. Testing

`test_is800_2025.py` contains 15 pytest tests with hand-calculated expected values (working shown in comments), including checks that Table 5 and the block shear equation match the 2007 module. To run: place the file in the repository's tests folder and run `pytest test_is800_2025.py -v` from a directory where `osdag` is importable (for example with `src` on `PYTHONPATH`).
