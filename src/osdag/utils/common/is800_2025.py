"""Module for Indian Standard, Draft IS 800 : 2025

Counterpart of is800_2007.py, following the same class/function structure.

Source: Draft IS 800:2025 (General Construction in Steel, Fourth Revision),
draft for comments. Clause numbers below refer to that draft.
"""
import math
from ...Common import *


class IS800_2025(object):
    """Perform calculations on steel design as per Draft IS 800:2025

    """

    # ==========================================================================
    """    CHAPTER  12     LIMIT STATE DESIGN   """
    # ==========================================================================
    # -------------------------------------------------------------
    #   12.4 Strength
    # -------------------------------------------------------------

    # Table 5 Partial Safety Factor for Materials, gamma_m (dict)
    # Reference: Draft IS 800:2025, Table 5, Clause 12.4.1
    # (Clause 5.4.1 in IS 800:2007; values are unchanged, only the clause number moved)
    cl_12_4_1_Table_5 = {"gamma_m0": {'yielding': 1.10, 'buckling': 1.10},
                         "gamma_m1": {'ultimate_stress': 1.25},
                         "gamma_mf": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mb": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mr": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.25},
                         "gamma_mw": {KEY_DP_FAB_SHOP: 1.25, KEY_DP_FAB_FIELD: 1.50}
                         }

    # ==========================================================================
    """    CHAPTER  13     DESIGN OF TENSION MEMBERS   """
    # ==========================================================================

    # ------------------------------------------------------------
    #   13.2 Design Strength due to Yielding of Gross Section
    # -------------------------------------------------------------

    @staticmethod
    def cl_13_2_tension_yielding_strength(A_g, f_y):
        """Calculate the design strength of a member in tension governed by yielding of the gross section

        Args:
            A_g: Gross area of cross section in sq. mm (float)
            f_y: Yield stress of the material in MPa (float)

        Return:
            T_dg: Design strength in tension due to yielding of gross section in N (float)

        Note:
            Reference:
            Draft IS 800:2025, cl. 13.2  (cl. 6.2 in IS 800:2007)

        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        T_dg = A_g * f_y / gamma_m0
        return T_dg

    # ------------------------------------------------------------
    #   13.3 Design Strength due to Rupture of Critical Section
    # -------------------------------------------------------------

    # cl. 13.3.1 Plates
    @staticmethod
    def cl_13_3_1_net_area_plate(b, t, n, d_h, staggered_legs=None, directly_punched=False):
        """Calculate the net effective area of a plate with bolt holes in the critical section

        Args:
            b: Width of the plate in mm (float)
            t: Thickness of the plate in mm (float)
            n: Number of bolt holes in the critical section (int)
            d_h: Diameter of the bolt hole in mm (float)
            staggered_legs: List of (p_s, g) tuples, one per inclined leg of the critical section, where
                            p_s is the staggered pitch and g is the gauge length between the bolt holes, both in mm
                            (list of tuples, optional; None means no staggered holes)
            directly_punched: True if the holes are directly punched; 2 mm is then added to d_h (bool)

        Return:
            A_n: Net effective area of the plate in sq. mm (float)

        Note:
            Assumption: d_h is the hole diameter itself, supplied by the caller (not the nominal bolt diameter).
            Reference:
            Draft IS 800:2025, cl. 13.3.1  (cl. 6.3.1 in IS 800:2007)

        """
        if directly_punched:
            d_h = d_h + 2.0
        staggered_term = 0.0
        for p_s, g in (staggered_legs or []):
            if g <= 0:
                raise ValueError("Gauge length g must be greater than zero")
            staggered_term += p_s ** 2 / (4.0 * g)
        A_n = (b - n * d_h + staggered_term) * t
        return A_n

    @staticmethod
    def cl_13_3_1_tension_rupture_strength(A_n, f_u):
        """Calculate the design strength of a plate in tension governed by rupture of the net cross section

        Args:
            A_n: Net effective area of the plate at the holes in sq. mm (float)
            f_u: Ultimate stress of the material in MPa (float)

        Return:
            T_dn: Design strength in tension due to rupture of the critical section in N (float)

        Note:
            Reference:
            Draft IS 800:2025, cl. 13.3.1  (cl. 6.3.1 in IS 800:2007)

        """
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        T_dn = 0.9 * A_n * f_u / gamma_m1
        return T_dn

    # cl. 13.3.2 Threaded rods
    @staticmethod
    def cl_13_3_2_threaded_rod_rupture_strength(A_n, f_u):
        """Calculate the design strength of a threaded rod in tension governed by rupture

        Args:
            A_n: Net root area at the threaded section in sq. mm (float)
            f_u: Ultimate stress of the material in MPa (float)

        Return:
            T_dn: Design strength of the threaded rod in tension due to rupture in N (float)

        Note:
            Reference:
            Draft IS 800:2025, cl. 13.3.2

        """
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        T_dn = 0.9 * A_n * f_u / gamma_m1
        return T_dn

    # cl. 13.3.3 Single angles
    @staticmethod
    def cl_13_3_3_shear_lag_factor_beta(w, t, b_s, L_c, f_y, f_u):
        """Calculate the shear lag factor, beta, for an angle connected through one leg

        Args:
            w: Outstand leg width in mm (float)
            t: Thickness of the leg in mm (float)
            b_s: Shear lag width in mm, as shown in Fig. 6 (float)
            L_c: Length of the end connection in mm, i.e. distance between the outermost bolts (or the length of
                 the weld) measured along the load direction (float)
            f_y: Yield stress of the material in MPa (float)
            f_u: Ultimate stress of the material in MPa (float)

        Return:
            beta: Shear lag factor (float)

        Note:
            beta = 1.4 - 0.076 (w/t) (f_y/f_u) (b_s/L_c), limited to a maximum of 0.9 f_u gamma_m0 / (f_y gamma_m1)
            and a minimum of 0.7.
            Assumption: the minimum of 0.7 is applied after the maximum limit.
            Reference:
            Draft IS 800:2025, cl. 13.3.3  (cl. 6.3.3 in IS 800:2007)

        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        beta = 1.4 - 0.076 * (w / t) * (f_y / f_u) * (b_s / L_c)
        beta_max = 0.9 * f_u * gamma_m0 / (f_y * gamma_m1)
        beta = min(beta, beta_max)
        beta = max(beta, 0.7)
        return beta

    @staticmethod
    def cl_13_3_3_single_angle_rupture_strength(A_nc, A_go, f_u, f_y, w, t, b_s, L_c):
        """Calculate the design strength of an angle connected through one leg, governed by rupture at the net section

        Args:
            A_nc: Net area of the connected leg in sq. mm (float)
            A_go: Gross area of the outstanding leg in sq. mm (float)
            f_u: Ultimate stress of the material in MPa (float)
            f_y: Yield stress of the material in MPa (float)
            w: Outstand leg width in mm (float)
            t: Thickness of the leg in mm (float)
            b_s: Shear lag width in mm, as shown in Fig. 6 (float)
            L_c: Length of the end connection in mm (float)

        Return:
            T_dn: Design strength in tension due to rupture at the net section in N (float)

        Note:
            Reference:
            Draft IS 800:2025, cl. 13.3.3  (cl. 6.3.3 in IS 800:2007)

        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        beta = IS800_2025.cl_13_3_3_shear_lag_factor_beta(w, t, b_s, L_c, f_y, f_u)
        T_dn = 0.9 * A_nc * f_u / gamma_m1 + beta * A_go * f_y / gamma_m0
        return T_dn

    # ------------------------------------------------------------
    #   13.4 Design Strength due to Block Shear
    # -------------------------------------------------------------

    # cl. 13.4.1 Bolted connections
    @staticmethod
    def cl_13_4_1_block_shear_strength(A_vg, A_vn, A_tg, A_tn, f_u, f_y):
        """Calculate the block shear strength of bolted connections

        Args:
            A_vg: Minimum gross area in shear along bolt line parallel to external force [in sq. mm] (float)
            A_vn: Minimum net area in shear along bolt line parallel to external force [in sq. mm] (float)
            A_tg: Minimum gross area in tension from the bolt hole to the toe of the angle,
                  end bolt line, perpendicular to the line of force [in sq. mm] (float)
            A_tn: Minimum net area in tension from the bolt hole to the toe of the angle,
                  end bolt line, perpendicular to the line of force [in sq. mm] (float)
            f_u: Ultimate stress of the material in MPa (float)
            f_y: Yield stress of the material in MPa (float)

        Return:
            T_db: Block shear strength of the bolted connection in N (float)

        Note:
            The smaller of the two failure modes governs.
            Reference:
            Draft IS 800:2025, cl. 13.4.1  (cl. 6.4.1 in IS 800:2007)

        """
        gamma_m0 = IS800_2025.cl_12_4_1_Table_5["gamma_m0"]['yielding']
        gamma_m1 = IS800_2025.cl_12_4_1_Table_5["gamma_m1"]['ultimate_stress']
        T_db1 = A_vg * f_y / (math.sqrt(3) * gamma_m0) + 0.9 * A_tn * f_u / gamma_m1
        T_db2 = 0.9 * A_vn * f_u / (math.sqrt(3) * gamma_m1) + A_tg * f_y / gamma_m0
        return min(T_db1, T_db2)

    # cl. 13.4.2 Welded connections: no closed-form equation in the draft; the block shear section must be
    # chosen by the designer around the end weld, so it is not implemented here.
