"""Compile supplied AAC/NAIA documents into the dashboard's normalized JSON payload."""

# ruff: noqa: E501

from __future__ import annotations

import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "backend/data/compiled/upike_stat_board.json"
PLAYER_PDF = (
    ROOT
    / "INFO/2025-26 Football Statistics - Pikeville (KY) - 2025-26 - NAIA Stats - Print Version.pdf"
)

STAT_HEADERS = ["metric", "overall", "overall_rank", "conference", "conference_rank", "opponent"]

TEAM_STATS_2025 = """
Games|10|2nd|6|3rd|10
Scoring|365|2nd|267|2nd|297
Points per game|36.5|2nd|44.5|2nd|29.7
Total offense|4628|2nd|2803|2nd|3842
Yards per game|462.8|1st|467.2|2nd|384.2
Passing yards|3646|1st|2158|1st|2565
Comp-Att-Int|337-486-9|1st|190-278-7|1st|162-314-7
Passing yards per game|364.6|1st|359.7|1st|256.5
Passing yards per attempt|7.5|2nd|7.8|4th|8.2
Passing yards per completion|10.8|5th|11.4|5th|15.8
Passing touchdowns|26|2nd|22|1st|21
Rushing yards|982|5th|645|5th|1277
Rushing attempts|294|6th|177|6th|333
Rushing yards per game|98.2|5th|107.5|5th|127.7
Yards per rush|3.3|5th|3.6|3rd|3.8
Rushing touchdowns|17|3rd|11|2nd|15
1st downs|277|1st|170|1st|199
Rushing 1st downs|77|4th|52|3rd|79
Passing 1st downs|172|1st|105|1st|101
Penalty 1st downs|28|1st|13|2nd|19
1st downs per game|27.7|1st|28.3|1st|-
3rd-down conversions|64-150|1st|34-80|4th|54-134
3rd down %|43%|2nd|43%|5th|40%
4th-down conversions|20-30|1st|15-20|1st|8-28
4th down %|67%|1st|75%|1st|29%
Kick returns (No.-Yards)|42-873|6th|26-599|2nd|56-1219
Kick return average|20.8|4th|23.0|2nd|21.8
Punt returns (No.-Yards)|15-88|3rd|10-60|2nd|10-65
Punt return average|5.9|5th|6.0|3rd|6.5
Field goals|11-15|2nd|4-7|3rd|7-13
Field goal %|73.3%|2nd|57.1%|3rd|53.8%
PATs|46-46|2nd|35-35|2nd|34-38
PAT %|100.0%|1st|100.0%|1st|89.5%
Punts (No.-Yards)|32-1304|3rd|13-587|6th|37-1340
Average per punt|40.8|1st|45.2|1st|36.2
Red zone scores|44-53|2nd|28-34|1st|28-37
Red zone %|83%|2nd|82%|2nd|76%
Red zone touchdowns|34-53|1st|25-34|1st|24-37
Red zone touchdown %|64%|2nd|74%|1st|65%
Fumbles-lost|15-12|2nd|10-8|3rd|8-6
Fumbles recovered|6|4th|6|2nd|12
Defensive INTs|7|5th|4|6th|-
Interception returns (No.-Yds)|7-22|7th|4-0|7th|9-151
Interception return average|3.1|7th|0.0|7th|16.8
Defensive TDs|2|2nd|2|2nd|-
Tackles|564|5th|360|6th|-
Sacks|16|5th|13|3rd|-
Penalties|93|6th|58|6th|94
Penalty yards|852|7th|548|7th|839
Time of possession per game|30:40|5th|28:25|5th|29:20
Home Attendance|7,048|1st|5,348|1st|16,926
Home Attendance average|1,410|1st|1,337|1st|-
"""

TEAM_STATS_2024 = """
Games|12|1st|6|3rd|12
Scoring|498|1st|334|1st|396
Points per game|41.5|1st|55.7|1st|33.0
Total offense|6001|1st|3413|1st|5055
Yards per game|500.1|1st|568.8|1st|421.3
Passing yards|4054|1st|2121|1st|3219
Comp-Att-Int|373-564-17|1st|202-281-8|1st|245-415-16
Passing yards per game|337.8|1st|353.5|1st|268.3
Passing yards per attempt|7.2|1st|7.5|2nd|7.8
Passing yards per completion|10.9|6th|10.5|6th|13.1
Passing touchdowns|40|1st|24|1st|36
Rushing yards|1947|2nd|1292|2nd|1836
Rushing attempts|363|3rd|218|4th|397
Rushing yards per game|162.3|2nd|215.3|2nd|153.0
Yards per rush|5.4|2nd|5.9|2nd|4.6
Rushing touchdowns|30|1st|22|1st|17
1st downs|349|1st|194|1st|270
Rushing 1st downs|126|1st|84|2nd|107
Passing 1st downs|199|1st|98|1st|141
Penalty 1st downs|24|2nd|12|4th|22
1st downs per game|29.1|1st|32.3|1st|-
3rd-down conversions|84-170|1st|43-85|2nd|74-155
3rd down %|49%|1st|51%|1st|48%
4th-down conversions|21-39|1st|14-22|1st|5-23
4th down %|54%|2nd|64%|1st|22%
Kick returns (No.-Yards)|49-882|3rd|23-430|4th|71-1042
Kick return average|18.0|4th|18.7|2nd|14.7
Punt returns (No.-Yards)|11-66|5th|11-66|4th|10-80
Punt return average|6.0|6th|6.0|5th|8.0
Field goals|1-3|5th|1-1|5th|7-12
Field goal %|33.3%|5th|100.0%|2nd|58.3%
PATs|57-64|1st|39-44|1st|47-49
PAT %|89.1%|4th|88.6%|4th|95.9%
Punts (No.-Yards)|33-1275|6th|11-413|7th|40-1472
Average per punt|38.6|1st|37.5|2nd|36.8
Red zone scores|56-65|1st|34-38|1st|34-41
Red zone %|86%|1st|89%|1st|83%
Red zone touchdowns|55-65|1st|33-38|1st|29-41
Red zone touchdown %|85%|1st|87%|1st|71%
Fumbles-lost|16-6|6th|10-4|5th|13-7
Fumbles recovered|7|7th|3|7th|6
Defensive INTs|16|1st|11|1st|-
Interception returns (No.-Yds)|16-125|2nd|11-111|2nd|17-166
Interception return average|7.8|6th|10.1|4th|9.8
Defensive TDs|0|5th|0|5th|-
Tackles|784|1st|363|6th|-
Sacks|28|4th|23|2nd|-
Penalties|111|7th|66|7th|94
Penalty yards|1094|7th|671|7th|840
Time of possession per game|30:15|3rd|32:30|3rd|29:15
Home Attendance|5,777|1st|3,108|1st|6,385
Home Attendance average|1,156|1st|1,036|1st|-
"""

GAME_LOG_HEADERS = [
    "date",
    "opponent",
    "score",
    "yds",
    "pass",
    "c_a",
    "comp_pct",
    "rush",
    "rush_att",
    "yards_per_rush",
    "int",
    "fum",
    "tackles",
    "sacks",
    "penalty_yards",
    "possession",
]

GAME_LOG_2025 = """
Aug 30|at Georgetown (Ky.)|L, 34-17|493|407|39-58|67%|86|29|3.0|1|-|49.0|1|68|32:37
Sep 13|at Campbellsville (KY)|L, 37-34|503|437|37-53|70%|66|27|2.4|-|-|45.0|-|39|33:47
Sep 20|Cumberland (Tenn.)|L, 21-17|312|271|31-41|76%|41|36|1.1|-|-|52.0|2|107|35:53
Sep 27|at Maryville (Tenn.)|L, 34-30|517|373|40-56|71%|144|25|5.8|2|0|58.0|0|90|34:00
Oct 11|Rio Grande|W, 44-0|650|444|38-52|73%|206|41|5.0|2|-|36.0|1|159|38:53
Oct 18|Point|W, 62-10|544|493|33-42|79%|51|23|2.2|-|2|62.0|7|78|23:05
Oct 25|at Bluefield (VA)|L, 43-40|418|263|17-31|55%|155|27|5.7|-|-|95.0|-|88|20:27
Nov 1|Union Commonwealth|W, 49-14|503|477|47-63|75%|26|22|1.2|1|-|42.0|-|63|32:29
Nov 8|Kentucky Christian|W, 51-42|338|216|30-46|65%|122|35|3.5|1|1|63.0|5|78|30:41
Nov 15|at Reinhardt (Ga.)|L, 62-21|350|265|25-44|57%|85|29|2.9|-|2|62.0|-|82|24:53
"""

GAME_LOG_2024 = """
Aug 29|Campbellsville (KY)|L, 34-33|465|441|34-55|62%|24|15|1.6|1|2|54.0|1|94|28:19
Sep 7|Georgetown (Ky.)|L, 23-20|388|319|34-47|72%|69|18|3.8|-|1|54.0|1|99|26:10
Sep 14|at Cumberlands (Ky.)|L, 52-20|340|240|24-48|50%|100|24|4.2|-|1|82.0|2|38|24:12
Sep 21|at Faulkner (AL)|L, 35-28|409|337|26-50|52%|72|23|3.1|1|1|67.0|1|99|27:31
Oct 5|Reinhardt (Ga.)|W, 47-21|557|299|35-51|69%|258|36|7.2|2|1|59.0|3|75|32:54
Oct 12|at Kentucky Christian|W, 66-34|626|448|38-56|68%|178|39|4.6|3|3|74.0|3|85|31:59
Oct 19|at Union Commonwealth|W, 62-35|502|320|33-50|66%|182|36|5.1|-|1|65.0|4|88|33:47
Oct 26|Bluefield (VA)|W, 48-34|604|160|24-33|73%|444|51|8.7|2|-|70.0|3|100|30:54
Nov 2|at Point|L, 23-21|387|248|31-44|70%|139|41|3.4|-|1|38.0|4|100|37:41
Nov 16|St. Andrews (NC)|W, 90-14|737|646|41-47|87%|91|15|6.1|4|1|57.0|6|223|27:48
Nov 23|at Baker|W, 42-35|552|310|24-35|69%|242|37|6.5|3|-|108.0|-|58|30:08
Nov 30|at Keiser (Fla.)|L, 56-21|434|286|29-48|60%|148|28|5.3|-|1|56.0|-|35|31:37
"""

GAME_IDS_2025 = [
    "20250830_dizi", "20250913_kqps", "20250920_xzbh", "20250927_uiom", "20251011_j14v",
    "20251018_1r1b", "20251025_nhhj", "20251101_rdne", "20251108_iabb", "20251115_cb1j",
]

APPEARANCES_2025 = """
Adam Wooten|20251011_j14v
Ahmad Fisher|20250830_dizi,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Ahmante Altman|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Alex Hatton|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Alex Lindsey|20250920_xzbh,20251018_1r1b,20251025_nhhj,20251108_iabb
Amon Williams|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251108_iabb,20251115_cb1j
Andre Thompson|20250927_uiom,20251115_cb1j
Brandon Newton|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Brett Coleman|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251115_cb1j
Caleb Anderson|20250830_dizi,20250913_kqps,20250920_xzbh,20251018_1r1b
Cobe Stribling|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Connor Goodman|20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
D'Vyne Cowan-Bazley|20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Dallas Kelly|20250830_dizi,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Damion Watts|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251108_iabb,20251115_cb1j
Deajuan McDougle|20250830_dizi,20250913_kqps,20250927_uiom
Demarcus Calhoun|20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Dige Savage|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Dylan Ferguson|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj
Elijah Roseburgh|20251018_1r1b,20251115_cb1j
Ethan Garn|20250830_dizi,20250913_kqps,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Gabe Marshall|20250830_dizi,20251018_1r1b
Grant Scott|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Guillermo Valadez|20250927_uiom
Hayden Russell|20250830_dizi,20250913_kqps,20251011_j14v,20251018_1r1b,20251025_nhhj,20251108_iabb,20251115_cb1j
Ian McCarty|20251018_1r1b,20251025_nhhj
Isaac Smith|20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Isaiah Esquibel|20250830_dizi,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Jalen Flowers|20250830_dizi,20250913_kqps,20251011_j14v,20251018_1r1b,20251025_nhhj,20251108_iabb,20251115_cb1j
Jayden Pepper|20250830_dizi,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Jeff Flowers|20250830_dizi,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Jonathan Besharatpour|20250830_dizi,20250913_kqps,20250927_uiom,20251018_1r1b,20251025_nhhj
Jordan Williams|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Kylan Ware|20251108_iabb
LaCharles Woodruff|20250913_kqps,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251115_cb1j
Landon Rowe|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251108_iabb,20251115_cb1j
Levi Evans|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Levi Wheeling|20251018_1r1b
Marcus Nunes|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Marshawn Boyden|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb
Maurice Davis|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Miguel Hernandez|20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Najmir Bellegarde|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Peter Zamora|20251011_j14v,20251018_1r1b
Porter Rode|20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne
Quentin Cremeans|20250830_dizi,20251018_1r1b
Quincy Clark|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Sa'Kuan Foster|20251011_j14v,20251101_rdne,20251108_iabb,20251115_cb1j
Tommy Turner|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Trevor Carter|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Ty Perkins|20251108_iabb,20251115_cb1j
Xavier Dahn|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251025_nhhj,20251101_rdne
Xavier Malone|20250830_dizi,20250913_kqps,20250920_xzbh,20250927_uiom,20251011_j14v,20251018_1r1b,20251025_nhhj,20251101_rdne,20251108_iabb,20251115_cb1j
Zach Morris|20250830_dizi,20250920_xzbh,20250927_uiom,20251025_nhhj,20251108_iabb
"""

SCHEDULE_HEADERS = ["date", "opponent", "result", "status", "notes"]
SCHEDULES = {
    "2023": """
Aug 26|at Campbellsville (KY)|W, 28-27|Final|
Sep 2|Cumberlands (KY)|L, 27-20|Final|
Sep 9|at Georgetown|L, 35-14|Final|Toyota Stadium - Georgetown, KY
Sep 16|Faulkner (AL)|W, 24-20|Final|
Sep 30|Union (KY)|W, 52-10|Final|Conference; Regional
Oct 7|at Reinhardt (GA)|L, 41-35|Final - 2OT|Conference; Regional
Oct 14|Kentucky Christian|W, 49-0|Final|Conference; Regional
Oct 21|at Bluefield (VA)|W, 51-42|Final|Conference; Regional
Oct 28|Point|W, 42-31|Final|Pikeville, Ky.; Conference; Regional
Nov 4|at St. Andrews (NC)|W, 68-0|Final|Senior Day; Conference
""",
    "2024": """
Aug 29|Campbellsville (KY)|L, 34-33|Final|
Sep 7|Georgetown|L, 23-20|Final|Pikeville, KY; Regional
Sep 14|at Cumberlands (KY)|L, 52-20|Final|Regional
Sep 21|at Faulkner (AL)|L, 35-28|Final|Regional
Oct 5|Reinhardt (GA)|W, 47-21|Final|Conference; Regional
Oct 12|at Kentucky Christian|W, 66-34|Final|Conference; Regional
Oct 19|at Union Commonwealth|W, 62-35|Final|Barbourville, Ky.; Conference; Regional
Oct 26|Bluefield (VA)|W, 48-34|Final|Conference
Nov 2|at Point|L, 23-21|Final|Valley, Ala.; Homecoming; Conference; Regional
Nov 16|St. Andrews (NC)|W, 90-14|Final|Conference
Nov 23|at Baker (KS)|W, 42-35|Final|NAIA FCS First Round; Baldwin City, Kan.
Nov 30|at Keiser|L, 56-21|Final|Postseason
""",
    "2025": """
Aug 30|at Georgetown|L, 34-17|Final|Toyota Stadium - Georgetown, KY; Regional
Sep 13|at Campbellsville (KY)|L, 37-34|Final|Regional
Sep 20|Cumberland (TN)|L, 21-17|Final|Regional
Sep 27|at Maryville (Tenn.)|L, 34-30|Final|
Oct 11|Rio Grande|W, 44-0|Final|Conference
Oct 18|Point|W, 62-10|Final|Conference; Regional
Oct 25|at Bluefield (VA)|L, 43-40|Final|Conference; Regional
Nov 1|Union Commonwealth|W, 49-14|Final|Conference; Regional
Nov 8|Kentucky Christian|W, 51-42|Final|Conference; Regional
Nov 15|at Reinhardt (GA)|L, 62-21|Final|Conference
""",
    "2026": """
Aug 27|at Arkansas Baptist||8:00 PM EDT|Next Event
Sep 5|Campbellsville (KY)||6:00 PM EDT|
Sep 12|Andrew College||3:00 PM EDT|
Sep 19|at Cumberland (TN)||7:00 PM EDT|
Sep 26|Bethel (TN)||3:00 PM EDT|
Oct 10|at Rio Grande||3:30 PM EDT|Conference
Oct 17|at Point||1:30 PM EDT|Valley, Ala. - Ram Stadium; Conference
Oct 24|Bluefield (VA)||6:00 PM EDT|Conference
Oct 31|at Union Commonwealth||3:00 PM EDT|Barbourville, Ky.; Williamson Stadium; Conference
Nov 7|at Kentucky Christian||1:30 PM EST|Conference
Nov 14|Reinhardt (GA)||1:00 PM EST|Pikeville, Kentucky; Conference
""",
}

PLAYER_FIELDS = {
    "Passing": ["GP", "CMP-ATT-INT", "PCT", "YDS", "TD", "LONG", "AVG/G"],
    "Rushing": ["GP", "ATT", "GAIN", "LOSS", "NET", "AVG", "TD", "LONG", "AVG/G"],
    "Receiving": ["GP", "REC", "REC/G", "YDS", "Y/G", "AVG", "TD", "LG"],
    "Punting": ["GP", "YDS", "AVG", "LONG", "TB", "FC", "I20", "BLK"],
    "Kicking": ["GP", "FGM", "FGA", "PCT", "LONG", "XPM", "XPA", "XP PCT", "PTS"],
    "Returns": [
        "KR",
        "KR YDS",
        "KR AVG",
        "KR TD",
        "KR LONG",
        "PR",
        "PR YDS",
        "PR AVG",
        "PR TD",
        "PR LONG",
    ],
    "Scoring": ["PTS", "PTS/G", "RUSH", "REC", "KR", "PR", "INT", "FUM", "XPM", "FGM", "2PT"],
    "Defensive Statistics": [
        "GP",
        "SOLO",
        "AST",
        "TOTAL",
        "TFL-YDS",
        "SCK-YDS",
        "INT-YDS",
        "BU",
        "FF",
        "FR-YDS",
        "BLK",
    ],
}


def parse_pipe_table(text: str, headers: list[str]) -> list[dict[str, str]]:
    rows = []
    for line in text.strip().splitlines():
        cells = line.split("|")
        if len(cells) != len(headers):
            raise ValueError(f"expected {len(headers)} cells, got {len(cells)}: {line}")
        rows.append(dict(zip(headers, cells, strict=True)))
    return rows


def parse_2025_game_log() -> list[dict[str, str]]:
    rows = parse_pipe_table(GAME_LOG_2025, GAME_LOG_HEADERS)
    for row, game_id in zip(rows, GAME_IDS_2025, strict=True):
        row["game_id"] = game_id
        row["source_url"] = (
            "https://naiastats.prestosports.com/sports/fball/2025-26/boxscores/"
            f"{game_id}.xml"
        )
    return rows


def parse_appearances() -> dict[str, list[str]]:
    appearances: dict[str, list[str]] = {}
    for line in APPEARANCES_2025.strip().splitlines():
        player, game_ids = line.split("|", maxsplit=1)
        appearances[player] = game_ids.split(",")
    return appearances


def parse_players() -> dict[str, dict[str, object]]:
    categories = {name: {"columns": fields, "rows": []} for name, fields in PLAYER_FIELDS.items()}
    active: str | None = None
    with pdfplumber.open(PLAYER_PDF) as pdf:
        for page in pdf.pages:
            for raw_line in (page.extract_text(layout=True) or "").splitlines():
                line = raw_line.strip()
                if line in PLAYER_FIELDS:
                    active = line
                    continue
                if active is None or not re.match(r"^\d+\s", line):
                    continue
                tokens = line.split()
                fields = PLAYER_FIELDS[active]
                if len(tokens) < len(fields) + 2:
                    continue
                jersey = tokens[0]
                values = tokens[-len(fields) :]
                name = " ".join(tokens[1 : -len(fields)]).rstrip(".")
                categories[active]["rows"].append(
                    {
                        "jersey": jersey,
                        "player": name.rstrip("."),
                        **dict(zip(fields, values, strict=True)),
                    }
                )
    return categories


def main() -> None:
    seasons = {
        "2023": {
            "label": "2023-24",
            "record": "7-3",
            "conference_record": "5-1",
            "region_record": "5-2",
            "home": "4-1",
            "away": "3-2",
            "neutral": "0-0",
            "streak": "W4",
            "schedule": parse_pipe_table(SCHEDULES["2023"], SCHEDULE_HEADERS),
        },
        "2024": {
            "label": "2024-25",
            "record": "6-6",
            "conference_record": "5-1",
            "region_record": "3-4",
            "home": "3-2",
            "away": "3-4",
            "neutral": "0-0",
            "streak": "L1",
            "national_rank": "68",
            "aac_rank": "3",
            "headline": {
                "Yds/Game": "500.1",
                "Rush/Game": "162.3",
                "Pass/Game": "337.8",
                "Pts/Game": "41.5",
                "Yds Allowed/Game": "421.3",
                "Rush Allowed/Game": "153.0",
                "Pass Allowed/Game": "268.3",
                "Pts Allowed/Game": "33.0",
            },
            "team_stats": parse_pipe_table(TEAM_STATS_2024, STAT_HEADERS),
            "game_log": parse_pipe_table(GAME_LOG_2024, GAME_LOG_HEADERS),
            "schedule": parse_pipe_table(SCHEDULES["2024"], SCHEDULE_HEADERS),
        },
        "2025": {
            "label": "2025-26",
            "record": "4-6",
            "conference_record": "4-2",
            "region_record": "3-4",
            "home": "4-1",
            "away": "0-5",
            "neutral": "0-0",
            "streak": "L1",
            "national_rank": "65",
            "aac_rank": "3",
            "headline": {
                "Yds/Game": "462.8",
                "Rush/Game": "98.2",
                "Pass/Game": "364.6",
                "Pts/Game": "36.5",
                "Yds Allowed/Game": "384.2",
                "Rush Allowed/Game": "127.7",
                "Pass Allowed/Game": "256.5",
                "Pts Allowed/Game": "29.7",
            },
            "team_stats": parse_pipe_table(TEAM_STATS_2025, STAT_HEADERS),
            "game_log": parse_2025_game_log(),
            "schedule": parse_pipe_table(SCHEDULES["2025"], SCHEDULE_HEADERS),
            "players": parse_players(),
            "appearances": parse_appearances(),
        },
        "2026": {
            "label": "2026-27",
            "record": "0-0",
            "conference_record": "0-0",
            "home": "0-0",
            "away": "0-0",
            "neutral": "0-0",
            "streak": "-",
            "schedule": parse_pipe_table(SCHEDULES["2026"], SCHEDULE_HEADERS),
        },
    }
    payload = {
        "team": "Pikeville (KY)",
        "conference": "Appalachian Athletic Conference",
        "default_season": "2025",
        "seasons": seasons,
        "sources": [
            {"label": "2025 NAIA team statistics", "path": str(PLAYER_PDF.relative_to(ROOT))},
            *[
                {
                    "label": f"{year}-{str(int(year) + 1)[-2:]} AAC schedule",
                    "path": (
                        f"INFO/{year}-{str(int(year) + 1)[-2:]} AAC Football Schedule - "
                        "Appalachian Athletic Conference - Print Version.pdf"
                    ),
                }
                for year in ("2023", "2024", "2025", "2026")
            ],
            {
                "label": "NAIA team profile",
                "url": "https://naiastats.prestosports.com/sports/fball/2025-26/conf/Appalachian/teams/pikevilleky?jsRendering=true",
            },
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "seasons": len(seasons),
                "player_rows": sum(
                    len(value["rows"]) for value in seasons["2025"]["players"].values()
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
