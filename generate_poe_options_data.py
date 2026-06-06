#!/usr/bin/env python3
"""
Generate options_data.json for the PoE player options HTML page.
Run from the Archipelago root directory:
    python generate_poe_options_data.py
"""
import sys, os, json, inspect, re

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

try:
    import Utils
    AP_VERSION = '.'.join(str(x) for x in Utils.version_tuple)
except Exception:
    AP_VERSION = '0.6.7'

from Options import (
    Choice, Toggle, DefaultOnToggle, Range, OptionSet,
    ProgressionBalancing, Accessibility, DeathLink,
)
from worlds.poe.Options import poe_options_groups, poe_presets, PathOfExileOptions


# ── Helpers ───────────────────────────────────────────────────────────────────

def camel_to_snake(name):
    s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
    return s.lower()


def to_display(name):
    return ' '.join(w.capitalize() for w in name.split('_'))


def get_type(cls):
    if issubclass(cls, OptionSet):         return 'option_set'
    if issubclass(cls, Range):             return 'range'
    if issubclass(cls, (Toggle, DefaultOnToggle)): return 'toggle'
    if issubclass(cls, Choice):            return 'choice'
    return 'unknown'


def get_choices(cls):
    seen = {}
    for attr in dir(cls):
        if attr.startswith('option_'):
            val = getattr(cls, attr)
            if isinstance(val, int) and val not in seen:
                seen[val] = attr[7:]
    return [
        {'value': v, 'name': n, 'display_name': to_display(n)}
        for v, n in sorted(seen.items())
    ]


def serialize(field_name, cls):
    t = get_type(cls)
    out = {
        'name': field_name,
        'display_name': getattr(cls, 'display_name', to_display(field_name)),
        'type': t,
        'description': inspect.cleandoc(cls.__doc__ or ''),
    }

    if t == 'choice':
        out['choices'] = get_choices(cls)
        d = cls.default
        out['default'] = 'random' if d == 'random' else int(d)

    elif t == 'toggle':
        out['default'] = int(bool(cls.default))

    elif t == 'range':
        out['range_start'] = int(cls.range_start)
        out['range_end']   = int(cls.range_end)
        out['default']     = int(cls.default)
        nv = getattr(cls, 'named_values', None)
        if nv:
            out['named_values'] = [
                {'value': int(v), 'name': n, 'display_name': to_display(n)}
                for n, v in sorted(nv.items(), key=lambda x: x[1])
            ]

    elif t == 'option_set':
        out['valid_keys'] = sorted(str(k) for k in cls.valid_keys)
        d = cls.default
        out['default'] = sorted(str(x) for x in d) if hasattr(d, '__iter__') else []

    return out


def normalize_preset_val(v):
    if isinstance(v, bool):                         return int(v)
    if isinstance(v, (set, frozenset, list)):        return sorted(str(x) for x in v)
    if isinstance(v, int):                           return v
    return v


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    std_group = {
        'name': 'Game Options',
        'options': [
            serialize('progression_balancing', ProgressionBalancing),
            serialize('accessibility', Accessibility),
        ],
    }

    poe_grps = []
    for grp in poe_options_groups:
        opts = [serialize(camel_to_snake(cls.__name__), cls) for cls in grp.options]
        poe_grps.append({'name': grp.name, 'options': opts})

    other_group = {
        'name': 'Other',
        'options': [serialize('death_link', DeathLink)],
    }

    SKIP = {'start_inventory'}
    presets_out = {
        name: {k: normalize_preset_val(v) for k, v in vals.items() if k not in SKIP}
        for name, vals in poe_presets.items()
    }

    data = {
        'game': 'Path of Exile',
        'groups': [std_group] + poe_grps + [other_group],
        'presets': presets_out,
    }

    # ── Inject item/location valid_keys ───────────────────────────────────────
    manifest_path = os.path.join(BASE, 'worlds', 'poe', 'archipelago.json')
    items_path    = os.path.join(BASE, 'worlds', 'poe', 'poeClient', 'static', 'poe_items.json')
    locs_path     = os.path.join(BASE, 'worlds', 'poe', 'poeClient', 'static', 'poe_locations.json')

    with open(manifest_path, encoding='utf-8') as f:
        manifest = json.load(f)
    with open(items_path, encoding='utf-8') as f:
        item_names = sorted(json.load(f).keys())
    with open(locs_path, encoding='utf-8') as f:
        locs_map = json.load(f)
    # Order locations by AP ID (source-file order) rather than alphabetically.
    base_items_path  = os.path.join(BASE, 'worlds', 'poe', 'data', 'BaseItems.json')
    level_locs_path  = os.path.join(BASE, 'worlds', 'poe', 'data', 'LevelLocations.json')
    bosses_data_path = os.path.join(BASE, 'worlds', 'poe', 'data', 'Bosses.json')
    with open(base_items_path, encoding='utf-8') as f:
        base_items_raw = json.load(f)
    with open(level_locs_path, encoding='utf-8') as f:
        level_locs_raw = json.load(f)
    with open(bosses_data_path, encoding='utf-8') as f:
        bosses_order_raw = json.load(f)
    _seen: set = set()
    _ordered: list = []
    for item in base_items_raw:
        name = item.get('name') or item['baseItem']
        if name in locs_map and name not in _seen:
            _ordered.append(name); _seen.add(name)
    for item in level_locs_raw:
        name = item['name']
        if name in locs_map and name not in _seen:
            _ordered.append(name); _seen.add(name)
    for key in bosses_order_raw:
        name = f'defeat {key}'
        if name in locs_map and name not in _seen:
            _ordered.append(name); _seen.add(name)
    # Append anything not matched above (future-proofing)
    for name in locs_map:
        if name not in _seen:
            _ordered.append(name)
    location_names = _ordered

    ITEM_OPTS = {'local_items', 'non_local_items', 'start_hints'}
    LOC_OPTS  = {'start_location_hints', 'exclude_locations', 'priority_locations'}

    bosses_path = os.path.join(BASE, 'worlds', 'poe', 'data', 'Bosses.json')
    with open(bosses_path, encoding='utf-8') as f:
        bosses_raw = json.load(f)
    boss_category_order = ['Guardian', 'Pinnacle', 'Uber']
    boss_groups = {cat: [] for cat in boss_category_order}
    for key, info in bosses_raw.items():
        cat = info.get('difficulty', 'Other')
        boss_groups.setdefault(cat, []).append(key)

    for grp in data['groups']:
        for opt in grp['options']:
            if opt['name'] in ITEM_OPTS:
                opt['valid_keys'] = item_names
            elif opt['name'] in LOC_OPTS:
                opt['valid_keys'] = location_names
            elif opt['name'] == 'bosses_available':
                opt['boss_groups'] = boss_groups

    data['version_info'] = {
        'world_version':       manifest['world_version'],
        'ap_version':          AP_VERSION,
        'minimum_ap_version':  manifest.get('minimum_ap_version', AP_VERSION),
    }

    out_paths = [
        os.path.join(BASE, 'worlds', 'poe', 'poeClient', 'pathofexile_ap', 'options_data.json'),
        os.path.join(BASE, 'Path-of-Exile-Archipelago-Client', 'app', 'src', 'data', 'poe_options.json'),
        os.path.join(BASE, 'pathofexile_ap', 'options_data.json'),
    ]
    for out_path in out_paths:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f'Written: {out_path}')


if __name__ == '__main__':
    main()
