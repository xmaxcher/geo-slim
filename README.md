<div align="center">

# 🌐 geo-slim

**Slim GeoIP / GeoSite databases for RU routing in Xray / V2Ray based clients**

[![Build](https://github.com/xmaxcher/geo-slim/actions/workflows/build.yml/badge.svg)](https://github.com/xmaxcher/geo-slim/actions/workflows/build.yml)
[![Release](https://img.shields.io/github/v/release/xmaxcher/geo-slim?label=release&color=2ea44f)](https://github.com/xmaxcher/geo-slim/releases/latest)
[![Updated](https://img.shields.io/github/release-date/xmaxcher/geo-slim?label=updated&color=blue)](https://github.com/xmaxcher/geo-slim/releases/latest)
[![License](https://img.shields.io/github/license/xmaxcher/geo-slim?color=lightgrey)](LICENSE)

`geoip.dat` **~1.8 MB** · `geosite.dat` **~5.2 MB** · ~10× smaller than the full sets · rebuilt every 6 hours

</div>

---

## ✨ Why

The full community sets weigh **~90 MB** — too much for phones that re-download them on every routing
update. This build keeps only what a typical *"Russian traffic direct, blocked traffic via proxy"*
routing actually uses, in the same format and with the same category names, so it is a drop-in
replacement.

| | Full sets | geo-slim |
|---|---:|---:|
| `geoip.dat` | ~18 MB | **~1.8 MB** |
| `geosite.dat` | ~74 MB | **~5.2 MB** |
| Total | ~92 MB | **~7 MB** |

## 📥 Download

Always points to the newest build:

```
https://github.com/xmaxcher/geo-slim/releases/latest/download/geoip.dat
https://github.com/xmaxcher/geo-slim/releases/latest/download/geosite.dat
```

Every release also contains `geoip.dat.sha256`, `geosite.dat.sha256` and `sha256sums.txt`:

```sh
curl -LO https://github.com/xmaxcher/geo-slim/releases/latest/download/geoip.dat
curl -LO https://github.com/xmaxcher/geo-slim/releases/latest/download/geoip.dat.sha256
sha256sum -c geoip.dat.sha256
```

## 🗂 Categories

<details open>
<summary><b>geoip.dat</b> — 7 categories</summary>

| Category | What it is |
|---|---|
| `ru` | Russian IP ranges |
| `ru-whitelist` | Whitelisted Russian ranges |
| `ru-blocked` | IPs of resources blocked in Russia |
| `ru-blocked-community` | Community additions to the blocked list |
| `re-filter` | re:filter list |
| `yandex` | Yandex networks |
| `private` | Private / LAN ranges |

</details>

<details>
<summary><b>geosite.dat</b> — 22 categories</summary>

| Category | What it is |
|---|---|
| `category-ru` | Russian domains |
| `category-bank-ru` · `category-gov-ru` | Banks · government services |
| `category-ecommerce-ru` · `category-retail-ru` | Marketplaces · retail |
| `category-travel-ru` · `category-medicine-ru` | Travel · medicine |
| `category-entertainment-ru` · `category-media-ru` | Entertainment · media |
| `category-betting-ru` · `category-media-ru-blocked` | Betting · blocked media |
| `mailru` · `mailru-group` · `yandex` · `mts-ru` | Large Russian ecosystems |
| `myoffice-ru` · `ideco-ru` · `genotek-ru` | Specific services |
| `ru-available-only-inside` | Services reachable only from Russian IPs |
| `ru-blocked` | Domains blocked in Russia |
| `category-ads-all` | Ads and trackers |
| `private` | Local / private domains |

</details>

## 🧭 Example (Xray routing)

```json
{
  "routing": {
    "rules": [
      { "type": "field", "outboundTag": "block",  "domain": ["geosite:category-ads-all"] },
      { "type": "field", "outboundTag": "direct", "domain": ["geosite:private", "geosite:category-ru"] },
      { "type": "field", "outboundTag": "direct", "ip":     ["geoip:private", "geoip:ru"] },
      { "type": "field", "outboundTag": "proxy",  "network": "tcp,udp" }
    ]
  }
}
```

## ⚙️ How it is built

```
runetfreedom/russia-blocked-geoip   ─┐
                                     ├─►  build_slim.py  ─►  out/geoip.dat · out/geosite.dat  ─►  Release
runetfreedom/russia-blocked-geosite ─┘     (keep listed categories, verify, checksum)
```

- Sources: [runetfreedom/russia-blocked-geoip](https://github.com/runetfreedom/russia-blocked-geoip),
  [runetfreedom/russia-blocked-geosite](https://github.com/runetfreedom/russia-blocked-geosite).
- Runs every 6 hours; a new release appears **only when the content changes**.
- The build refuses to publish if a required category disappears or a file looks truncated —
  clients then simply keep the previous release.

Build locally:

```sh
mkdir -p src
curl -fsSL -o src/geoip.dat   https://github.com/runetfreedom/russia-blocked-geoip/releases/latest/download/geoip.dat
curl -fsSL -o src/geosite.dat https://github.com/runetfreedom/russia-blocked-geosite/releases/latest/download/geosite.dat
python3 build_slim.py          # → out/geoip.dat, out/geosite.dat
```

## 📄 License

[GPL-3.0](LICENSE), same as the upstream data.
