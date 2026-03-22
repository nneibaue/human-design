"""
Demo of composite charts and emergent channel formation.

Shows how new channels can form when charts combine.
"""

from datetime import datetime

from human_design.models.bodygraph import BirthInfo, RawBodyGraph
from human_design.models.coordinates import LocalTime


def main():
    # Create two individual charts
    sandy = RawBodyGraph(
        birth_info=BirthInfo(
            date="1990-01-15",
            localtime=LocalTime(datetime(1990, 1, 15, 9, 13)),
            city="Albuquerque",
            country="NM",
        )
    )

    heath = RawBodyGraph(
        birth_info=BirthInfo(
            date="1985-06-20",
            localtime=LocalTime(datetime(1985, 6, 20, 14, 30)),
            city="Seattle",
            country="WA",
        )
    )

    print("=" * 70)
    print("INDIVIDUAL CHARTS")
    print("=" * 70)
    print(f"\nSandy ({sandy.type.value}, {sandy.authority.value}, {sandy.profile.profile_notation}):")
    print(f"  Activated gates: {sorted(sandy.all_activated_gates)}")
    print(f"  Active channels: {len(sandy.active_channels)}")
    print(f"  Defined centers: {sandy.defined_centers}")

    print(f"\nHeath ({heath.type.value}, {heath.authority.value}, {heath.profile.profile_notation}):")
    print(f"  Activated gates: {sorted(heath.all_activated_gates)}")
    print(f"  Active channels: {len(heath.active_channels)}")
    print(f"  Defined centers: {heath.defined_centers}")

    # Combine with + operator
    interaction = sandy + heath

    print("\n" + "=" * 70)
    print("INTERACTION CHART (Sandy + Heath)")
    print("=" * 70)
    print(f"\nComposite Type: {interaction.type.value}")
    print(f"Composite Authority: {interaction.authority.value}")
    print(f"Total activated gates: {len(interaction.all_activated_gates)}")
    print(f"Active channels: {len(interaction.active_channels)}")
    print(f"Defined centers: {interaction.defined_centers}")

    # Show emergent channels
    emergent = interaction.emergent_channels()
    if emergent:
        print(f"\n🌟 EMERGENT CHANNELS (formed when combined): {len(emergent)}")
        for ch in emergent:
            print(f"  Channel {ch.channel_id}: {ch.name} ({ch.gate_a}-{ch.gate_b})")
            print(f"    Connects: {ch.center_a} ↔ {ch.center_b}")
    else:
        print("\nNo emergent channels - all composite channels exist in individuals")

    # Add a third person for penta
    daughter = RawBodyGraph(
        birth_info=BirthInfo(
            date="2010-03-10",
            localtime=LocalTime(datetime(2010, 3, 10, 8, 0)),
            city="Portland",
            country="OR",
        )
    )

    print(f"\n\nDaughter ({daughter.type.value}, {daughter.authority.value}, {daughter.profile.profile_notation}):")
    print(f"  Activated gates: {sorted(daughter.all_activated_gates)}")
    print(f"  Active channels: {len(daughter.active_channels)}")

    # Create family penta
    family = sandy + heath + daughter

    print("\n" + "=" * 70)
    print("FAMILY PENTA (Sandy + Heath + Daughter)")
    print("=" * 70)
    print(f"\nComposite Type: {family.type.value}")
    print(f"Composite Authority: {family.authority.value}")
    print(f"Total activated gates: {len(family.all_activated_gates)}")
    print(f"Active channels: {len(family.active_channels)}")
    print(f"Defined centers: {family.defined_centers}")

    emergent_family = family.emergent_channels()
    if emergent_family:
        print(f"\n🌟 EMERGENT CHANNELS in family: {len(emergent_family)}")
        for ch in emergent_family:
            print(f"  Channel {ch.channel_id}: {ch.name} ({ch.gate_a}-{ch.gate_b})")


if __name__ == "__main__":
    main()
