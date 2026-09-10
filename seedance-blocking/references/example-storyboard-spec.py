# Kellanova / Pringles — 60s, one continuous take, locked-off camera.
# Storyboard: 15 scenes. Solid objects blocked, fluids left as gaps, hand blocked.
#
# SUBJECT is a CARRIER, not a real object: an invisible static proxy at the centre
# of the arrangement, sized like one can, so the camera has something to hold and
# the camera gates have something to measure. It is never built in Blender.
# With a carrier and a locked-off rig the camera gates pass trivially and prove
# nothing — the choreography gate is what actually proves this film. Run both.
#
# GEOMETRY
#   camera sits at y = -6.5, looking down +Y. Smaller y = nearer camera.
#   FRONT slot   x=0.00  y=-1.60  scale 1.00   (hero: near, large, overlapping)
#   ARC (behind) y≈+1.30..1.45    scale 0.55   (five seats, tight enough that the
#                                                front silhouette cuts across them)
#   LINE-UP      y=+0.60          scale 0.80   (scene 13: all equal, standing clear)

FRONT = [0.00, -1.60, 0.00]
ARC = {
    "bacon":  [-0.75, 1.42, 0.00],
    "cheese": [-0.39, 1.33, 0.00],
    "pizza":  [ 0.00, 1.30, 0.00],
    "herbs":  [ 0.39, 1.33, 0.00],
    "steak":  [ 0.75, 1.42, 0.00],
}
BACK = 0.55
HERO = 1.00

SHOT = {
    "name": "kellanova", "fps": 24, "seconds": 60,
    "rig": "tripod",

    "subject": {                       # CARRIER — see header
        "mode": "profile",
        "size": [0.60, 0.60, 1.60],
        "axis": "y",
        "start": [0.0, 0.0, 0.0],
        "speed": [(0.0, 0.0), (60.0, 0.0)],
    },

    "shots": [
        {"t0": 0.0, "t1": 60.0, "name": "oner", "camera": {
            "fit": 0.55,
            "aim_distance": 5.0,
            "waypoints": [
                {"t":  0.0, "pos": [0.0, -6.5, 1.2], "lens": 40, "aim": [0, 0, 0.2]},
                {"t": 60.0, "pos": [0.0, -6.5, 1.2], "lens": 40, "aim": [0, 0, 0.2]},
            ]}},
    ],

    "cast": {
        "bacon":  {"size": [0.60, 0.60, 1.60], "color": "red"},
        "cheese": {"size": [0.60, 0.60, 1.60], "color": "cyan"},
        "pizza":  {"size": [0.60, 0.60, 1.60], "color": "orange"},
        "herbs":  {"size": [0.60, 0.60, 1.60], "color": "green"},
        "steak":  {"size": [0.60, 0.60, 1.60], "color": "purple"},
        "logo":   {"size": [1.40, 0.05, 0.40], "color": "white", "role": "graphic"},
        "handL":  {"size": [0.45, 0.30, 0.22], "color": "yellow", "role": "graphic"},
        "handR":  {"size": [0.45, 0.30, 0.22], "color": "yellow", "role": "graphic"},
    },

    # (t, name, [x,y,z], scale). A member absent before its first key or after its
    # last is off screen — that is how things enter and leave.
    "choreography": [
        # ---- SCENE 1 (0-3): logo alone --------------------------------------
        (0.0,  "logo", [0.0, 0.0, 0.0], 0.10),
        (1.2,  "logo", [0.0, 0.0, 0.0], 1.00),
        (2.4,  "logo", [0.0, 0.0, 0.0], 1.00),
        (3.0,  "logo", [0.0, 0.0, 0.0], 0.10),

        # ---- SCENE 2 (3-7): five cans arrive in the arc ----------------------
        (3.2,  "bacon",  ARC["bacon"],  0.05), (7.0, "bacon",  ARC["bacon"],  BACK),
        (3.2,  "cheese", ARC["cheese"], 0.05), (7.0, "cheese", ARC["cheese"], BACK),
        (3.2,  "pizza",  ARC["pizza"],  0.05), (7.0, "pizza",  ARC["pizza"],  BACK),
        (3.2,  "herbs",  ARC["herbs"],  0.05), (7.0, "herbs",  ARC["herbs"],  BACK),
        (3.2,  "steak",  ARC["steak"],  0.05), (7.0, "steak",  ARC["steak"],  BACK),

        # ---- SCENE 3-4 (7-14.5): BACON forward, bursts, returns --------------
        # bacon leaves the arc the instant the carousel window opens at 7.0s —
        # a window with no one in front is exactly the line-up the gate rejects.
        (8.2,  "bacon", FRONT, HERO), (14.0, "bacon", FRONT, HERO),
        (16.4, "bacon", ARC["bacon"], BACK),

        # ---- SCENE 5-6 (14.5-21.5): CHEESE forward --------------------------
        (14.0, "cheese", ARC["cheese"], BACK),
        (15.2, "cheese", FRONT, HERO), (21.0, "cheese", FRONT, HERO),
        (22.5, "cheese", ARC["cheese"], BACK),

        # ---- SCENE 7-8 (21.5-28): PIZZA forward -----------------------------
        (21.0, "pizza", ARC["pizza"], BACK),
        (22.2, "pizza", FRONT, HERO), (27.5, "pizza", FRONT, HERO),
        (29.0, "pizza", ARC["pizza"], BACK),

        # ---- SCENE 9-10 (28-35): HERBS forward ------------------------------
        (27.5, "herbs", ARC["herbs"], BACK),
        (28.7, "herbs", FRONT, HERO), (34.5, "herbs", FRONT, HERO),
        (36.0, "herbs", ARC["herbs"], BACK),

        # ---- SCENE 11-12 (35-41.5): STEAK forward ---------------------------
        (34.5, "steak", ARC["steak"], BACK),
        (35.7, "steak", FRONT, HERO), (40.8, "steak", FRONT, HERO),
        (42.0, "steak", ARC["steak"], BACK),

        # ---- SCENE 13 (41.5-47.5): the line-up, all equal, standing clear ----
        # the carousel window closes at 42.0s: from here the five are equals on
        # purpose, so the solo/overlap rules no longer apply.
        (42.0, "bacon",  ARC["bacon"],  BACK),
        (42.0, "cheese", ARC["cheese"], BACK),
        (42.0, "pizza",  ARC["pizza"],  BACK),
        (42.0, "herbs",  ARC["herbs"],  BACK),
        (47.5, "bacon",  [-3.00, 0.60, 0.0], 0.80),
        (47.5, "cheese", [-1.50, 0.60, 0.0], 0.80),
        (47.5, "pizza",  [ 0.00, 0.60, 0.0], 0.80),
        (47.5, "herbs",  [ 1.50, 0.60, 0.0], 0.80),
        (47.5, "steak",  [ 3.00, 0.60, 0.0], 0.80),

        # ---- SCENE 14 (47.5-56): a hand takes bacon and passes it right -----
        (48.5, "handL", [-5.20, -0.60, 0.0], 1.00),
        (50.5, "handL", [-3.00,  0.35, 0.0], 1.00),
        (52.5, "handL", [-0.40,  0.10, 0.0], 1.00),
        (54.0, "handL", [-5.20, -0.60, 0.0], 1.00),
        (51.5, "handR", [ 5.20, -0.60, 0.0], 1.00),
        (52.5, "handR", [ 0.60,  0.10, 0.0], 1.00),
        (55.5, "handR", [ 5.20, -0.60, 0.0], 1.00),
        (50.5, "bacon", [-3.00, 0.55, 0.0], 0.80),
        (52.5, "bacon", [ 0.10, 0.10, 0.0], 0.85),
        (55.5, "bacon", [ 5.20,-0.60, 0.0], 0.80),
        # the other four fade out as the hand carries bacon away
        (52.0, "cheese", [-1.50, 0.60, 0.0], 0.80), (55.0, "cheese", [-1.50, 0.60, 0.0], 0.05),
        (52.0, "pizza",  [ 0.00, 0.60, 0.0], 0.80), (55.0, "pizza",  [ 0.00, 0.60, 0.0], 0.05),
        (52.0, "herbs",  [ 1.50, 0.60, 0.0], 0.80), (55.0, "herbs",  [ 1.50, 0.60, 0.0], 0.05),
        (52.0, "steak",  [ 3.00, 0.60, 0.0], 0.80), (55.0, "steak",  [ 3.00, 0.60, 0.0], 0.05),

        # ---- SCENE 15 (56-60): logo returns and holds ------------------------
        (56.2, "logo", [0.0, 0.0, 0.0], 0.10),
        (57.4, "logo", [0.0, 0.0, 0.0], 1.00),
        (60.0, "logo", [0.0, 0.0, 0.0], 1.00),
    ],

    # The carousel runs from the moment the first can steps forward (7.0s) until
    # the line-up starts forming (42.0s). Before 7.0s the five arrive as equals in
    # the arc and NO ONE is meant to be in front — scene 2 is the establishing
    # arrangement, not a swap. After 42.0s they deliberately stand clear.
    "front_zone": {"solo_from": 8.2, "solo_until": 41.5},

    "beats": [
        (0.0,  "SCENE 1 — logo alone, centre, grows in from nothing and holds"),
        (3.0,  "SCENE 2 — logo shrinks away; five cans arrive in a shallow arc, all equal, none in front"),
        (7.0,  "SCENE 3 — BACON travels FORWARD out of the arc, growing; the other four stay back and are cut off by it"),
        (9.5,  "SCENE 4 — GAP: fat, sizzle and crumbs are fluid, not blocked. Blocked: pan slab + crisp disc leave the can and return"),
        (14.5, "SCENE 5 — BACON falls back into the arc; CREAM CHEESE travels FORWARD"),
        (16.5, "SCENE 6 — GAP: spread and herb bits are fluid. Blocked: bowl cyl + knife slab + crisp disc out and back"),
        (21.5, "SCENE 7 — CHEESE returns; PIZZA travels FORWARD"),
        (23.5, "SCENE 8 — GAP: tomato splash is fluid. Blocked: pizza disc spins alongside a crisp disc"),
        (28.0, "SCENE 9 — PIZZA returns; MED HERBS travels FORWARD"),
        (30.0, "SCENE 10 — GAP: falling herb bits are particles. Blocked: platter disc + two olive spheres on a stick"),
        (35.0, "SCENE 11 — HERBS returns; STEAK travels FORWARD, last of the five"),
        (37.0, "SCENE 12 — GAP: sizzle and smoke are fluid. Blocked: grill slab + steak slab out and back"),
        (41.5, "SCENE 13 — the arc opens out and all five settle into a straight line at equal size, standing clear"),
        (47.5, "SCENE 14 — a hand box enters from the left, takes BACON, carries it right; a second hand takes it off frame right; the other four fade out"),
        (56.0, "SCENE 15 — hands and can gone; the logo grows back in at centre and holds to the end"),
    ],
}
