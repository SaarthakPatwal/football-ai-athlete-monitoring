"""Explicit, offline fictional CSV writer. Never imported by the app.
Events are authored scenario dates, not labels computed from measurements.
Run from the repository root: python demo_data/generate_health_demo.py
"""
from datetime import date, timedelta
from pathlib import Path
import math
import csv

ROOT = Path(__file__).resolve().parent
START = date(2026, 5, 10)
DAYS = 150
# Authored fictional events spread through train, validation and test periods.
SCENARIOS = {f'P{i:03}': [22 + (i * 3) % 13, 64 + (i * 5) % 17, 105 + (i * 2) % 9, 135 + i % 8]
             for i in range(1, 13) if i % 4 != 0}


def write(name, rows):
    with (ROOT / name).open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    health, medical, outcomes = [], [], []
    for i in range(1, 13):
        pid = f'P{i:03}'
        events = SCENARIOS.get(pid, [])
        profile = (i - 1) % 3
        for day in range(DAYS):
            when = START + timedelta(days=day)
            wave = math.sin(day / 6 + i)
            # Deliberately imperfect fictional association: pre-event changes and non-event dips.
            onset = min((event - day for event in events if 0 <= event - day <= 10), default=99)
            burden = (11 - onset) / 11 if onset != 99 else 0
            burden += max(0, math.sin(day / 13 + i)) * .35
            health.append(dict(player_id=pid, date=when, resting_hr=round(49 + 4 * profile + 8 * burden + wave, 2),
                hrv=round(79 - 9 * profile - 17 * burden + 3 * wave, 2), sleep_hours=round(8.1 - .4 * profile - .9 * burden + .2 * wave, 2),
                sleep_quality=round(8.5 - profile - 1.5 * burden, 2), soreness=round(1.5 + profile + 2 * burden + .3 * wave, 2),
                fatigue=round(2 + profile + 2.5 * burden, 2), stress=round(2 + profile + 2 * burden, 2),
                energy_level=round(8.5 - profile - 2 * burden, 2), hydration_status=round(8.5 - .5 * profile - burden, 2),
                weight=round(62 + (i-1)*1.8 + .3 * wave, 2), body_fat_pct=round(10 + profile + .2 * wave, 2),
                blood_pressure_sys=round(112 + 3 * profile + wave, 2), blood_pressure_dia=round(70 + 2 * profile + wave, 2),
                oxygen_saturation=round(98 + .4 * wave, 2), body_temperature=round(36.5 + .15 * wave, 2)))
            outcomes.append(dict(player_id=pid, event_date=when, health_event=int(day in events)))
            if day % 30 == 0:
                medical.append(dict(player_id=pid, test_date=when, hemoglobin=round(14.8 - .2 * profile + .15 * wave, 2),
                    hematocrit=round(44 - profile + wave, 2), wbc_count=round(6 + .3 * wave, 2), platelet_count=240 + i,
                    ferritin=round(95 - 12 * profile - day * .08 + 3 * wave, 2) if i % 5 else '',
                    serum_iron=round(100 - 4 * profile + wave, 2), vitamin_d=round(37 - 3 * profile + wave, 2),
                    vitamin_b12=420 + i * 5 if day % 60 == 0 else '', glucose=round(88 + wave, 2),
                    creatinine=round(.9 + .02 * profile, 2), crp=round(1 + .2 * profile + .1 * wave, 2) if i % 4 else ''))
    write('health.csv', health)
    write('medical_tests.csv', medical)
    write('health_events.csv', outcomes)
    print(f'Fictional demonstration data — not real medical data. {len(health)} health, {len(medical)} medical, {len(outcomes)} outcome rows.')


if __name__ == '__main__':
    main()
