"""Generate sample database command."""

from pathlib import Path

import click


@click.command()
@click.option(
    "--database",
    type=click.Path(path_type=Path),
    help="Path to database file (default: uses LEGGEN_DATABASE_PATH or ~/.config/leggen/leggen-dev.db)",
)
@click.option(
    "--accounts",
    type=int,
    default=3,
    help="Number of sample accounts to generate (default: 3)",
)
@click.option(
    "--transactions",
    type=int,
    default=50,
    help="Number of transactions per account (default: 50)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing database without confirmation",
)
@click.pass_context
def generate_sample_db(
    ctx: click.Context, database: Path, accounts: int, transactions: int, force: bool
):
    """Generate a sample database with realistic financial data for testing."""

    # Import here to avoid circular imports
    import subprocess
    import sys
    from pathlib import Path as PathlibPath

    # Get the script path
    script_path = (
        PathlibPath(__file__).parent.parent.parent / "scripts" / "generate_sample_db.py"
    )

    # Build command arguments
    cmd = [sys.executable, str(script_path)]

    if database:
        cmd.extend(["--database", str(database)])

    cmd.extend(["--accounts", str(accounts)])
    cmd.extend(["--transactions", str(transactions)])

    if force:
        cmd.append("--force")

    # Execute the script
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"Error generating sample database: {e}")
        ctx.exit(1)


# Export the command
generate_sample_db = generate_sample_db
