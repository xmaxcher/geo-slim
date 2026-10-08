import os, sys, struct

"""Slim GeoIP/GeoSite builder: keeps only the categories listed below.

Input:  src/geoip.dat, src/geosite.dat  (runetfreedom/russia-blocked-geoip, russia-blocked-geosite)
Output: out/geoip.dat, out/geosite.dat
Exit code 1 if a required category is missing or the output looks truncated.
"""
HERE = os.path.dirname(os.path.abspath(__file__))
GEOIP_SRC = os.path.join(HERE, "src", "geoip.dat")
GEOSITE_SRC = os.path.join(HERE, "src", "geosite.dat")
GEOIP_OUT = os.path.join(HERE, "out", "geoip.dat")
GEOSITE_OUT = os.path.join(HERE, "out", "geosite.dat")

# Without these the routing makes no sense: refuse to publish.
GEOIP_REQUIRED = {"RU", "RU-BLOCKED", "PRIVATE"}
GEOSITE_REQUIRED = {"CATEGORY-RU", "RU-BLOCKED", "CATEGORY-ADS-ALL", "PRIVATE"}
MIN_GEOIP_BYTES = 500_000
MIN_GEOSITE_BYTES = 2_000_000

GEOIP_KEEP = {
    "RU", "RU-WHITELIST", "RU-BLOCKED", "RU-BLOCKED-COMMUNITY",
    "RE-FILTER", "YANDEX", "PRIVATE",
}

GEOSITE_KEEP = {
    "CATEGORY-RU",
    "CATEGORY-BANK-RU",
    "CATEGORY-GOV-RU",
    "CATEGORY-ECOMMERCE-RU",
    "CATEGORY-RETAIL-RU",
    "CATEGORY-TRAVEL-RU",
    "CATEGORY-MEDICINE-RU",
    "CATEGORY-ENTERTAINMENT-RU",
    "CATEGORY-BETTING-RU",
    "CATEGORY-MEDIA-RU",
    "CATEGORY-MEDIA-RU-BLOCKED",
    "MAILRU",
    "MAILRU-GROUP",
    "MTS-RU",
    "MYOFFICE-RU",
    "IDECO-RU",
    "GENOTEK-RU",
    "YANDEX",
    "RU-AVAILABLE-ONLY-INSIDE",
    "RU-BLOCKED",
    "CATEGORY-ADS-ALL",
    "PRIVATE",
}


def read_varint(b, p):
    r = 0; s = 0
    while True:
        x = b[p]; p += 1
        r |= (x & 0x7F) << s
        if not (x & 0x80):
            return r, p
        s += 7


def iter_fields(b, end):
    p = 0
    while p < end:
        tag, p = read_varint(b, p)
        wt = tag & 7
        fn = tag >> 3
        if wt == 0:
            v, p = read_varint(b, p); yield fn, v, None
        elif wt == 2:
            ln, p = read_varint(b, p); yield fn, None, b[p:p+ln]; p += ln
        elif wt == 1:
            p += 8
        elif wt == 5:
            p += 4
        else:
            raise ValueError(f"unknown wire_type={wt}")


def write_varint(n):
    out = bytearray()
    while True:
        byte = n & 0x7F
        n >>= 7
        if n:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


def w_tag(field_num, wire_type):
    return write_varint((field_num << 3) | wire_type)


def w_string(field_num, s):
    payload = s.encode("utf-8") if isinstance(s, str) else s
    return w_tag(field_num, 2) + write_varint(len(payload)) + payload


def w_varint(field_num, val):
    return w_tag(field_num, 0) + write_varint(val)


def w_embedded(field_num, payload):
    return w_tag(field_num, 2) + write_varint(len(payload)) + payload


def filter_geoip(src_path, keep_set):
    with open(src_path, "rb") as f:
        data = f.read()
    out_entries = []
    kept_stats = {}
    for fn, vi, vb in iter_fields(data, len(data)):
        if fn != 1 or vb is None:
            continue
        country = ""
        for ifn, ivi, ivb in iter_fields(vb, len(vb)):
            if ifn == 1 and ivb is not None:
                country = ivb.decode("utf-8", errors="replace")
                break
        if country.upper() in keep_set:
            out_entries.append(vb)
            cnt = sum(1 for f, _, _ in iter_fields(vb, len(vb)) if f == 2)
            kept_stats[country] = cnt
    out = b"".join(w_embedded(1, e) for e in out_entries)
    return out, kept_stats


def filter_geosite(src_path, keep_set):
    with open(src_path, "rb") as f:
        data = f.read()
    out_entries = []
    kept_stats = {}
    for fn, vi, vb in iter_fields(data, len(data)):
        if fn != 1 or vb is None:
            continue
        country = ""
        for ifn, ivi, ivb in iter_fields(vb, len(vb)):
            if ifn == 1 and ivb is not None:
                country = ivb.decode("utf-8", errors="replace")
                break
        if country.upper() in keep_set:
            out_entries.append(vb)
            cnt = sum(1 for f, _, _ in iter_fields(vb, len(vb)) if f == 2)
            kept_stats[country] = cnt
    out = b"".join(w_embedded(1, e) for e in out_entries)
    return out, kept_stats


def fmt_size(n):
    if n < 1024: return f"{n} B"
    if n < 1024 * 1024: return f"{n/1024:.1f} KB"
    return f"{n/1024/1024:.2f} MB"


if __name__ == "__main__":
    os.makedirs(os.path.dirname(GEOIP_OUT), exist_ok=True)
    errors = []
    print("=" * 70)
    print("Building geoip.dat")
    print("=" * 70)
    src_size = os.path.getsize(GEOIP_SRC)
    out, stats = filter_geoip(GEOIP_SRC, GEOIP_KEEP)
    with open(GEOIP_OUT, "wb") as f: f.write(out)
    out_size = os.path.getsize(GEOIP_OUT)
    print(f"Source : {fmt_size(src_size)}")
    print(f"Output : {fmt_size(out_size)}  ({out_size*100/src_size:.2f}% of source)")
    print()
    print("Kept categories:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k:30s} {v:>10,} CIDRs")
    missing = GEOIP_KEEP - set(s.upper() for s in stats)
    if missing:
        print(f"\nWARNING: not found in source: {missing}")
    if GEOIP_REQUIRED & missing:
        errors.append(f"geoip: required categories missing: {GEOIP_REQUIRED & missing}")
    if out_size < MIN_GEOIP_BYTES:
        errors.append(f"geoip: output too small ({out_size} B)")

    print()
    print("=" * 70)
    print("Building geosite.dat")
    print("=" * 70)
    src_size = os.path.getsize(GEOSITE_SRC)
    out, stats = filter_geosite(GEOSITE_SRC, GEOSITE_KEEP)
    with open(GEOSITE_OUT, "wb") as f: f.write(out)
    out_size = os.path.getsize(GEOSITE_OUT)
    print(f"Source : {fmt_size(src_size)}")
    print(f"Output : {fmt_size(out_size)}  ({out_size*100/src_size:.2f}% of source)")
    print()
    print("Kept categories:")
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {k:30s} {v:>10,} domains")
    missing = GEOSITE_KEEP - set(s.upper() for s in stats)
    if missing:
        print(f"\nWARNING: not found in source: {missing}")
    if GEOSITE_REQUIRED & missing:
        errors.append(f"geosite: required categories missing: {GEOSITE_REQUIRED & missing}")
    if out_size < MIN_GEOSITE_BYTES:
        errors.append(f"geosite: output too small ({out_size} B)")

    print()
    print("=" * 70)
    print(f"TOTAL: {fmt_size(os.path.getsize(GEOIP_OUT) + os.path.getsize(GEOSITE_OUT))}")
    print(f"Source total: {fmt_size(os.path.getsize(GEOIP_SRC) + os.path.getsize(GEOSITE_SRC))}")
    print("=" * 70)
    if errors:
        print()
        for e in errors:
            print(f"ERROR: {e}")
        sys.exit(1)
