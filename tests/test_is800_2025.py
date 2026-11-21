"""Unit tests for osdag/utils/common/is800_2025.py

Run from the repository's src directory (or wherever osdag is importable):
    pytest tests/test_is800_2025.py -v

Expected values are hand-calculated from the Draft IS 800:2025 clauses (working shown in comments).
"""
import math
import pytest

# Osdag's real Common.py has heavy import-time side effects (a circular import with component.py, and database
# queries such as connectdb("Bolt")), which are not needed to test pure calculations. The IS 800 modules only
# use the two constants below, so a minimal stand-in for osdag.Common is registered before they are imported.
import sys
import types

_common_stub = types.ModuleType("osdag.Common")
_common_stub.KEY_DP_FAB_SHOP = "Shop"
_common_stub.KEY_DP_FAB_FIELD = "Field"
sys.modules["osdag.Common"] = _common_stub

from osdag.Common import KEY_DP_FAB_SHOP, KEY_DP_FAB_FIELD
from osdag.utils.common.is800_2025 import IS800_2025
from osdag.utils.common.is800_2007 import IS800_2007


# ---------------------------------------------------------------- Table 5 (cl. 12.4.1)
def test_table_5_values():
    t = IS800_2025.cl_12_4_1_Table_5
    assert t["gamma_m0"]["yielding"] == 1.10
    assert t["gamma_m0"]["buckling"] == 1.10
    assert t["gamma_m1"]["ultimate_stress"] == 1.25
    assert t["gamma_mw"][KEY_DP_FAB_SHOP] == 1.25
    assert t["gamma_mw"][KEY_DP_FAB_FIELD] == 1.50


def test_table_5_unchanged_from_2007():
    # Draft 2025 Table 5 (cl. 12.4.1) has the same values as IS 800:2007 Table 5 (cl. 5.4.1)
    assert IS800_2025.cl_12_4_1_Table_5 == IS800_2007.cl_5_4_1_Table_5


# ---------------------------------------------------------------- cl. 13.2 yielding
def test_tension_yielding_strength():
    # T_dg = A_g f_y / gamma_m0 = 1000 * 250 / 1.10 = 227272.73 N
    assert IS800_2025.cl_13_2_tension_yielding_strength(1000, 250) == pytest.approx(227272.73, rel=1e-6)


# ---------------------------------------------------------------- cl. 13.3.1 plates
def test_net_area_no_stagger():
    # A_n = (b - n d_h) t = (200 - 2*20) * 10 = 1600 mm^2
    assert IS800_2025.cl_13_3_1_net_area_plate(200, 10, 2, 20) == pytest.approx(1600.0)


def test_net_area_with_stagger():
    # p_s^2 / (4 g) = 40^2 / (4*50) = 8 ; A_n = (200 - 3*22 + 8) * 10 = 1420 mm^2
    assert IS800_2025.cl_13_3_1_net_area_plate(200, 10, 3, 22, [(40, 50)]) == pytest.approx(1420.0)


def test_net_area_directly_punched_adds_2mm():
    # d_h = 20 + 2 = 22 -> same result as the staggered case above
    assert IS800_2025.cl_13_3_1_net_area_plate(200, 10, 3, 20, [(40, 50)], directly_punched=True) == pytest.approx(1420.0)


def test_net_area_zero_gauge_raises():
    with pytest.raises(ValueError):
        IS800_2025.cl_13_3_1_net_area_plate(200, 10, 3, 22, [(40, 0)])


def test_plate_rupture_strength():
    # T_dn = 0.9 A_n f_u / gamma_m1 = 0.9 * 800 * 410 / 1.25 = 236160 N
    assert IS800_2025.cl_13_3_1_tension_rupture_strength(800, 410) == pytest.approx(236160.0)


# ---------------------------------------------------------------- cl. 13.3.2 threaded rods
def test_threaded_rod_rupture_strength():
    # T_dn = 0.9 * 500 * 410 / 1.25 = 147600 N
    assert IS800_2025.cl_13_3_2_threaded_rod_rupture_strength(500, 410) == pytest.approx(147600.0)


# ---------------------------------------------------------------- cl. 13.3.3 single angles
def test_beta_normal_case():
    # w/t = 10, f_y/f_u = 250/410, b_s/L_c = 140/150
    # beta = 1.4 - 0.076 * 10 * 0.60976 * 0.93333 = 0.96748 (within limits 0.7 and 1.2989)
    assert IS800_2025.cl_13_3_3_shear_lag_factor_beta(100, 10, 140, 150, 250, 410) == pytest.approx(0.96748, abs=1e-5)


def test_beta_lower_limit():
    # raw beta = 1.4 - 0.076 * 20 * 0.60976 * 1.0 = 0.473 -> limited to 0.7
    assert IS800_2025.cl_13_3_3_shear_lag_factor_beta(100, 5, 100, 100, 250, 410) == pytest.approx(0.7)


def test_beta_upper_limit():
    # raw beta = 1.4 - 0.076 * 2 * 0.60976 * 0.1 = 1.3907
    # upper limit = 0.9 * f_u * gamma_m0 / (f_y * gamma_m1) = 0.9 * 410 * 1.10 / (250 * 1.25) = 1.29888
    assert IS800_2025.cl_13_3_3_shear_lag_factor_beta(20, 10, 10, 100, 250, 410) == pytest.approx(1.29888, abs=1e-5)


def test_single_angle_rupture_strength():
    # beta = 0.96748 (see test_beta_normal_case)
    # T_dn = 0.9 * 600 * 410 / 1.25 + 0.96748 * 500 * 250 / 1.10
    #      = 177120 + 109940.9 = 287060.9 N
    result = IS800_2025.cl_13_3_3_single_angle_rupture_strength(600, 500, 410, 250, 100, 10, 140, 150)
    assert result == pytest.approx(287060.9, rel=1e-5)


# ---------------------------------------------------------------- cl. 13.4.1 block shear
def test_block_shear_strength_takes_smaller_mode():
    # A_vg=2000, A_vn=1500, A_tg=800, A_tn=600, f_u=410, f_y=250
    # T_db1 = 2000*250/(sqrt(3)*1.10) + 0.9*600*410/1.25 = 262431.4 + 177120 = 439551.9 N
    # T_db2 = 0.9*1500*410/(sqrt(3)*1.25) + 800*250/1.10 = 255650.7 + 181818.2 = 437468.9 N
    # smaller governs -> 437468.9 N
    result = IS800_2025.cl_13_4_1_block_shear_strength(2000, 1500, 800, 600, 410, 250)
    assert result == pytest.approx(437468.9, rel=1e-6)


def test_block_shear_same_as_2007():
    args = (2000, 1500, 800, 600, 410, 250)
    assert IS800_2025.cl_13_4_1_block_shear_strength(*args) == pytest.approx(
        IS800_2007.cl_6_4_1_block_shear_strength(*args))
