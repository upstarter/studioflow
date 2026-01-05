"""
Enhanced Export Commands with Validation
Export with YouTube compliance checking
"""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from studioflow.core.export_validator import ExportValidator
from studioflow.core.ffmpeg import FFmpegProcessor
from studioflow.core.resolve_profiles import ResolveProfiles

console = Console()
app = typer.Typer()


@app.command()
def youtube(
    video_path: Path = typer.Argument(..., help="Video file to export"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Validate export"),
    quality: str = typer.Option("4k", "--quality", "-q", help="Quality: 4k/1080/720"),
    show_command: bool = typer.Option(False, "--show-command", help="Show FFmpeg command"),
):
    """
    Export video for YouTube with validation
    
    Examples:
        sf export youtube video.mp4
        sf export youtube video.mp4 --validate --quality 4k
    """
    
    if not video_path.exists():
        console.print(f"[red]File not found: {video_path}[/red]")
        raise typer.Exit(1)
    
    # Get export settings
    settings = ResolveProfiles.get_youtube_settings(quality)
    
    # Determine output path
    if not output:
        output = video_path.parent / f"{video_path.stem}_youtube_{quality}.mp4"
    
    console.print(f"[cyan]Exporting for YouTube {quality.upper()}...[/cyan]\n")
    
    # Show settings
    table = Table(title="Export Settings", show_header=False, box=None)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    
    for key, value in settings.items():
        if key not in ["command"]:
            table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(table)
    console.print()
    
    # Export
    with console.status(f"[cyan]Exporting to {output.name}...[/cyan]"):
        result = FFmpegProcessor.export_for_platform(
            video_path,
            platform="youtube",
            output_file=output,
            **settings
        )
    
    if not result.success:
        console.print(f"[red]Export failed: {result.error_message}[/red]")
        raise typer.Exit(1)
    
    # Validate
    if validate:
        console.print("\n[cyan]Validating export...[/cyan]")
        validator = ExportValidator()
        validation = validator.validate_youtube(output)
        
        if validation["valid"]:
            console.print("[green]✓ Export validated - ready for YouTube![/green]")
        else:
            console.print("[yellow]⚠ Export has issues:[/yellow]")
            for error in validation.get("errors", []):
                console.print(f"  ❌ {error}")
            for warning in validation.get("warnings", []):
                console.print(f"  ⚠️  {warning}")
            
            if validation.get("errors"):
                console.print("\n[yellow]Fix errors before uploading[/yellow]")
    
    # Show file info
    size_mb = output.stat().st_size / (1024**2)
    console.print(f"\n[green]✓ Exported: {output}[/green]")
    console.print(f"  Size: {size_mb:.1f} MB")
    
    if show_command:
        command = ResolveProfiles.generate_export_command(video_path, f"youtube_{quality}")
        console.print(f"\n[bold]FFmpeg Command:[/bold]")
        console.print(Panel(command, border_style="cyan"))


@app.command()
def validate(
    video_path: Path = typer.Argument(..., help="Video file to validate"),
    platform: str = typer.Option("youtube", "--platform", "-p", help="Platform: youtube/instagram/tiktok"),
):
    """Validate video export for platform compliance"""
    
    if not video_path.exists():
        console.print(f"[red]File not found: {video_path}[/red]")
        raise typer.Exit(1)
    
    validator = ExportValidator()
    
    if platform == "youtube":
        result = validator.validate_youtube(video_path)
    else:
        console.print(f"[yellow]Platform '{platform}' validation not yet implemented[/yellow]")
        return
    
    # Display results
    console.print(f"\n[bold]Validation Results for {video_path.name}[/bold]\n")
    
    if result["valid"]:
        console.print("[green]✓ PASS - Video is compliant![/green]\n")
    else:
        console.print("[red]✗ FAIL - Video has issues[/red]\n")
    
    # Errors
    if result.get("errors"):
        console.print("[bold red]Errors:[/bold red]")
        for error in result["errors"]:
            console.print(f"  ❌ {error}")
        console.print()
    
    # Warnings
    if result.get("warnings"):
        console.print("[bold yellow]Warnings:[/bold yellow]")
        for warning in result["warnings"]:
            console.print(f"  ⚠️  {warning}")
        console.print()
    
    # Details
    if result.get("details"):
        table = Table(title="Video Details", show_header=False, box=None)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in result["details"].items():
            table.add_row(key.replace("_", " ").title(), str(value))
        
        console.print(table)


if __name__ == "__main__":
    app()

