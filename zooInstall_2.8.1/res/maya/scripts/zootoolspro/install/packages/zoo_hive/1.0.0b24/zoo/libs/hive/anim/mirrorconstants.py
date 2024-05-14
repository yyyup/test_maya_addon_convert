"""Constants for mirroring Hive components and IDs

"""

# ---------------------------
# COMPONENT ANIMATION FLIP ATTRIBUTES
# ---------------------------

FLIP_STANDARD_WORLD = ["translateX", "rotateY", "rotateZ"]
FLIP_STANDARD_FK = ["translateX", "translateY", "translateZ"]
FLIP_BENDY_WORLD = ["translateY"]
# LEG (legcomponent) ----------------------
LEG_DICT = {"endik": FLIP_STANDARD_WORLD,
            "upVec": FLIP_STANDARD_WORLD,
            "controlPanel": [],
            "uprTwist": FLIP_STANDARD_FK,
            "lwrTwist": FLIP_STANDARD_FK,
            "toeTap_piv": [],
            "toeTip_piv": [],
            "outer_piv": [],
            "inner_piv": [],
            "heel_piv": [],
            "ballroll_piv": [],
            "lwrTwistOffset": [],
            "uprTwistOffset": [],
            "baseik": FLIP_STANDARD_WORLD,
            "endfk": FLIP_STANDARD_FK,
            "midfk": FLIP_STANDARD_FK,
            "ballfk": FLIP_STANDARD_FK,
            "uprfk": FLIP_STANDARD_FK,
            "bendy01": FLIP_BENDY_WORLD,
            "bendyMid00": FLIP_BENDY_WORLD,
            "bendyMid01": FLIP_BENDY_WORLD,
            "tangent00Out": FLIP_BENDY_WORLD,
            "tangent01In": FLIP_BENDY_WORLD,
            "tangent01Out": FLIP_BENDY_WORLD,
            "tangent02In": FLIP_BENDY_WORLD
            }

# ARM (armcomponent) ----------------------
ARM_DICT = {"endik": FLIP_STANDARD_FK,
            "upVec": FLIP_STANDARD_WORLD,
            "controlPanel": [],
            "uprTwist": FLIP_STANDARD_FK,
            "lwrTwist": FLIP_STANDARD_FK,
            "lwrTwistOffset": [],
            "uprTwistOffset": [],
            "baseik": FLIP_STANDARD_FK,
            "endfk": FLIP_STANDARD_FK,
            "midfk": FLIP_STANDARD_FK,
            "uprfk": FLIP_STANDARD_FK,
            "bendy01": FLIP_BENDY_WORLD,
            "bendyMid00": FLIP_BENDY_WORLD,
            "bendyMid01": FLIP_BENDY_WORLD,
            "tangent00Out": FLIP_BENDY_WORLD,
            "tangent01In": FLIP_BENDY_WORLD,
            "tangent01Out": FLIP_BENDY_WORLD,
            "tangent02In": FLIP_BENDY_WORLD
            }

# FKCHAIN (fkchain) ----------------
FK_DICT = {"fk": FLIP_STANDARD_FK,
           "controlPanel": []}

# FINGER (finger) ----------------------
FINGER_DICT = FK_DICT

# HEAD_DICT (headcomponent) ----------------------
HEAD_DICT = {"controlPanel": [],
             "neck": [],
             "head": []}

# VCHAIN (vchaincomponent) ----------------------
VCHAIN_DICT = {"controlPanel": [],
               "endik": FLIP_STANDARD_FK,
               "upVec": FLIP_STANDARD_WORLD,
               "uprTwist": FLIP_STANDARD_FK,
               "lwrTwist": FLIP_STANDARD_FK,
               "lwrTwistOffset": [],
               "uprTwistOffset": [],
               "baseik": FLIP_STANDARD_FK,
               "endfk": FLIP_STANDARD_FK,
               "midfk": FLIP_STANDARD_FK,
               "uprfk": FLIP_STANDARD_FK,
               "bendy01": FLIP_STANDARD_FK,
               "bendyMid00": FLIP_STANDARD_WORLD,
               "bendyMid01": FLIP_STANDARD_FK,
               "tangent00Out": FLIP_STANDARD_WORLD,
               "tangent01In": FLIP_STANDARD_WORLD,
               "tangent01Out": FLIP_STANDARD_FK,
               "tangent02In": FLIP_STANDARD_FK
               }

# AIM (aimcomponent) ----------------------
AIM_DICT = {"controlPanel": [],
            "eye": FLIP_STANDARD_FK,
            "aim": ["rotateY", "rotateZ", "translateX", "translateY", "translateZ"]}

# SPINEFK (spineFk) ----------------------
SPINEFK_DICT = {"controlPanel": [],
                "hips": FLIP_STANDARD_WORLD,
                "cog": FLIP_STANDARD_WORLD,
                "gimbal": FLIP_STANDARD_WORLD,
                "fk": FLIP_STANDARD_FK}

# SPINEIK (spineIk) ----------------------
SPINEIK_DICT = {"controlPanel": [],
                "hips": FLIP_STANDARD_FK,
                "hipSwing": FLIP_STANDARD_FK,
                "cog": FLIP_STANDARD_FK,
                "cogGimbal": FLIP_STANDARD_FK,
                "fk": FLIP_STANDARD_FK,
                "ctrl": FLIP_STANDARD_FK,
                "tweaker00": FLIP_STANDARD_FK,
                "tweaker01": FLIP_STANDARD_FK,
                "tweaker02": FLIP_STANDARD_FK,
                "worldUpVec": []}

# JAW (jaw) ----------------------
JAW_DICT = {"controlPanel": [],
            "rotAll": FLIP_STANDARD_FK,
            "topLip": FLIP_STANDARD_FK,
            "botLip": FLIP_STANDARD_FK,
            "jaw": FLIP_STANDARD_FK}

# ------------------- MAIN FLIP DICTIONARY ----------------------------
FLIP_ATTR_DICT = {"legcomponent": LEG_DICT,
                  "finger": FINGER_DICT,
                  "fkchain": FK_DICT,
                  "armcomponent": ARM_DICT,
                  "headcomponent": HEAD_DICT,
                  "vchaincomponent": VCHAIN_DICT,
                  "aimcomponent": AIM_DICT,
                  "spineIk": SPINEIK_DICT,
                  "spineFk": SPINEFK_DICT,
                  "jaw": JAW_DICT}
