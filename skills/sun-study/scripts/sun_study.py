# /// script
# requires-python = ">=3.10"
# dependencies = ["pvlib>=0.11", "pandas>=2.0", "matplotlib>=3.7"]
# ///
"""
sun_study.py - sun position, sun-path diagram, shadow lengths and an optional EPW
climate summary for one site. NOT a compliance calculation.

Deps:   pvlib, pandas, matplotlib
Usage:  uv run sun_study.py --lat 52.37 --lon 4.90 --tz Europe/Amsterdam --out out/sun
                            [--height 12] [--year 2026] [--dates 2026-05-01,2026-08-15]
                            [--epw station.epw] [--base-temp 18]

Writes <out>_sunpath.png/.svg and <out>_report.md, and prints the same report.
- Times are LOCAL CLOCK TIME in --tz (daylight saving applied where the zone uses
  it). Solar noon is reported per date so clock and solar time can be compared.
- Solstice/equinox dates are the usual calendar approximations (20 Mar, 21 Jun,
  22 Sep, 21 Dec); the sun's position on the neighbouring day differs by well
  under a degree.
- Shadow length = height / tan(altitude), on flat level ground, for a vertical
  edge of the given height. Direction = sun azimuth + 180 deg.
- Solar position: pvlib NREL SPA. Azimuth is degrees clockwise from TRUE north.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import pvlib  # noqa: E402

BANNER = ("NOT A COMPLIANCE CALCULATION. Indicative sun geometry for early design only. "
          "Daylight, sunlight and overshadowing assessments need measured geometry, the "
          "applicable standard (e.g. BS EN 17037, BRE 209, local rules) and a qualified assessor.")


def die(msg: str) -> None:
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(1)


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def compass(az: float) -> str:
    pts = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return pts[int((az % 360) / 22.5 + 0.5) % 16]


def day_positions(loc: pvlib.location.Location, date: pd.Timestamp, step_min: int = 10) -> pd.DataFrame:
    times = pd.date_range(date, date + pd.Timedelta(days=1), freq=f"{step_min}min", tz=loc.tz, inclusive="left")
    sp = loc.get_solarposition(times)
    return sp[["apparent_elevation", "azimuth"]].rename(columns={"apparent_elevation": "alt", "azimuth": "az"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lat", type=float, required=True)
    ap.add_argument("--lon", type=float, required=True)
    ap.add_argument("--tz", required=True, help="IANA time zone, e.g. Europe/London, America/New_York")
    ap.add_argument("--out", required=True)
    ap.add_argument("--year", type=int, default=pd.Timestamp.now().year)
    ap.add_argument("--height", type=float, help="height in metres of an edge to compute shadow lengths for")
    ap.add_argument("--dates", help="extra dates, comma-separated YYYY-MM-DD")
    ap.add_argument("--epw", help="EnergyPlus weather file for a climate summary")
    ap.add_argument("--base-temp", type=float, default=18.0, help="degree-day base temperature, deg C")
    args = ap.parse_args()

    if not (-90 <= args.lat <= 90 and -180 <= args.lon <= 180):
        die("--lat/--lon out of range")
    try:
        loc = pvlib.location.Location(args.lat, args.lon, tz=args.tz)
        pd.Timestamp("2000-01-01", tz=args.tz)
    except Exception:
        die(f"unknown time zone {args.tz!r}; use an IANA name like Europe/Amsterdam")
    if args.height is not None and args.height <= 0:
        die("--height must be > 0 m")

    y = args.year
    south = args.lat < 0
    named = {f"{y}-03-20": "March equinox", f"{y}-06-21": "June solstice" + (" (winter)" if south else " (summer)"),
             f"{y}-09-22": "September equinox", f"{y}-12-21": "December solstice" + (" (summer)" if south else " (winter)")}
    if args.dates:
        for d in args.dates.split(","):
            try:
                pd.Timestamp(d.strip())
            except ValueError:
                die(f"bad date {d!r}")
            named.setdefault(d.strip(), "custom date")

    lines = [f"# Sun study: {args.lat:.4f}, {args.lon:.4f}", "", f"> {BANNER}", "",
             f"Time zone: {args.tz} (local clock time, DST applied where used) | Solar position: pvlib NREL SPA | "
             f"Azimuth: degrees clockwise from true north", ""]

    fig = plt.figure(figsize=(8, 8), dpi=200)
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.set_rlim(0, 90); ax.set_rticks([0, 15, 30, 45, 60, 75]); ax.set_yticklabels(["90", "75", "60", "45", "30", "15"], fontsize=7)
    ax.set_xticks([math.radians(a) for a in range(0, 360, 45)]); ax.set_xticklabels(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
    greys = ["#000000", "#555555", "#888888", "#b3261e", "#1f4e79", "#4f7a28"]

    for i, (d, label) in enumerate(sorted(named.items())):
        date = pd.Timestamp(d, tz=args.tz)
        sp = day_positions(loc, date)
        up = sp[sp.alt > 0]
        lines += [f"## {label}: {d}", ""]
        if up.empty:
            lines += ["Sun does not rise (polar night).", ""]
            continue
        noon = sp.alt.idxmax()
        rise, sets = up.index[0], up.index[-1]
        day_len = (sets - rise).total_seconds() / 3600 + 10 / 60
        lines.append(f"Sunrise ~{rise:%H:%M} at {sp.az[rise]:.0f} deg ({compass(sp.az[rise])}) | "
                     f"solar noon ~{noon:%H:%M} | max altitude {sp.alt[noon]:.1f} deg | "
                     f"sunset ~{sets:%H:%M} at {sp.az[sets]:.0f} deg ({compass(sp.az[sets])}) | "
                     f"day length ~{day_len:.1f} h (10-min resolution)")
        lines.append("")
        hdr = "| Clock time | Altitude | Azimuth |" + (f" Shadow of {args.height:g} m edge |" if args.height else "")
        lines += [hdr, "|---|---|---|" + ("---|" if args.height else "")]
        for t in pd.date_range(date, periods=24, freq="h"):
            alt, az = float(sp.alt.get(t, float("nan"))), float(sp.az.get(t, float("nan")))
            if not alt > 0:
                continue
            row = f"| {t:%H:%M} | {alt:.1f} deg | {az:.0f} deg {compass(az)} |"
            if args.height:
                L = args.height / math.tan(math.radians(alt))
                row += f" {L:.1f} m towards {compass(az + 180)}" + (" (very long, low sun)" if alt < 5 else "") + " |"
            lines.append(row)
        lines.append("")
        c = greys[i % len(greys)]
        ax.plot([math.radians(a) for a in up.az], [90 - a for a in up.alt], color=c, linewidth=1.4, label=f"{label} ({d})")
        hours = [t for t in pd.date_range(date, periods=24, freq="h") if t in up.index]
        ax.scatter([math.radians(sp.az[t]) for t in hours], [90 - sp.alt[t] for t in hours], s=8, color=c)
        if i == 0:
            for t in hours:
                ax.annotate(f"{t:%H}", (math.radians(sp.az[t]), 90 - sp.alt[t]), fontsize=6, xytext=(3, 3),
                            textcoords="offset points")

    ax.set_title(f"Sun path, {args.lat:.3f}, {args.lon:.3f}  ({args.tz}, clock time)", fontsize=10, pad=18)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=7, frameon=False)
    fig.text(0.5, -0.04, "Not a compliance calculation. Centre = overhead; rings = altitude. True north.",
             ha="center", fontsize=6.5, color="#444")

    if args.epw:
        try:
            data, meta = pvlib.iotools.read_epw(args.epw)
        except Exception as e:
            die(f"cannot read EPW {args.epw}: {e}")
        dist = haversine_km(args.lat, args.lon, meta["latitude"], meta["longitude"])
        lines += ["## Climate (EPW)", "",
                  f"Station: {meta.get('city', '?')}, {meta.get('state-prov', '')} {meta.get('country', '')} "
                  f"(WMO {meta.get('WMO_code', '?')}, {meta.get('data_type', '?')}), "
                  f"{meta['latitude']:.2f}, {meta['longitude']:.2f}, elevation {meta['altitude']:.0f} m",
                  f"Distance from site: {dist:.1f} km" + ("  WARNING: over 50 km - may not represent the site" if dist > 50 else ""),
                  f"Typical-year file: months are stitched from different years; use for design trends, not for a specific year.",
                  ""]
        t = data["temp_air"]; g = data["ghi"]
        m = pd.DataFrame({"mean": t.groupby(t.index.month).mean(), "max": t.groupby(t.index.month).max(),
                          "min": t.groupby(t.index.month).min(),
                          "ghi": g.groupby(g.index.month).sum() / 1000})
        lines += ["| Month | Mean temp | Max | Min | Global horiz. irradiation |", "|---|---|---|---|---|"]
        for mo, r in m.iterrows():
            lines.append(f"| {pd.Timestamp(2000, mo, 1):%b} | {r['mean']:.1f} C | {r['max']:.1f} C | {r['min']:.1f} C | {r['ghi']:.0f} kWh/m2 |")
        daily = t.resample("D").mean()
        hdd = (args.base_temp - daily).clip(lower=0).sum()
        cdd = (daily - args.base_temp).clip(lower=0).sum()
        ws = data["wind_speed"]; wd = data["wind_direction"]
        sectors = ((wd[ws > 0.5] % 360) / 45 + 0.5).astype(int) % 8
        names8 = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        freq = sectors.value_counts(normalize=True).sort_values(ascending=False)
        lines += ["", f"Annual global horizontal irradiation: {g.sum() / 1000:.0f} kWh/m2 (sum of hourly GHI)",
                  f"Degree days (base {args.base_temp:g} C, from daily mean temperature): heating {hdd:.0f} K.d, cooling {cdd:.0f} K.d",
                  "Prevailing wind (share of hours > 0.5 m/s by 45-deg sector): " +
                  ", ".join(f"{names8[k]} {v:.0%}" for k, v in freq.head(3).items()),
                  f"Mean wind speed: {ws.mean():.1f} m/s at the station (10 m mast; site exposure differs)", ""]

    lines += ["---", f"_{BANNER}_"]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    for ext in (".png", ".svg"):
        fig.savefig(out.with_name(out.name + "_sunpath" + ext), bbox_inches="tight", facecolor="#fff")
    report = "\n".join(lines)
    out.with_name(out.name + "_report.md").write_text(report)
    print(report)
    print(f"\nwrote: {out}_sunpath.png/.svg, {out}_report.md")


if __name__ == "__main__":
    main()
