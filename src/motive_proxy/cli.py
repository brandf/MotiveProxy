"""Command-line interface for MotiveProxy."""

import click
import uvicorn
from motive_proxy.settings import get_settings


@click.group()
def cli():
    """MotiveProxy - A bidirectional proxy for OpenAI-compatible clients."""
    pass


@cli.command()
@click.option("--host", default=None, help="Host to bind to")
@click.option("--port", default=None, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--log-level", default=None, help="Logging level (debug, info, warning, error)")
@click.option("--debug", is_flag=True, help="Enable debug mode")
def run(host: str, port: int, reload: bool, log_level: str, debug: bool):
    """MotiveProxy - A bidirectional proxy for OpenAI-compatible clients."""
    settings = get_settings()
    
    # Override settings with CLI arguments
    if host is not None:
        settings.host = host
    if port is not None:
        settings.port = port
    if log_level is not None:
        settings.log_level = log_level
    if debug:
        settings.debug = True
        settings.log_level = "DEBUG"
    
    # Display effective configuration
    click.echo("Starting MotiveProxy with configuration:")
    click.echo(f"   Host: {settings.host}")
    click.echo(f"   Port: {settings.port}")
    click.echo(f"   Debug: {settings.debug}")
    click.echo(f"   Log Level: {settings.log_level}")
    click.echo(f"   Handshake Timeout: {settings.handshake_timeout_seconds}s")
    click.echo(f"   Turn Timeout: {settings.turn_timeout_seconds}s")
    click.echo(f"   Session TTL: {settings.session_ttl_seconds}s")
    click.echo(f"   Max Sessions: {settings.max_sessions}")
    click.echo(f"   Auto-reload: {reload}")
    click.echo()
    
    # Start the server
    uvicorn.run(
        "motive_proxy.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


# E2E testing is handled by a separate tool, not part of MotiveProxy core


def main():
    """Main CLI entry point."""
    cli()


if __name__ == "__main__":
    main()