"""Command-line interface for Payment Claim Detector."""

from pathlib import Path
from typing import Optional

import typer

from payment_claim_detector.main import run_analysis
from payment_claim_detector.settings import get_settings

app = typer.Typer()
settings = get_settings()


@app.command()
def run(
    tracker_file: Path = typer.Option(..., "--tracker-file", "-t", help="Path to historical tracker workbook"),
    register_file: Path = typer.Option(..., "--register-file", "-r", help="Path to weekly payment register"),
    output_dir: Path = typer.Option(settings.data.output_dir, "--output-dir", "-o", help="Output directory"),
    start_date: Optional[str] = typer.Option(None, "--start-date", help="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = typer.Option(None, "--end-date", help="End date filter (YYYY-MM-DD)"),
    processed_log: Optional[Path] = typer.Option(None, "--processed-log", help="Path to processed payment log CSV"),
    state: Optional[str] = typer.Option(None, "--state", "-s", help="Restrict analysis to one state (e.g. ID, CO, NV, UT)"),
    ttd_only: bool = typer.Option(False, "--ttd-only", help="Filter to TTD payments only (payment_description contains TTD)"),
) -> None:
    """Run payment claim detection analysis."""
    typer.echo(f"Processing tracker: {tracker_file}")
    typer.echo(f"Processing register: {register_file}")
    typer.echo(f"Output directory: {output_dir}")
    if state:
        typer.echo(f"State filter: {state.upper()}")
    if ttd_only:
        typer.echo("Payment type filter: TTD only")

    run_analysis(
        tracker_file=tracker_file,
        register_file=register_file,
        output_dir=output_dir,
        start_date=start_date,
        end_date=end_date,
        processed_payment_log=processed_log,
        state_filter=state,
        ttd_only=ttd_only,
    )

    typer.echo("Analysis complete!")


@app.command()
def version() -> None:
    """Show version information."""
    from payment_claim_detector import __version__
    typer.echo(f"Payment Claim Detector v{__version__}")


if __name__ == "__main__":
    app()