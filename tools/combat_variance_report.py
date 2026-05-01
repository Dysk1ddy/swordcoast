from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dnd_game.gameplay.combat_variance import build_default_variance_report


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Report combat variance across fixed seeds.")
    parser.add_argument("--seed-start", type=int, default=1001)
    parser.add_argument("--seeds", type=int, default=100)
    args = parser.parse_args()
    seeds = tuple(range(args.seed_start, args.seed_start + max(1, args.seeds)))
    report = build_default_variance_report(seeds)

    print("# Combat Variance Report")
    print()
    print(f"Seeds: `{seeds[0]}` to `{seeds[-1]}`")
    print()
    print("## Action Profiles")
    print()
    print("| Action | Samples | Mean | CV | Zero | P10 | P50 | P90 | Crit | Crit Damage Share |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for profile in report.action_profiles:
        print(
            f"| {profile.name} | {profile.sample_count} | {profile.mean_damage:.2f} | "
            f"{profile.coefficient_of_variation:.2f} | {percent(profile.zero_result_chance)} | "
            f"{profile.p10_damage} | {profile.p50_damage} | {profile.p90_damage} | "
            f"{percent(profile.critical_chance)} | {percent(profile.critical_damage_share)} |"
        )
    print()
    print("## Encounter Profiles")
    print()
    print("| Encounter | Seeds | Victory | Rounds P10 | Rounds P50 | Rounds P90 | Downed Mean | Downed P90 |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for profile in report.encounter_profiles:
        print(
            f"| {profile.name} | {profile.seed_count} | {percent(profile.victory_rate)} | "
            f"{profile.rounds_p10} | {profile.rounds_p50} | {profile.rounds_p90} | "
            f"{profile.downed_allies_mean:.2f} | {profile.downed_allies_p90} |"
        )


if __name__ == "__main__":
    main()
