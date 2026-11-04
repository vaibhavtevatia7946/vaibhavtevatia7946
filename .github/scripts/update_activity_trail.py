import html
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import date
from pathlib import Path


owner = os.environ["GITHUB_REPOSITORY"].split("/", 1)[0]
url = f"https://github.com/users/{owner}/contributions"
request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(request, timeout=30) as response:
    page = response.read().decode("utf-8")

days = re.findall(r'<td[^>]*data-date="(\d{4}-\d{2}-\d{2})"[^>]*id="([^"]+)"', page)
tooltips = dict(
    re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>(.*?)</tool-tip>', page, re.DOTALL)
)
if not days:
    raise RuntimeError(f"No contribution dates found for {owner}")

daily_counts = {}
for day, component_id in days:
    tooltip = html.unescape(tooltips.get(component_id, ""))
    count = re.search(r"\b(\d+)\s+contributions?\b", tooltip)
    if count:
        daily_counts[day] = int(count.group(1))
    elif "no contributions" in tooltip.lower():
        daily_counts[day] = 0
    else:
        raise RuntimeError(f"Could not read contribution count for {day}")

latest_day = max(date.fromisoformat(day) for day in daily_counts)
first_month = latest_day.year * 12 + latest_day.month - 12
months = []
for offset in range(12):
    month_index = first_month + offset
    year, month = divmod(month_index, 12)
    months.append((year, month + 1))

monthly_counts = defaultdict(int)
for day, count in daily_counts.items():
    parsed_day = date.fromisoformat(day)
    key = (parsed_day.year, parsed_day.month)
    if key in months:
        monthly_counts[key] += count

width, height, baseline = 1100, 360, 280
bar_width, bar_step, first_x = 42, 80, 72
max_count = max(monthly_counts.values(), default=0)
max_height = 150
bars = []
labels = []
for index, (year, month) in enumerate(months):
    x = first_x + index * bar_step
    count = monthly_counts[(year, month)]
    bar_height = max(4, round(count / max_count * max_height)) if max_count else 4
    y = baseline - bar_height
    color = "#2da44e" if count == max_count and count else "#72d594" if count else "#b9efcb"
    bars.append(
        f'<rect x="{x}" y="{y}" width="{bar_width}" height="{bar_height}" '
        f'rx="2" fill="{color}"/>'
    )
    labels.append(
        f'<text x="{x + bar_width / 2:g}" y="304">{date(year, month, 1):%b}</text>'
    )

hops = ";".join(
    f"{65 + index * bar_step} {max(55, baseline - min(max_height, monthly_counts[month] / max_count * max_height) - 76):.0f}"
    if max_count else f"{65 + index * bar_step} 204"
    for index, month in enumerate(months)
)
hops = f"{hops};65 204"
total = sum(monthly_counts.values())
updated = latest_day.strftime("%d %b %Y").upper()
bar_markup = "".join(bars)
label_markup = "".join(labels)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">Vaibhav's hopping GitHub activity trail</title>
<desc id="desc">A pixel bunny hops across monthly contribution bars in a green and white theme. {total} contributions are shown from the last 12 months, through {updated}.</desc>
<rect x="1" y="1" width="1098" height="358" rx="14" fill="#fff" stroke="#d0d7de"/>
<text x="26" y="34" fill="#57606a" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="12" font-weight="700" letter-spacing="1.4">~/ RANDOM HOP CONTRIBUTIONS</text>
<text x="1074" y="34" text-anchor="end" fill="#57606a" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="700" letter-spacing=".8">UPDATED {updated}</text>
<line x1="28" y1="{baseline}" x2="1072" y2="{baseline}" stroke="#aeb8c1" stroke-width="2" stroke-dasharray="2 5"/>
<g>{bar_markup}</g>
<g fill="#57606a" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="10" font-weight="700" text-anchor="middle">{label_markup}</g>
<g shape-rendering="crispEdges">
<animateTransform attributeName="transform" type="translate" values="{hops}" dur="14s" repeatCount="indefinite"/>
<rect x="13" y="0" width="9" height="25" fill="#24292f"/><rect x="16" y="3" width="4" height="18" fill="#fff"/>
<rect x="33" y="4" width="9" height="22" fill="#24292f"/><rect x="36" y="7" width="4" height="15" fill="#fff"/>
<rect x="9" y="21" width="39" height="8" fill="#24292f"/><rect x="5" y="27" width="47" height="21" fill="#24292f"/>
<rect x="10" y="30" width="37" height="15" fill="#fff"/><rect x="11" y="45" width="35" height="7" fill="#24292f"/>
<rect x="17" y="49" width="10" height="5" fill="#24292f"/><rect x="33" y="49" width="10" height="5" fill="#24292f"/>
<rect x="20" y="31" width="3" height="4" fill="#24292f"/><rect x="39" y="31" width="3" height="4" fill="#24292f"/>
<rect x="47" y="37" width="5" height="5" fill="#24292f"/><rect x="49" y="38" width="2" height="2" fill="#2da44e"/>
</g>
<text x="28" y="338" fill="#57606a" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" font-weight="700" letter-spacing=".7">HEIGHT = MONTHLY CONTRIBUTIONS · PIXEL HOPS REPEAT</text>
<text x="1072" y="338" text-anchor="end" fill="#57606a" font-family="ui-monospace, SFMono-Regular, Menlo, monospace" font-size="9" font-weight="700" letter-spacing=".6">CONTRIBUTIONS · LAST 12 MONTHS</text>
</svg>'''

ET.fromstring(svg)
Path("assets/activity-trail.svg").write_text(svg, encoding="utf-8")
print(f"Updated activity trail through {updated} ({total} contributions).")
