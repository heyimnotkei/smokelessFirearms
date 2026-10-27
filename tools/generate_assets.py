#!/usr/bin/env python3
"""Regenerates everything under resources/assets/smokelessfirearms.

Needs the Firearmsfork repo checked out (it derives the arm/hand animation poses,
projectile entity and item behaviours from it so they stay structurally valid):

    python3 tools/generate_assets.py /path/to/Firearmsfork

Tweak the constants below and re-run to retune the look/feel.
"""
import copy, json, os, sys, random
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DOM = "smokelessfirearms"
A = os.path.join(ROOT, "resources", "assets", DOM)
FORK = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "..", "Firearmsfork")
FA = os.path.join(FORK, "resources", "assets", "maltiezfirearms")

# ---- tunables -------------------------------------------------------------
LEVER_DEG = 62      # lever swing. If it swings the wrong way in game, negate this.
GATE_DEG = 55       # loading gate swing (same note)
LOAD_MS = 1300      # one round through the side gate
CYCLE_MS = 1000     # working the lever (chambers a round)
SHOT_TAIL_MS = 700  # extra time after the shot for the lever cycle
MAG_SIZE = 7        # 6 in the tube + 1 chambered, like the real carbine
RIFLE_SHADED = False  # False = flat, unshaded placeholder look

# Flat placeholder colours. ONE 16x16 texture (4x4 cells of 4px) shared by every model.
PALETTE = [("steel", (74, 78, 86)), ("wood", (118, 76, 44)), ("brass", (198, 154, 58)),
           ("lead", (128, 132, 138)), ("copper", (188, 108, 70)), ("dark", (40, 42, 48))]
PAL_NAMES = [n for n, _ in PALETTE]


def w(path, obj):
    p = os.path.join(A, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        if isinstance(obj, str):
            f.write(obj)
        else:
            json.dump(obj, f, indent=2, ensure_ascii=False)


def load_json(p):
    with open(p, encoding="utf-8-sig") as f:
        return json.load(f)


# ---- shape helpers --------------------------------------------------------
FACES = ["north", "east", "south", "west", "up", "down"]


def cell_uv(color):
    i = PAL_NAMES.index(color)
    cx, cy = i % 4, i // 4
    return [cx * 4 + 1, cy * 4 + 1, cx * 4 + 3, cy * 4 + 3]   # well inside the solid cell


def box(name, a, b, color, shade=True, **extra):
    uv = cell_uv(color)
    e = {"name": name, "from": list(a), "to": list(b),
         "faces": {f: {"texture": "#pal", "uv": list(uv), "autoUv": False} for f in FACES}}
    if not shade:
        e["shade"] = False
    e.update(extra)
    return e


def pivot(name, p, children):
    uv = cell_uv("steel")
    return {"name": name, "from": list(p), "to": list(p), "rotationOrigin": list(p), "shade": False,
            "faces": {f: {"texture": "#pal", "uv": list(uv)} for f in FACES}, "children": children}


def rel(child, origin):
    """Children are positioned relative to the parent's 'from'."""
    c = copy.deepcopy(child)
    c["from"] = [round(c["from"][i] - origin[i], 3) for i in range(3)]
    c["to"] = [round(c["to"][i] - origin[i], 3) for i in range(3)]
    return c


def shape_wrapper(elements, animations=None):
    return {"editor": {"allAngles": False, "entityTextureMode": False},
            "textureWidth": 16, "textureHeight": 16, "textureSizes": {},
            "textures": {"pal": DOM + ":palette"},
            "elements": elements, "animations": animations or []}


def joint_animation(names):
    """An engine only creates animation joints for elements named in the shape's own animations.
    Without this block the item-frame animations (lever / gate) have nothing to drive."""
    zero = lambda: {n: {"rotationX": 0.0, "rotationY": 0.0, "rotationZ": 0.0} for n in names}
    return [{"name": "Joints", "code": "joints", "quantityframes": 2, "onActivityStopped": "Rewind",
             "onAnimationEnd": "Hold",
             "keyframes": [{"frame": 0, "elements": zero()}, {"frame": 1, "elements": zero()}]}]


# ---- rifle: 1 unit ~ 1 inch, muzzle toward -Z, butt toward +Z (same as the fork's carbine)
def rifle_shape():
    S = RIFLE_SHADED
    b = lambda n, a, c, col, **kw: box(n, a, c, col, shade=S, **kw)
    els = []
    els.append(b("Barrel", (-0.42, 0.35, -26.5), (0.42, 1.2, -6.5), "steel"))
    els.append(b("Muzzle", (-0.5, 0.3, -26.5), (0.5, 1.25, -25.6), "steel"))
    els.append(b("Mag_tube", (-0.36, -0.55, -25.0), (0.36, 0.22, -6.5), "steel"))
    els.append(b("Tube_cap", (-0.42, -0.6, -25.6), (0.42, 0.27, -24.9), "steel"))
    els.append(b("Forend", (-0.62, -0.8, -21.0), (0.62, 0.3, -6.5), "wood"))
    els.append(b("Band", (-0.6, -0.72, -15.4), (0.6, 1.3, -14.8), "steel"))
    els.append(b("Front_sight", (-0.1, 1.2, -25.8), (0.1, 1.68, -25.4), "dark"))
    els.append(b("Rear_sight_base", (-0.35, 1.2, -10.2), (0.35, 1.35, -9.0), "dark"))
    els.append(b("Rear_sight_leaf_l", (-0.55, 1.3, -9.9), (-0.3, 1.6, -9.5), "dark"))
    els.append(b("Rear_sight_leaf_r", (0.3, 1.3, -9.9), (0.55, 1.6, -9.5), "dark"))
    els.append(b("Receiver", (-0.66, -1.5, -6.5), (0.66, 1.3, 1.6), "steel"))
    els.append(b("Receiver_top", (-0.5, 1.3, -5.5), (0.5, 1.45, 1.2), "steel"))
    els.append(b("Ejection_port", (-0.68, 0.35, -4.0), (-0.66, 1.0, -0.4), "dark"))
    els.append(b("Tang", (-0.4, 0.35, 1.6), (0.4, 1.4, 3.4), "steel"))
    els.append(b("Wrist", (-0.6, -1.3, 1.6), (0.6, 1.1, 5.0), "wood"))
    els.append(b("Comb", (-0.6, -1.5, 5.0), (0.6, 1.3, 8.0), "wood"))
    els.append(b("Butt", (-0.6, -2.6, 8.0), (0.6, 1.0, 11.6), "wood"))
    els.append(b("Butt_heel", (-0.6, -3.6, 9.4), (0.6, 0.2, 11.6), "wood"))
    els.append(b("Buttplate", (-0.65, -3.7, 11.6), (0.65, 0.3, 12.0), "dark"))
    els.append(b("Receiver_screw", (0.66, 0.2, -1.0), (0.7, 0.5, -0.7), "brass"))
    lp = (0.0, -1.5, 1.0)  # lever pivot
    lever_children = [
        b("Trigger", (-0.12, -2.7, -0.4), (0.12, -1.5, -0.1), "dark"),
        b("Lever_front", (-0.3, -5.0, -3.4), (0.3, -1.5, -2.7), "dark"),
        b("Lever_bottom", (-0.3, -5.0, -3.4), (0.3, -4.3, 4.1), "dark"),
        b("Lever_rear", (-0.3, -4.8, 3.4), (0.3, -1.2, 4.1), "dark"),
    ]
    els.append(pivot("Lever", lp, [rel(c, lp) for c in lever_children]))
    els.append(b("Hammer", (-0.16, 1.0, 1.2), (0.16, 2.05, 1.9), "dark",
                 rotationX=-25.0, rotationOrigin=[0.0, 1.1, 1.5]))
    gp = (0.66, -0.8, -2.4)  # side loading gate, hinged on its front edge
    els.append(pivot("Gate", gp, [rel(b("Gate_plate", (0.66, -1.2, -2.4), (0.8, -0.1, 0.4), "brass"), gp)]))
    # attachment anchor: the cartridge shown at the gate while loading
    els.append({"name": "Bullet", "from": [0.9, -0.6, -1.4], "to": [0.9, -0.6, -1.4],
                "rotationOrigin": [0.9, -0.6, -1.4], "shade": False,
                "faces": {f: {"texture": "#pal", "uv": cell_uv("lead")} for f in FACES},
                "attachmentpoints": [{"code": "bullet", "posX": "0.25", "posY": "0.25", "posZ": "0.25",
                                      "rotationX": "0.0", "rotationY": "0.0", "rotationZ": "0.0"}]})
    return shape_wrapper(els, joint_animation(["Lever", "Gate"]))


# ---- small items: centred at (8, y, 8) like the fork's bullet, lying along Z (nose toward -Z).
# Being centred in the 16x16 block cube is what makes the inventory icon land in its slot.
CART_PARTS = lambda tip: [("Rim", 0, 0.25, 0.62, "brass"), ("Case", 0.25, 2.3, 0.52, "brass"),
                          ("Shoulder", 2.3, 2.6, 0.42, "brass"), ("Bullet_base", 2.6, 3.5, 0.36, tip),
                          ("Bullet_nose", 3.5, 3.9, 0.26, tip), ("Bullet_tip", 3.9, 4.1, 0.14, tip)]


def lying(parts, yc):
    length = max(p[2] for p in parts)
    rear = 8 + length / 2
    return [box(n, (8 - r, yc - r, round(rear - a1, 3)), (8 + r, yc + r, round(rear - a0, 3)), c)
            for n, a0, a1, r, c in parts]


CART_YC = 0.62
CASING_PARTS = CART_PARTS("lead")[:3]
PRIMER_PARTS = [("Cup", 0, 0.5, 0.5, "brass"), ("Pellet", 0.5, 0.62, 0.25, "dark")]
PRIMER_YC = 0.5


def small_transforms(gui_scale, yc, ground_scale):
    oy = round(yc / 16, 3)
    return {
        "guiTransform": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": -25, "y": 40, "z": 0},
                         "origin": {"x": 0.5, "y": oy, "z": 0.5}, "scale": gui_scale},
        "fpHandTransform": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0},
                            "origin": {"x": 0.5, "y": oy, "z": 0.5}, "scale": 1.0},
        "tpHandTransform": {"translation": {"x": -0.9, "y": -0.6, "z": -0.7}, "rotation": {"x": 0, "y": 0, "z": 0},
                            "origin": {"x": 0.5, "y": oy, "z": 0.5}, "scale": 0.8},
        "groundTransform": {"translation": {"x": 0, "y": 0, "z": 0}, "rotation": {"x": 0, "y": 0, "z": 0},
                            "origin": {"x": 0.5, "y": oy, "z": 0.5}, "scale": ground_scale},
    }


# ---- animations: derive hand poses from the fork's carbine ---------------
def retime(anim, total_ms):
    kf = anim["PlayerKeyFrames"]
    old = kf[-1]["EasingTime"]
    for k in kf:
        k["EasingTime"] = int(k["EasingTime"] * total_ms / old)
    return anim


def item_frames(pairs):
    return [{"DurationFraction": f, "EasingFunction": "Linear", "Elements": e} for f, e in pairs]


def neutral(anim):
    anim["ItemKeyFrames"] = []
    anim["ItemAnimationStart"] = -1
    anim["ItemAnimationEnd"] = -1
    anim["ParticlesFrames"] = []
    return anim


def build_anims():
    car = load_json(os.path.join(FA, "config", "animations", "carbine.json"))
    out = {}
    L0 = {"Lever": [0, 0, 0, 0, 0, 0]}
    L1 = {"Lever": [0, 0, 0, LEVER_DEG, 0, 0]}
    for sfx in ("", "-tp"):
        a = retime(copy.deepcopy(car["firearms-carbine-prime" + sfx]), LOAD_MS)
        a["ItemAnimationStart"] = 0
        a["ItemAnimationEnd"] = LOAD_MS
        a["ParticlesFrames"] = []
        g0 = {"Gate": [0, 0, 0, 0, 0, 0]}
        g1 = {"Gate": [0, 0, 0, 0, GATE_DEG, 0]}
        a["ItemKeyFrames"] = item_frames([(0.0, g0), (0.15, g1), (0.7, g1), (0.9, g0), (1.0, g0)])
        out["leveraction-load" + sfx] = a

        a = retime(copy.deepcopy(car["firearms-carbine-prime" + sfx]), CYCLE_MS)
        a["ItemAnimationStart"] = 0
        a["ItemAnimationEnd"] = CYCLE_MS
        a["CallbackFrames"] = []
        a["ParticlesFrames"] = []
        a["ItemKeyFrames"] = item_frames([(0.0, L0), (0.15, L0), (0.5, L1), (0.6, L1), (0.9, L0), (1.0, L0)])
        out["leveraction-prime" + sfx] = a

        a = copy.deepcopy(car["firearms-carbine-shoot" + sfx])
        kf = a["PlayerKeyFrames"]
        t0 = kf[-1]["EasingTime"]
        total = t0 + SHOT_TAIL_MS
        for t in (t0 + 150, total):
            k = copy.deepcopy(kf[-1])
            k["EasingTime"] = t
            kf.append(k)
        for c in a.get("CallbackFrames", []):
            c["DurationFraction"] = c["DurationFraction"] * t0 / total
        for s in a.get("SoundFrames", []):
            s["DurationFraction"] = s["DurationFraction"] * t0 / total
        a["SoundFrames"] = [s for s in a.get("SoundFrames", []) if "flintlock" not in s["Code"][0]]
        a["ParticlesFrames"] = []
        a["ItemAnimationStart"] = 0
        a["ItemAnimationEnd"] = total
        f = lambda ms: round(ms / total, 4)
        a["ItemKeyFrames"] = item_frames([(0.0, L0), (f(t0 + 20), L0), (f(t0 + 260), L1),
                                          (f(t0 + 380), L1), (f(total - 60), L0), (1.0, L0)])
        out["leveraction-shoot" + sfx] = a

        for name in ("primed", "loaded", "aim"):
            out["leveraction-" + name + sfx] = neutral(copy.deepcopy(car["firearms-carbine-" + name + sfx]))
    return out


# ---- items ---------------------------------------------------------------
def build_rifle_item():
    it = load_json(os.path.join(FA, "itemtypes", "firearms", "carbine.json"))
    it["class"] = "SmokelessFirearms:Repeater"
    it["code"] = "leveraction"
    it["variantgroups"] = [{"code": "type", "states": ["carbine"]}]
    it["durability"] = 1200
    it["shape"] = {"base": DOM + ":firearms/leveraction"}
    for b in it["behaviors"]:
        if b["name"] == "CombatOverhaul:AnimatableAttachable":
            b["properties"]["animated-shape"] = DOM + ":firearms/leveraction"
    at = it["attributes"]
    at["handbook"] = {"groupBy": ["leveraction-*"]}
    P = DOM + ":leveraction-"
    at.update({
        "BulletDamageMultiplier": 1.25, "BulletDamageStrength": 9, "BulletVelocity": 14,
        "DispersionMOA": [45, 45],
        "MagazineSize": MAG_SIZE, "BulletLoadedPerReload": 1, "BulletsLoadedPerBulletItem": 1,
        "WaddingUsedPerReload": 0, "LoadPowderConsumption": 0, "PrimePowderConsumption": 0,
        "BulletWildcard": "*" + DOM + ":cartridge-*",
        "FlaskWildcard": DOM + ":no-flask-needed",
        "LoadingRequirementWildcard": "", "PrimingRequirementWildcard": "", "CockingRequirementWildcard": "",
        "IdleAnimation": "maltiezfirearms:firearms-shoulder",
        "ReadyAnimation": "maltiezfirearms:firearms-ready",
        "LoadAnimation": [P + "load"], "PrimeAnimation": P + "prime",
        "AimAnimation": P + "aim", "ShootAnimation": [P + "shoot"],
        "LoadedAnimation": [P + "loaded"], "PrimedAnimation": P + "primed",
        "LoadSpeedPenalty": -0.5, "ReloadAnimationSpeed": 1,
        # The cartridge model is centred at (8, 0.62, 8) and lies along Z, so it already points forward.
        # translation ~= -8*scale + 0.5 cancels the centring offset (same convention as the fork's BulletTransform).
        "BulletTransform": {"translation": {"x": -3.5, "y": 0.2, "z": -3.5},
                            "rotation": {"x": 0, "y": 0, "z": 0}, "scale": 0.5},
    })
    at.pop("CockedAnimation", None)
    at["Aiming"].update({"AimDrift": 10, "AimTwitch": 5})
    at["Recoil"].update({"VerticalBaseDeg": 3.0, "MaxQueuedVerticalDeg": 20})
    it.pop("texturesByType", None)
    return it


def build_cartridge_item():
    it = load_json(os.path.join(FA, "itemtypes", "ammunition", "bullet.json"))
    it["code"] = "cartridge"
    it["variantgroups"] = [{"code": "bullet", "states": ["lead", "copper"]}]
    it.pop("shape", None)
    it["shapeByType"] = {"*-lead": {"base": DOM + ":item/cartridge-lead"},
                         "*-copper": {"base": DOM + ":item/cartridge-copper"}}
    it.pop("textures", None)
    it["maxstacksize"] = 64
    it["behaviors"] = [b for b in it["behaviors"] if b["name"] != "GroundStorable"]
    for b in it["behaviors"]:
        if b["name"] == "CombatOverhaul:Projectile":
            s = b["properties"]["stats"]
            s["PenetrationDistance"] = 2
            s["CollisionRadius"] = 0.02
            s["EntityCode"] = DOM + ":cartridge-{bullet}"
            s["DamageStatsByType"] = {"*-lead": {"DamageType": "PiercingAttack", "Damage": 20},
                                      "*-copper": {"DamageType": "PiercingAttack", "Damage": 17}}
    it["creativeinventory"] = {"general": ["*"], DOM: ["*"]}
    it.update(small_transforms(3.6, CART_YC, 2.5))
    return it


def simple_item(code, shape, gui_scale, yc):
    it = {"code": code, "class": "Item", "maxstacksize": 64, "shape": {"base": DOM + ":item/" + shape},
          "creativeinventory": {"general": ["*"], DOM: ["*"]}}
    it.update(small_transforms(gui_scale, yc, 3.0))
    return it


def build_powder_item(code):
    it = load_json(os.path.join(FA, "itemtypes", "ammunition", "gunpowder.json"))
    it["code"] = code
    for k in ("variantgroups", "shapeByType", "textureByType", "behaviorsByType",
              "transitionablePropsByType", "grindingPropsByType"):
        it.pop(k, None)
    it["shape"] = {"base": "maltiezfirearms:powder/gunpowder"}
    it["textures"] = {"gunpowder": {"base": DOM + ":" + code}}
    it["creativeinventory"] = {"general": ["*"], DOM: ["*"]}
    it["attributes"]["dissolveInWater"] = False
    return it


def build_entity():
    e = load_json(os.path.join(FA, "entities", "bullet.json"))
    e["code"] = "cartridge"
    e["variantgroups"] = [{"code": "bullet", "states": ["lead", "copper"]}]
    e["client"]["textures"] = {"metal": {"base": "game:block/metal/plate/{bullet}"}}
    for side in ("client", "server"):
        for b in e[side]["behaviors"]:
            if b.get("code") == "CombatOverhaul:ProjectilePhysics":
                b["SmokeTrail"] = False   # smokeless powder: no trail
    return e


# ---- recipes -------------------------------------------------------------
def build_recipes():
    R = {}
    # Vanilla barrels hold at most ONE item ingredient + ONE liquid, and outputs use "stackSize".
    # So guncotton is a grid recipe, and the barrel step is guncotton + spirits only.
    R["grid/guncotton.json"] = [{
        "ingredientPattern": "FSU", "width": 3, "height": 1,
        "ingredients": {"F": {"type": "item", "code": "game:flaxfibers", "quantity": 4},
                        "S": {"type": "item", "code": "game:saltpeter", "quantity": 1},
                        "U": {"type": "item", "code": "game:powder-sulfur", "quantity": 1}},
        "output": {"type": "item", "code": DOM + ":guncotton", "quantity": 4}}]
    R["barrel/smokelesspowder.json"] = [{
        "code": "smokelesspowder", "sealHours": 12,
        "ingredients": [
            {"type": "item", "code": DOM + ":guncotton", "quantity": 8},
            {"type": "item", "code": "game:spiritportion", "litres": 1}],
        "output": {"type": "item", "code": DOM + ":smokelesspowder", "stackSize": 16}}]
    ammo = [
        {"ingredientPattern": "H,P", "width": 1, "height": 2,
         "ingredients": {"H": {"type": "item", "code": "game:hammer-*", "isTool": True},
                         "P": {"type": "item", "code": "game:metalplate-brass"}},
         "output": {"type": "item", "code": DOM + ":casing", "quantity": 4}},
        {"ingredientPattern": "H,P,B", "width": 1, "height": 3,
         "ingredients": {"H": {"type": "item", "code": "game:hammer-*", "isTool": True},
                         "P": {"type": "item", "code": "game:metalplate-brass"},
                         "B": {"type": "item", "code": "game:blastingpowder"}},
         "output": {"type": "item", "code": DOM + ":primer", "quantity": 6}}]
    for m in ("lead", "copper"):
        ammo.append({
            "ingredientPattern": "CP,SB", "width": 2, "height": 2,
            "ingredients": {"C": {"type": "item", "code": DOM + ":casing", "quantity": 4},
                            "P": {"type": "item", "code": DOM + ":primer", "quantity": 4},
                            "S": {"type": "item", "code": DOM + ":smokelesspowder", "quantity": 2},
                            "B": {"type": "item", "code": "maltiezfirearms:bullet-" + m, "quantity": 4}},
            "output": {"type": "item", "code": DOM + ":cartridge-" + m, "quantity": 4}})
    R["grid/ammo.json"] = ammo
    R["grid/leveraction.json"] = [{
        "ingredientPattern": "PBN,WGP", "width": 3, "height": 2,
        "ingredients": {"P": {"type": "item", "code": "game:metalplate-steel"},
                        "B": {"type": "item", "code": "maltiezfirearms:barrel-carbine-steel"},
                        "N": {"type": "item", "code": "game:metalnailsandstrips-steel"},
                        "W": {"type": "item", "code": "game:plank-*"},
                        "G": {"type": "item", "code": "game:gear-rusty"}},
        "output": {"type": "item", "code": DOM + ":leveraction-carbine"}}]
    return R


LANG = {
    "item-smokelesspowder": "Smokeless powder",
    "item-guncotton": "Guncotton",
    "item-casing": "Brass case (.30-30)",
    "item-primer": "Primer",
    "item-cartridge-lead": ".30-30 cartridge (lead)",
    "item-cartridge-copper": ".30-30 cartridge (copper)",
    "item-leveraction-carbine": "Lever-action carbine",
    "itemdesc-smokelesspowder": "Nitrocellulose powder. Far stronger than black powder and leaves no smoke trail. Used to load metallic cartridges.",
    "itemdesc-guncotton": "Nitrated plant fibre. Soak in spirits in a sealed barrel to gelatinise it into smokeless powder.",
    "itemdesc-casing": "Empty brass case for a .30-30 cartridge.",
    "itemdesc-primer": "Percussion primer cup for metallic cartridges.",
    "itemdesc-cartridge-*": "Brass-cased .30-30 round loaded with smokeless powder. Fired from the lever-action carbine.",
    "itemdesc-leveraction-carbine": "Side-loading, lever-action repeating carbine (6 in the tube + 1 chambered).<br><br>Only reload when empty: hold right mouse to load through the side gate, then hold again to chamber a round and aim. Firing works the lever automatically.<br><br><i>Hold 'Alt' to interact instead of aim/reload.</i><br>",
    "iteminfo-rounds": "Rounds: {0}/{1}",
}


def make_pngs():
    random.seed(3030)
    tex = os.path.join(A, "textures")
    os.makedirs(tex, exist_ok=True)

    # the shared flat palette: solid 4x4 cells, no noise, no gradients
    pal = Image.new("RGBA", (16, 16), PALETTE[0][1] + (255,))
    d = ImageDraw.Draw(pal)
    for i, (_, rgb) in enumerate(PALETTE):
        cx, cy = i % 4, i // 4
        d.rectangle([cx * 4, cy * 4, cx * 4 + 3, cy * 4 + 3], fill=rgb + (255,))
    pal.save(os.path.join(tex, "palette.png"))

    def noise(path, base, var, size=16):
        im = Image.new("RGB", (size, size))
        px = im.load()
        for x in range(size):
            for y in range(size):
                dd = random.randint(-var, var)
                px[x, y] = tuple(max(0, min(255, c + dd)) for c in base)
        im.save(os.path.join(tex, path))

    noise("smokelesspowder.png", (58, 58, 62), 14)
    noise("guncotton.png", (226, 222, 210), 12)

    ic = Image.new("RGBA", (128, 128), (36, 30, 26, 255))
    d = ImageDraw.Draw(ic)
    d.rectangle([56, 22, 72, 84], fill=(201, 154, 58, 255))
    d.rectangle([52, 84, 76, 92], fill=(201, 154, 58, 255))
    d.polygon([(56, 22), (72, 22), (64, 6)], fill=(160, 160, 165, 255))
    d.rectangle([20, 104, 108, 112], fill=(90, 62, 40, 255))
    os.makedirs(os.path.join(ROOT, "resources"), exist_ok=True)
    ic.save(os.path.join(ROOT, "resources", "modicon.png"))


def main():
    w("shapes/firearms/leveraction.json", rifle_shape())
    for m in ("lead", "copper"):
        w(f"shapes/item/cartridge-{m}.json", shape_wrapper(lying(CART_PARTS(m), CART_YC)))
    w("shapes/item/casing.json", shape_wrapper(lying(CASING_PARTS, CART_YC)))
    w("shapes/item/primer.json", shape_wrapper(lying(PRIMER_PARTS, PRIMER_YC)))
    w("config/animations/leveraction.json", build_anims())
    w("itemtypes/leveraction.json", build_rifle_item())
    w("itemtypes/cartridge.json", build_cartridge_item())
    w("itemtypes/casing.json", simple_item("casing", "casing", 5.5, CART_YC))
    w("itemtypes/primer.json", simple_item("primer", "primer", 12, PRIMER_YC))
    w("itemtypes/smokelesspowder.json", build_powder_item("smokelesspowder"))
    w("itemtypes/guncotton.json", build_powder_item("guncotton"))
    w("entities/cartridge.json", build_entity())
    for path, obj in build_recipes().items():
        w("recipes/" + path, obj)
    w("lang/en.json", LANG)
    make_pngs()
    print("generated into", os.path.abspath(A))


if __name__ == "__main__":
    main()
