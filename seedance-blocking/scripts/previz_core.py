"""
previz_core.py -- Blender-resident blocking API for the seedance-blocking skill.

THERE ARE NO ENVIRONMENTS IN HERE. On purpose.

A previz set is always the same six ideas: a ground, some slabs, some repeated
rows of slabs, a few lights, some colour-coded markers, and the actor. A corridor,
a city street, a subway platform and a forest clearing are all that, arranged
differently. So this file ships the PARTS and the shot spec composes the place.
Adding a named environment here would mean editing the skill every time the user
names somewhere new, which is exactly the wrong shape.

Pushed into the live Blender ONCE per session and parked in
bpy.app.driver_namespace["PV"], so later calls are one-liners.

Blender 5.2 LTS. Z-up, metres, radians.
"""
import bpy, math, os, json
from mathutils import Matrix, Vector

# ============================================================ scene setup ===
def reset(fps=24, seconds=30, res=(1920, 1080), engine='BLENDER_EEVEE',
          world_rgb=(0.020, 0.026, 0.038)):
    sc = bpy.context.scene
    sc.render.fps = fps
    sc.frame_start, sc.frame_end = 1, int(round(seconds * fps))
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.engine = engine
    for n in ("Cube", "Light", "Camera"):
        o = bpy.data.objects.get(n)
        if o: bpy.data.objects.remove(o, do_unlink=True)
    sc.timeline_markers.clear()
    w = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*world_rgb, 1.0)
    return {"frames": [sc.frame_start, sc.frame_end], "fps": fps}

def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c

def wipe(prefixes=("SET_", "MK_", "HERO", "RIG_", "CAM_", "AIM_", "LGT_")):
    """Clear a previous blocking pass without touching anything else."""
    n = 0
    for o in list(bpy.data.objects):
        if any(o.name.startswith(p) for p in prefixes):
            bpy.data.objects.remove(o, do_unlink=True); n += 1
    for a in list(bpy.data.actions):
        if a.users == 0: bpy.data.actions.remove(a, do_unlink=True)
    bpy.context.scene.timeline_markers.clear()
    return n

# =============================================================== materials ==
PALETTE = {
    "red":    (0.620, 0.055, 0.045), "cyan":   (0.05, 0.45, 0.55),
    "green":  (0.10, 0.45, 0.13),    "yellow": (0.70, 0.55, 0.06),
    "blue":   (0.08, 0.15, 0.55),    "magenta":(0.55, 0.06, 0.42),
    "orange": (0.72, 0.28, 0.04),    "purple": (0.30, 0.10, 0.52),
    "black":  (0.020, 0.020, 0.022), "dark":   (0.085, 0.088, 0.092),
    "grey":   (0.28, 0.29, 0.28),    "light":  (0.52, 0.53, 0.51),
    "white":  (0.72, 0.72, 0.70),
}
def mat(name, color, rough=0.7, metal=0.0, emit=0.0):
    rgb = PALETTE.get(color, color) if isinstance(color, str) else color
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled"); b.location = (100, 0)
    nt.links.new(b.outputs["BSDF"], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1.0)      # SOLID viewport reads THIS, not the nodes
    m.roughness = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m

def _matfor(color, emit=0.0, rough=0.7, metal=0.0):
    key = color if isinstance(color, str) else "c%d" % (hash(tuple(color)) & 0xffff)
    return mat(f"MAT_{key}{'_e' if emit else ''}", color, rough, metal, emit)

# ============================================== THE PARTS (compose with these)
def slab(name, size, loc, color="grey", rot=(0, 0, 0), emit=0.0, rough=0.7,
         metal=0.0, base=False, collection="SET"):
    """One box. The universal building unit: floors, walls, facades, kerbs,
    platforms, crates, roofs, steps. base=True spans z 0..h instead of centring."""
    C = coll(collection)
    o = bpy.data.objects.get(name)
    if o is None:
        me = bpy.data.meshes.new(name + "_m")
        sx, sy, sz = size[0]/2, size[1]/2, size[2]/2
        z0, z1 = (0.0, size[2]) if base else (-sz, sz)
        v = [(-sx,-sy,z0),(sx,-sy,z0),(sx,sy,z0),(-sx,sy,z0),
             (-sx,-sy,z1),(sx,-sy,z1),(sx,sy,z1),(-sx,sy,z1)]
        f = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        me.from_pydata(v, [], f); me.update()
        o = bpy.data.objects.new(name, me); C.objects.link(o)
    o.location, o.rotation_mode, o.rotation_euler = loc, 'XYZ', rot
    o.data.materials.clear(); o.data.materials.append(_matfor(color, emit, rough, metal))
    return o

def row(name, size, start, count, step, axis="y", color="grey", emit=0.0,
        rough=0.7, metal=0.0, base=False, collection="SET"):
    """A slab repeated N times along an axis, via an Array modifier -- so a
    500 m colonnade is still ONE object. This is the parallax workhorse:
    ribs, piers, columns, lamp posts, parked cars, fence posts, trees, windows."""
    o = slab(name, size, start, color, emit=emit, rough=rough, metal=metal,
             base=base, collection=collection)
    m = o.modifiers.get("ARR") or o.modifiers.new("ARR", 'ARRAY')
    m.use_relative_offset, m.use_constant_offset = False, True
    off = [0.0, 0.0, 0.0]; off["xyz".index(axis)] = step
    m.constant_offset_displace = off
    m.count = count
    return o

def cyl(name, radius, height, loc, color="grey", axis="z", verts=12,
        emit=0.0, rough=0.7, metal=0.0, collection="SET"):
    """Round stock: pipes, poles, trunks, barrels, pillars."""
    rot = {"z": (0, 0, 0), "y": (math.pi/2, 0, 0), "x": (0, math.pi/2, 0)}[axis]
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=height,
                                        location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    coll(collection).objects.link(o)
    o.data.materials.clear(); o.data.materials.append(_matfor(color, emit, rough, metal))
    return o

def ground(size=240.0, color="dark", z=0.0, drop=0.02):
    """`drop` sinks the ground's TOP face below the nominal floor. Without it the
    ground's top sits at exactly z=0 -- the same plane as every flat set piece
    built on the floor -- and the two z-fight. That flickers in the RENDER, not
    just the viewport: same depth buffer."""
    return slab("SET_ground", (size, size, 0.2), (0, 0, z - drop - 0.1), color, rough=0.8)

def checker(size=200.0, square=2.0, z=0.0, a="light", b="dark",
            posts=0, post_x=9.0, post_step=8.0, post_y0=-40.0):
    """THE DEFAULT SET. A checkerboard ground plane -- THREE objects, no
    composition, no occlusion checking, no thinking.

    Use this whenever the brief did not NAME a place. The squares streaming past
    are real parallax in every axis, which is why animators have blocked on a
    checkerboard forever: it reads scale, speed, height, heading and ground
    contact without committing the shot to a location nobody asked for.

    Inventing a set when none was requested costs minutes of composition and
    hands Seedance a place the brief never wanted.

    Built as GEOMETRY, not a procedural texture: the viewport delivers in SOLID
    shading, which ignores shader nodes entirely. Base plane in `b`, two arrayed
    tile sets in `a` covering the (even,even) and (odd,odd) squares.

    posts=N adds two flanking rows of thin verticals when a move needs an
    off-ground reference (a crane down, an orbit, a rise). Still one line.
    Nothing gates posts against the camera route -- keep |cam x| < post_x - 1."""
    half, step = size / 2.0, square * 2.0
    n = max(int(size / step), 1)
    base = slab("SET_checker", (size, size, 0.2), (0, 0, z - 0.1), b, rough=0.75)
    for tag, k in (("a", 0.5), ("b", 1.5)):
        o = slab(f"SET_checker_{tag}", (square, square, 0.04),
                 (-half + k * square, -half + k * square, z + 0.02), a, rough=0.75)
        for ax, mn in (("x", "ARR_X"), ("y", "ARR_Y")):
            m = o.modifiers.get(mn) or o.modifiers.new(mn, 'ARRAY')
            m.use_relative_offset, m.use_constant_offset = False, True
            off = [0.0, 0.0, 0.0]; off["xyz".index(ax)] = step
            m.constant_offset_displace, m.count = off, n
    if posts:
        for sgn, tag in ((-1, "L"), (1, "R")):
            row(f"SET_post_{tag}", (0.25, 0.25, 3.0), (sgn * post_x, post_y0, 1.5),
                posts, post_step, color="grey")
    return base

def marker(name, kind="swap", size=(2, 2, 2), loc=(0, 0, 1), color="magenta"):
    """Explicit 'replace me' stand-ins that become asset-list lines.
    kind 'gap'  -> black volume the video model fills (steam, smoke, crowd, water)
    kind 'swap' -> coloured slab the prompt names and maps to a reference image"""
    return slab(f"MK_{name}", size, loc, "black" if kind == "gap" else color,
                rough=0.85, collection="MARKERS")

# ==================================================================== light ==
def light(name, kind='AREA', loc=(0, 0, 5), rot=(0, 0, 0), energy=200.0,
          color=(1.0, 0.95, 0.88), size=1.0, size_y=None):
    d = bpy.data.lights.get("LD_" + name) or bpy.data.lights.new("LD_" + name, kind)
    d.type, d.energy, d.color = kind, energy, color
    if kind == 'AREA':
        d.shape = 'RECTANGLE' if size_y else 'SQUARE'
        d.size = size
        if size_y: d.size_y = size_y
    if kind == 'SUN': d.angle = 0.05
    o = bpy.data.objects.get(name) or bpy.data.objects.new(name, d)
    if name not in coll("LIGHTING").objects: coll("LIGHTING").objects.link(o)
    o.data, o.location, o.rotation_mode, o.rotation_euler = d, loc, 'XYZ', rot
    return o

def light_row(name, count, start, step, axis="y", **kw):
    """Lights cannot use Array modifiers -- they need real objects. One shared
    light datablock across all of them, so tuning one tunes every copy."""
    out = []
    for i in range(count):
        loc = list(start); loc["xyz".index(axis)] += i * step
        o = light(f"{name}_{i:02d}", loc=tuple(loc), **kw)
        if i: o.data = bpy.data.objects[f"{name}_00"].data
        out.append(o)
    return out

def sun(rot=(1.05, 0.0, 0.6), energy=3.0, color=(1.0, 0.94, 0.84), sky=(0.16, 0.20, 0.29)):
    o = light("LGT_sun", 'SUN', (0, 0, 20), rot, energy, color)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (*sky, 1)
    return o

# ==================================================================== actor ==
def actor(name="HERO", size=(0.50, 0.35, 1.80), color="red", oriented=False,
          start=(0, 0, 0), wheels=None, body_z=0.0):
    """The hero: ONE coloured box on a root empty. Never a character.
    oriented=True paints facing in: +Y red, -Y black, sides and top green.

    wheels=(track, wheelbase, radius) bolts four cylinders to the root for a
    vehicle -- still boxes-and-cylinders, but a drift is unreadable without them
    and there is no other way to aim a camera at a front wheel. body_z lifts the
    body so the wheels sit under it."""
    C = coll("HERO")
    root = bpy.data.objects.get(f"RIG_{name}_root")
    if root is None:
        root = bpy.data.objects.new(f"RIG_{name}_root", None); C.objects.link(root)
    root.empty_display_type, root.empty_display_size = 'PLAIN_AXES', 0.45
    root.rotation_mode, root.location = 'XYZ', start
    blk = slab(f"{name}_block", size, (0, 0, body_z), color, base=True, rough=0.52,
               collection="HERO")
    blk.parent, blk.matrix_parent_inverse = root, Matrix.Identity(4)
    if oriented:
        blk.data.materials.clear()
        for c in ("green", "red", "black"):
            blk.data.materials.append(mat(f"MAT_face_{c}", c, 0.52))
        for p, i in zip(blk.data.polygons, [0, 0, 2, 0, 1, 0]):   # bot top -Y +X +Y -X
            p.material_index = i
    if wheels:
        track, wheelbase, r = wheels
        for sx, tx in ((-1, "L"), (1, "R")):
            for sy, ty in ((-1, "R"), (1, "F")):      # F = front (+Y)
                w = cyl(f"{name}_wheel_{ty}{tx}", r, r * 0.72,
                        (sx * track / 2.0, sy * wheelbase / 2.0, r),
                        color="black", axis="x", verts=16, collection="HERO")
                w.parent, w.matrix_parent_inverse = root, Matrix.Identity(4)
    return root, blk

# ============================================== slotted-action-safe baking ===
def _cbag(idd, name, id_type, slot_name):
    """Blender 5.2: animation_data_clear() only UNLINKS -- the next keyframe
    re-links the same action with every stale fcurve intact. Destroy it."""
    ad = idd.animation_data
    if ad and ad.action:
        old = ad.action; idd.animation_data_clear()
        bpy.data.actions.remove(old, do_unlink=True)
    act = bpy.data.actions.new(name)
    slot = act.slots.new(id_type=id_type, name=slot_name)
    strip = act.layers.new("Layer").strips.new(type='KEYFRAME')
    idd.animation_data_create()
    idd.animation_data.action = act
    idd.animation_data.action_slot = slot
    return strip.channelbag(slot, ensure=True)

def bake(idd, channels, id_type='OBJECT', name=None, start=1):
    cb = _cbag(idd, name or f"ACT_{idd.name}", id_type, idd.name)
    for (path, idx), vals in channels.items():
        n = len(vals)
        fcu = cb.fcurves.new(path, index=idx)
        fcu.keyframe_points.add(n)
        flat = []
        for i, v in enumerate(vals): flat += [start + i, v]
        fcu.keyframe_points.foreach_set("co", flat)
        fcu.keyframe_points.foreach_set("interpolation", [1] * n)
        fcu.update()
    return len(channels)

# ================================================== consume the solved bake ==
def load_bake(path, hero="HERO", clip=(0.15, 320.0)):
    """Reads solve_shot.py output. One camera PER SHOT, bound to timeline
    markers, so cuts happen live in the viewport with nothing rendered."""
    D = json.load(open(path))
    sc = bpy.context.scene
    sc.render.fps, sc.frame_start, sc.frame_end = D["fps"], 1, D["frames"]
    # carry the solver's OWN limits across, so audit() can never gate on the
    # wrong numbers for this rig
    bpy.app.driver_namespace["PV_RIG"] = D.get("rig")
    bpy.app.driver_namespace["PV_LIMITS"] = D.get("limits") or {}
    bpy.app.driver_namespace["PV_CROP"] = [sh.get("crop_from_f") for sh in D["shots"]]

    root = bpy.data.objects.get(f"RIG_{hero}_root") or actor(hero)[0]
    S = D["subject"]
    ch = {("location", 0): [p[0] for p in S], ("location", 1): [p[1] for p in S],
          ("location", 2): [p[2] for p in S], ("rotation_euler", 2): D["yaw"]}
    if D.get("pitch") and any(abs(v) > 1e-9 for v in D["pitch"]):
        # 'ZYX' applies Z FIRST then X -> R = Rx(tilt).Rz(spin): the object spins
        # about its OWN axis and the whole spinning thing is then tilted. The
        # default 'XYZ' would tilt first and then yaw about WORLD Z, which makes
        # a tilted object precess like a gyroscope instead of spinning in place.
        root.rotation_mode = 'ZYX'
        ch[("rotation_euler", 0)] = D["pitch"]
    bake(root, ch, name=f"ACT_{hero}_root")

    C = coll("CAM_rig")
    sc.timeline_markers.clear()
    cams = []
    for i, sh in enumerate(D["shots"]):
        tag = f"{i+1:02d}"
        aim = bpy.data.objects.get(f"AIM_{tag}")
        if aim is None:
            aim = bpy.data.objects.new(f"AIM_{tag}", None); C.objects.link(aim)
        aim.empty_display_type, aim.empty_display_size = 'SPHERE', 0.22
        cam = bpy.data.objects.get(f"CAM_{tag}")
        if cam is None:
            cam = bpy.data.objects.new(f"CAM_{tag}", bpy.data.cameras.new(f"CAM_{tag}"))
            C.objects.link(cam)
        cd = cam.data
        cd.sensor_fit, cd.sensor_width = 'HORIZONTAL', 36.0
        cd.clip_start, cd.clip_end = clip
        cam.rotation_mode = 'XYZ'
        cam.constraints.clear()
        tt = cam.constraints.new('TRACK_TO'); tt.name = "AIM"; tt.target = aim
        tt.track_axis, tt.up_axis = 'TRACK_NEGATIVE_Z', 'UP_Y'
        f0 = sh["f0"]
        bake(cam, {("location", k): [p[k] for p in sh["cam"]] for k in range(3)},
             name=f"ACT_cam_{tag}", start=f0)
        bake(aim, {("location", k): [p[k] for p in sh["aim"]] for k in range(3)},
             name=f"ACT_aim_{tag}", start=f0)
        bake(cd, {("lens", 0): sh["lens"]}, id_type='CAMERA',
             name=f"ACT_lens_{tag}", start=f0)
        cams.append(cam)
        if len(D["shots"]) > 1:
            mk = sc.timeline_markers.new(f"SHOT_{tag}", frame=f0)
            mk.camera = cam                       # <- the cut, live in the viewport
    sc.camera = cams[0]
    sc.frame_set(1)
    return {"frames": D["frames"], "shots": len(cams), "cameras": [c.name for c in cams],
            "rig": D.get("rig"), "limits": D.get("limits")}

# ======================================================== viewport delivery ==
def viewport_ready(shading='SOLID', overlays=False, clip=(0.15, 320.0)):
    """Put the user's viewport in camera view, clean, on frame 1, ready for Space.
    This is the delivery step -- NOT a render. Nothing is written to disk."""
    sc = bpy.context.scene
    sc.sync_mode = 'FRAME_DROP'              # hold real time instead of playing slow
    sc.frame_set(sc.frame_start)
    n = 0
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            s = area.spaces.active
            s.region_3d.view_perspective = 'CAMERA'
            s.shading.type = shading
            s.overlay.show_overlays = overlays
            s.show_gizmo = False
            s.clip_start, s.clip_end = clip
            n += 1
            area.tag_redraw()
    return {"viewports_set": n, "frames": [sc.frame_start, sc.frame_end],
            "shots": len(sc.timeline_markers) or 1,
            "hint": "camera view, solid shading, frame 1 -- press Space to play"}

# =================================================================== audit ===
def audit(hero="HERO", step=3, max_deg_per_s=None, min_subject_distance=None):
    """Re-measure from EVALUATED matrices. The solver proved the plan; this
    proves what actually got built. Walks every shot's own camera.

    Gates against the RIG's limits, picked up from the bake by load_bake -- so a
    motion-control whip or an FPV dive is judged by its own physics, not the
    gimbal defaults. Pass an argument only to override."""
    L = bpy.app.driver_namespace.get("PV_LIMITS") or {}
    if max_deg_per_s is None:        max_deg_per_s = L.get("max_deg_per_s", 30.0)
    if min_subject_distance is None: min_subject_distance = L.get("min_subject_distance", 2.6)
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    blk = bpy.data.objects.get(f"{hero}_block")
    mks = sorted(sc.timeline_markers, key=lambda m: m.frame)
    spans = []
    if mks and any(m.camera for m in mks):
        for i, m in enumerate(mks):
            end = mks[i+1].frame - 1 if i + 1 < len(mks) else sc.frame_end
            spans.append((m.camera, m.frame, end))
    else:
        spans = [(sc.camera, sc.frame_start, sc.frame_end)]
    crops = bpy.app.driver_namespace.get("PV_CROP") or []
    out = []
    for si, (cam, f0, f1) in enumerate(spans):
        crop_f = crops[si] if si < len(crops) else None
        prev_f = prev_p = None
        rates, speeds, oof, marg, dists, cropped = [], [], 0, [], [], 0
        for f in range(f0, f1 + 1, step):
            sc.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            ce, be = cam.evaluated_get(dg), blk.evaluated_get(dg)
            M = ce.matrix_world; p = M.translation.copy()
            fwd = (M.to_3x3() @ Vector((0, 0, -1))).normalized()
            if prev_f is not None:
                dt = step / sc.render.fps
                rates.append(math.degrees(math.acos(max(-1, min(1, fwd.dot(prev_f))))) / dt)
                speeds.append((p - prev_p).length / dt)
            prev_f, prev_p = fwd, p
            nd = [world_to_camera_view(sc, ce, be.matrix_world @ Vector(c))
                  for c in be.bound_box]
            inframe = (min(n.z for n in nd) > 0 and min(n.x for n in nd) > 0
                       and max(n.x for n in nd) < 1 and min(n.y for n in nd) > 0
                       and max(n.y for n in nd) < 1)
            in_crop = crop_f is not None and f >= crop_f
            if not inframe:
                if in_crop: cropped += 1        # DELIBERATE, not a failure
                else:       oof += 1
            if not in_crop:
                marg.append(min(min(n.x for n in nd), 1 - max(n.x for n in nd),
                                min(n.y for n in nd), 1 - max(n.y for n in nd)))
            dists.append((be.matrix_world.translation - p).length)
        out.append({"camera": cam.name, "frames": [f0, f1], "out_of_frame": oof,
                    "cropped_frames": cropped,
                    "crop_from_frame": crop_f,
                    "tightest_margin": round(min(marg), 3) if marg else None,
                    "rot_max": round(max(rates), 1) if rates else 0.0,
                    "speed": [round(min(speeds), 2), round(max(speeds), 2)] if speeds else [0, 0],
                    "min_dist": round(min(dists), 2)})
    sc.frame_set(sc.frame_start)
    return {"shots": out,
            "rig": bpy.app.driver_namespace.get("PV_RIG"),
            "limits": {"max_deg_per_s": max_deg_per_s,
                       "min_subject_distance": min_subject_distance},
            "PASS": all(s["out_of_frame"] == 0
                        and s["rot_max"] <= max_deg_per_s
                        and s["min_dist"] >= min_subject_distance for s in out)}

# ================================================================== output ===
def backup(label, folder=None):
    if folder is None:
        home = os.path.expanduser("~")
        root = os.path.join(home, "Movies") if os.path.isdir(os.path.join(home, "Movies")) else home
        folder = os.path.join(root, "previz_blocking", "backups")
    os.makedirs(folder, exist_ok=True)
    p = os.path.join(folder, f"{label}.blend")
    bpy.ops.wm.save_as_mainfile(filepath=p, copy=True)   # copy: active path untouched
    return p

def motion_render(path, res=(1920, 1080)):
    """The Seedance camera authority: greybox, every frame, MP4.
    HEAVY -- only after the user has watched the viewport and approved."""
    sc = bpy.context.scene
    ims = sc.render.image_settings
    has_mt = hasattr(ims, "media_type")          # Blender 5.x split video out
    keep = (sc.render.filepath, sc.render.resolution_x, sc.render.resolution_y,
            ims.file_format, ims.media_type if has_mt else None)
    sc.render.resolution_x, sc.render.resolution_y = res
    # 5.x: file_format only lists STILL formats until media_type is VIDEO, so
    # setting FFMPEG first raises "enum FFMPEG not found".
    if has_mt: ims.media_type = 'VIDEO'
    ims.file_format = 'FFMPEG'
    sc.render.ffmpeg.format, sc.render.ffmpeg.codec = 'MPEG4', 'H264'
    sc.render.ffmpeg.constant_rate_factor = 'HIGH'
    sc.render.filepath = path
    bpy.ops.render.opengl(animation=True, view_context=False)
    sc.render.filepath, sc.render.resolution_x, sc.render.resolution_y = keep[:3]
    if has_mt: ims.media_type = keep[4]
    ims.file_format = keep[3]
    return path
