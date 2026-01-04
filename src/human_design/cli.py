"""
64keys.com Scraper CLI

A Typer-based command-line application for scraping Human Design gate information
from 64keys.com with proper authentication.
"""

import json
from datetime import datetime

import typer

from .api import bodygraph_to_summary, get_gate, get_gates, get_home_page
from .models import BirthInfo, LocalTime, RawBodyGraph

app = typer.Typer(help="Scraper for 64keys.com Human Design data")


@app.command()
def bodygraph(
    date: str = typer.Argument(help="Birth date in YYYY-MM-DD format (e.g., 1990-01-15)"),
    time: str = typer.Argument(help="Birth time in HH:MM format (e.g., 09:13)"),
    city: str = typer.Argument(help="Birth city"),
    state: str = typer.Argument(help="Birth state/province"),
    raw: bool = typer.Option(False, "--raw", help="Output raw bodygraph without 64keys content"),
) -> None:
    """
    Calculate a Human Design bodygraph and output as JSON.

    Examples:
        human-design bodygraph 1990-01-15 09:13 Albuquerque NM
        human-design bodygraph 1990-01-15 09:13 Albuquerque NM --raw
        human-design bodygraph 2000-06-21 12:30 London UK
    """
    try:
        # Parse time
        time_parts = time.split(":")
        if len(time_parts) != 2:
            typer.echo(f"❌ Invalid time format: {time}. Use HH:MM", err=True)
            raise typer.Exit(code=1)

        hour, minute = int(time_parts[0]), int(time_parts[1])
        local_dt = datetime(
            int(date.split("-")[0]), int(date.split("-")[1]), int(date.split("-")[2]), hour, minute
        )

        # Create birth info
        typer.echo(f"📊 Calculating bodygraph for {city}, {state} on {date} at {time}...", err=True)
        birth_info = BirthInfo(
            date=date,
            localtime=LocalTime(local_dt),
            city=city,
            country=state,
        )

        # Calculate raw bodygraph
        raw_bodygraph = RawBodyGraph(birth_info=birth_info)

        if raw:
            # Output raw bodygraph as JSON
            json_output = raw_bodygraph.model_dump_json(indent=2)
        else:
            # Convert to summary via API
            typer.echo("🔄 Converting to 64keys summary...", err=True)
            summary = bodygraph_to_summary(raw_bodygraph)
            json_output = summary.model_dump_json(indent=2)

        # Output as JSON
        typer.echo(json_output)

    except ValueError as e:
        typer.echo(f"❌ Invalid input: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def gate(
    gate_number: int = typer.Argument(help="Gate number (1-64)", min=1, max=64),
    line: float | None = typer.Option(None, help="Optional line number (e.g., 11.4)"),
) -> None:
    """
    Fetch and display Human Design gate information.

    Examples:
        human-design gate 11           # Get Gate 11 info
        human-design gate 11 --line 11.4  # Get Gate 11, Line 4 info
    """
    try:
        typer.echo("🔐 Authenticating...", err=False)
        gate_data = get_gate(gate_number)
        typer.echo(" ✓", err=False)

        # Display results
        typer.echo("\n" + "=" * 60)
        typer.secho(f"Gate {gate_data.number}: {gate_data.name}", bold=True)
        typer.echo("=" * 60)
        typer.echo(f"Quarter: {gate_data.quarter}")
        typer.echo(f"\n📝 Summary:\n{gate_data.summary}\n")
        typer.echo(f"💡 Description:\n{gate_data.description}\n")
        typer.echo(f"🎯 Strive:\n{gate_data.strive}\n")

        # Display lines
        typer.secho("Lines:", bold=True)
        typer.echo("-" * 60)

        for gate_line in gate_data.lines:
            if line is None or gate_line.line_number == line:
                typer.echo(f"  {gate_line.line_number} - {gate_line.title}")
                typer.echo(f"    {gate_line.text}\n")

        typer.echo("=" * 60)

    except ValueError as e:
        typer.echo(f"\n❌ Invalid input: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def cache_gates() -> None:
    """
    Cache all 64 Human Design gates locally.
    """
    try:
        typer.echo("🔐 Authenticating...", err=False)
        gate_numbers: list[int] = list(range(1, 65))
        # TODO: fix typing
        gates = get_gates(gate_numbers)  # type: ignore
        typer.echo(" ✓", err=False)

        export = [g.model_dump() for g in gates.values()]
        typer.echo("\n💾 Caching gates locally...", err=False)
        with open("gates.json", "w") as f:
            json.dump(export, f, indent=2)
        typer.echo(" ✓")

        typer.echo("✅ All gates cached successfully!")

    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def show_gates(
    gate_numbers: str = typer.Argument(help="Gate numbers (e.g., '1 2 11 42' or '1-10')"),
) -> None:
    """
    Fetch and display multiple Human Design gates in one command.

    Examples:
        human-design gates "1 2 11 42"           # Get multiple gates
        human-design gates "1-10"                # Get gates 1 through 10
    """
    try:
        # Parse gate numbers
        parsed_gates: list[int] = []

        for part in gate_numbers.split():
            if "-" in part:
                # Handle range (e.g., "1-10")
                try:
                    start, end = part.split("-")
                    start_num, end_num = int(start.strip()), int(end.strip())
                    parsed_gates.extend(range(start_num, end_num + 1))
                except ValueError as e:
                    typer.echo(f"❌ Invalid range format: {part}", err=True)
                    raise typer.Exit(code=1) from e
            else:
                try:
                    parsed_gates.append(int(part))
                except ValueError as e:
                    typer.echo(f"❌ Invalid gate number: {part}", err=True)
                    raise typer.Exit(code=1) from e

        # Validate gate numbers
        for gate_num in parsed_gates:
            if not 1 <= gate_num <= 64:
                typer.echo(f"❌ Gate number must be between 1 and 64, got {gate_num}", err=True)
                raise typer.Exit(code=1)

        if not parsed_gates:
            typer.echo("❌ No valid gate numbers provided", err=True)
            raise typer.Exit(code=1)

        typer.echo("🔐 Authenticating...", err=False)
        # TODO: fix typing
        gates_data = get_gates(parsed_gates)  # type: ignore
        typer.echo(" ✓")

        # Display results
        for gate_data in gates_data.values():
            typer.echo("\n" + "=" * 60)
            typer.secho(f"Gate {gate_data.number}: {gate_data.name}", bold=True)
            typer.echo("=" * 60)
            typer.echo(f"Quarter: {gate_data.quarter}")
            typer.echo(f"\n📝 Summary:\n{gate_data.summary}\n")
            typer.echo(f"💡 Description:\n{gate_data.description}\n")
            typer.echo(f"🎯 Strive:\n{gate_data.strive}\n")

            # Display lines
            typer.secho("Lines:", bold=True)
            typer.echo("-" * 60)

            for gate_line in gate_data.lines:
                typer.echo(f"  {gate_line.line_number} - {gate_line.title}")
                typer.echo(f"    {gate_line.text}\n")

        typer.echo("=" * 60)

    except ValueError as e:
        typer.echo(f"\n❌ Invalid input: {e}", err=True)
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def home() -> None:
    """Fetch and save the 64keys homepage."""
    try:
        typer.echo("🔐 Authenticating...", err=False)
        typer.echo(" ✓", err=False)

        typer.echo("\n📖 Fetching homepage...", err=False)
        html_content = get_home_page()
        typer.echo(" ✓", err=False)

        typer.echo("\n💾 Saving to home.html...", err=False)
        with open("home.html", "w") as f:
            f.write(html_content)
        typer.echo(" ✓")

        typer.echo("✅ Done! Saved to home.html")

    except Exception as e:
        typer.echo(f"\n❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from None


if __name__ == "__main__":
    app()
