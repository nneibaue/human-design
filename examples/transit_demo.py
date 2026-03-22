"""
Demo of transit calculations and overlays.

Shows how current planetary positions can be overlaid on birth charts
to see influences at the present moment.
"""

from datetime import datetime

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime
from human_design.models.transit import Transit


def main():
    # Create birth chart
    birth_chart = RawBodyGraph(
        birth_info=BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
            city="Albuquerque",
            country="NM",
        )
    )

    print("=" * 70)
    print("BIRTH CHART")
    print("=" * 70)
    print(f"\nType: {birth_chart.type.value}")
    print(f"Authority: {birth_chart.authority.value}")
    print(f"Profile: {birth_chart.profile.profile_notation} ({birth_chart.profile.profile_name})")
    print(f"Active channels: {len(birth_chart.active_channels)}")
    print(f"Defined centers: {birth_chart.defined_centers}")

    # Create transit for current moment
    current_transit = Transit.now(location="Denver, CO")

    print("\n" + "=" * 70)
    print("CURRENT TRANSIT (Now)")
    print("=" * 70)
    print(f"\nActivated gates: {sorted(current_transit.all_activated_gates)}")
    print(f"Active channels: {len(current_transit.active_channels)}")
    print(f"Defined centers: {current_transit.defined_centers}")

    # Overlay transit on birth chart
    with_transit = birth_chart + current_transit

    print("\n" + "=" * 70)
    print("BIRTH CHART + CURRENT TRANSIT")
    print("=" * 70)
    print(f"\nComposite type: {with_transit.type.value}")
    print(f"Composite authority: {with_transit.authority.value}")
    print(f"Total gates: {len(with_transit.all_activated_gates)}")
    print(f"Active channels: {len(with_transit.active_channels)}")
    print(f"Defined centers: {with_transit.defined_centers}")

    # Check for emergent channels
    emergent = with_transit.emergent_channels()
    if emergent:
        print(f"\n🌟 EMERGENT CHANNELS (activated by transit): {len(emergent)}")
        for ch in emergent:
            print(f"  Channel {ch.channel_id}: {ch.name} ({ch.gate_a}-{ch.gate_b})")
            print(f"    Connects: {ch.center_a} ↔ {ch.center_b}")
    else:
        print("\nNo emergent channels from current transit")

    # Show specific historical transit
    print("\n" + "=" * 70)
    print("HISTORICAL TRANSIT (New Year's 2024)")
    print("=" * 70)

    nye_2024 = Transit.at(
        datetime(2024, 1, 1, 0, 0),
        location="Denver, CO"
    )

    print(f"\nTransit gates: {sorted(nye_2024.all_activated_gates)}")
    print(f"Transit channels: {len(nye_2024.active_channels)}")

    with_nye = birth_chart + nye_2024
    emergent_nye = with_nye.emergent_channels()

    if emergent_nye:
        print(f"\n🌟 EMERGENT CHANNELS at NYE 2024: {len(emergent_nye)}")
        for ch in emergent_nye:
            print(f"  Channel {ch.channel_id}: {ch.name} ({ch.gate_a}-{ch.gate_b})")

    # Show how transits change throughout the year
    print("\n" + "=" * 70)
    print("TRANSIT SNAPSHOT ACROSS 2024")
    print("=" * 70)

    months = [
        ("2024-01-01", "January"),
        ("2024-04-01", "April"),
        ("2024-07-01", "July"),
        ("2024-10-01", "October"),
    ]

    for date_str, month_name in months:
        year, month, day = map(int, date_str.split("-"))
        transit = Transit.at(
            datetime(year, month, day, 12, 0),
            location="Denver, CO"
        )
        with_t = birth_chart + transit
        emerg = with_t.emergent_channels()

        print(f"\n{month_name} 2024:")
        print(f"  Transit gates: {len(transit.all_activated_gates)}")
        print(f"  Composite channels: {len(with_t.active_channels)}")
        print(f"  Emergent channels: {len(emerg)}")
        if emerg:
            print(f"    → {', '.join(ch.name for ch in emerg[:3])}")


if __name__ == "__main__":
    main()
