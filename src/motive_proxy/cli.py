"""Command-line interface for MotiveProxy."""

import click
import uvicorn

from motive_proxy.app import create_app


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to",
    show_default=True,
)
@click.option(
    "--port",
    default=8000,
    type=int,
    help="Port to bind the server to",
    show_default=True,
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
@click.option(
    "--log-level",
    default="info",
    type=click.Choice(["critical", "error", "warning", "info", "debug"]),
    help="Log level",
    show_default=True,
)
def main(host: str, port: int, reload: bool, log_level: str) -> None:
    """Run the MotiveProxy server."""
    app = create_app()

    click.echo(f"🚀 Starting MotiveProxy server on http://{host}:{port}")
    click.echo(f"📚 API documentation available at http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
