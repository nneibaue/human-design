"""
64keys.com Scraper CLI

A Typer-based command-line application for scraping Human Design gate information
from 64keys.com with proper authentication.
"""

import json
from datetime import datetime, timedelta

import typer

try:
    import boto3
    from rich.console import Console
    from rich.table import Table

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from .api import bodygraph_to_summary, get_gate, get_gates, get_home_page
from .models import BirthInfo, LocalTime, RawBodyGraph

app = typer.Typer(help="Scraper for 64keys.com Human Design data")

# AWS sub-commands
aws_app = typer.Typer(help="AWS infrastructure commands")
app.add_typer(aws_app, name="aws")


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


# AWS Commands
@aws_app.command("jobs")
def aws_jobs(
    queue: str = typer.Option("transcribe-queue", "--queue", "-q", help="Job queue name"),
    limit: int = typer.Option(20, "--limit", "-n", help="Number of jobs to show"),
    status: str = typer.Option(
        "ALL", "--status", "-s", help="Filter by status (RUNNING, SUCCEEDED, FAILED, ALL)"
    ),
) -> None:
    """
    Monitor AWS Batch jobs for transcription.

    Examples:
        hd aws jobs                           # Show all recent jobs
        hd aws jobs --status RUNNING          # Show only running jobs
        hd aws jobs --limit 50                # Show last 50 jobs
    """
    if not AWS_AVAILABLE:
        typer.echo("❌ Error: boto3 and rich are required. Install with: pip install -e '.[dev]'", err=True)
        raise typer.Exit(code=1)

    try:
        console = Console()
        batch = boto3.client("batch")

        # Determine which statuses to query
        if status.upper() == "ALL":
            statuses = ["SUBMITTED", "PENDING", "RUNNABLE", "STARTING", "RUNNING", "SUCCEEDED", "FAILED"]
        else:
            statuses = [status.upper()]

        # Fetch jobs
        console.print(f"🔍 Fetching jobs from queue: [cyan]{queue}[/cyan]...")
        all_jobs = []

        for job_status in statuses:
            try:
                response = batch.list_jobs(
                    jobQueue=queue, jobStatus=job_status, maxResults=min(limit, 100)
                )
                all_jobs.extend(response.get("jobSummaryList", []))
            except Exception as e:
                console.print(f"[yellow]⚠ Could not fetch {job_status} jobs: {e}[/yellow]")

        if not all_jobs:
            console.print(f"[yellow]No jobs found in queue '{queue}'[/yellow]")
            return

        # Sort by creation time (newest first)
        all_jobs.sort(key=lambda x: x.get("createdAt", 0), reverse=True)
        all_jobs = all_jobs[:limit]

        # Create table
        table = Table(title=f"AWS Batch Jobs - {queue}", show_header=True, header_style="bold magenta")
        table.add_column("Job Name", style="cyan", width=40)
        table.add_column("Status", justify="center", width=12)
        table.add_column("Created", width=20)
        table.add_column("Duration", justify="right", width=12)

        for job in all_jobs:
            job_name = job["jobName"]
            job_status_display = job["status"]

            # Color code status
            if job_status_display == "SUCCEEDED":
                status_display = f"[green]{job_status_display}[/green]"
            elif job_status_display == "FAILED":
                status_display = f"[red]{job_status_display}[/red]"
            elif job_status_display == "RUNNING":
                status_display = f"[yellow]{job_status_display}[/yellow]"
            else:
                status_display = f"[blue]{job_status_display}[/blue]"

            # Format timestamps
            created_at = datetime.fromtimestamp(job["createdAt"] / 1000)
            created_str = created_at.strftime("%Y-%m-%d %H:%M:%S")

            # Calculate duration if available
            if "startedAt" in job:
                started = datetime.fromtimestamp(job["startedAt"] / 1000)
                if "stoppedAt" in job:
                    stopped = datetime.fromtimestamp(job["stoppedAt"] / 1000)
                    duration = stopped - started
                else:
                    duration = datetime.now() - started
                duration_str = str(duration).split(".")[0]  # Remove microseconds
            else:
                duration_str = "-"

            table.add_row(job_name, status_display, created_str, duration_str)

        console.print(table)

        # Summary stats
        status_counts = {}
        for job in all_jobs:
            s = job["status"]
            status_counts[s] = status_counts.get(s, 0) + 1

        console.print("\n[bold]Summary:[/bold]")
        for s, count in sorted(status_counts.items()):
            console.print(f"  {s}: {count}")

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@aws_app.command("billing")
def aws_billing(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to show"),
    breakdown: bool = typer.Option(True, "--breakdown/--no-breakdown", help="Show service breakdown"),
) -> None:
    """
    Show AWS billing and cost breakdown.

    Examples:
        hd aws billing                    # Show last 30 days
        hd aws billing --days 7           # Show last 7 days
        hd aws billing --no-breakdown     # Hide service breakdown
    """
    if not AWS_AVAILABLE:
        typer.echo("❌ Error: boto3 and rich are required. Install with: pip install -e '.[dev]'", err=True)
        raise typer.Exit(code=1)

    try:
        console = Console()
        ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer is us-east-1 only

        # Calculate date range
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        console.print(f"💰 Fetching billing data from [cyan]{start_date}[/cyan] to [cyan]{end_date}[/cyan]...")

        # Get total cost
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": str(start_date), "End": str(end_date)},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )

        total_cost = 0.0
        for result in response["ResultsByTime"]:
            amount = float(result["Total"]["UnblendedCost"]["Amount"])
            total_cost += amount

        console.print(f"\n[bold]Total Cost ({days} days):[/bold] [green]${total_cost:.2f}[/green]")

        # Get service breakdown if requested
        if breakdown:
            response_by_service = ce.get_cost_and_usage(
                TimePeriod={"Start": str(start_date), "End": str(end_date)},
                Granularity="MONTHLY",
                Metrics=["UnblendedCost"],
                GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
            )

            # Parse service costs
            service_costs = {}
            for result in response_by_service["ResultsByTime"]:
                for group in result["Groups"]:
                    service = group["Keys"][0]
                    amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                    if amount > 0:  # Only show services with cost
                        service_costs[service] = service_costs.get(service, 0) + amount

            if service_costs:
                # Sort by cost (descending)
                sorted_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)

                # Create table
                table = Table(
                    title=f"Service Breakdown ({days} days)",
                    show_header=True,
                    header_style="bold magenta",
                )
                table.add_column("Service", style="cyan", width=50)
                table.add_column("Cost", justify="right", style="green", width=15)
                table.add_column("% of Total", justify="right", width=12)

                for service, cost in sorted_services:
                    pct = (cost / total_cost * 100) if total_cost > 0 else 0
                    table.add_row(service, f"${cost:.2f}", f"{pct:.1f}%")

                console.print("\n")
                console.print(table)
            else:
                console.print("\n[yellow]No service breakdown available[/yellow]")

        # Show forecast if available
        try:
            forecast_response = ce.get_cost_forecast(
                TimePeriod={
                    "Start": str(end_date),
                    "End": str(end_date + timedelta(days=30)),
                },
                Metric="UNBLENDED_COST",
                Granularity="MONTHLY",
            )
            forecast_amount = float(forecast_response["Total"]["Amount"])
            console.print(f"\n[bold]30-day Forecast:[/bold] [yellow]${forecast_amount:.2f}[/yellow]")
        except Exception:
            pass  # Forecast not always available

    except Exception as e:
        typer.echo(f"❌ Error: {e}", err=True)
        typer.echo("\n💡 Tip: Make sure Cost Explorer is enabled in your AWS account", err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
