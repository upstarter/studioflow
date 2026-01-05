"""
Smart Media Organization Commands
Auto-tagging, search, and intelligent organization
"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from studioflow.core.smart_organization import SmartMediaOrganizer
from studioflow.core.media import MediaScanner

console = Console()
app = typer.Typer()


@app.command()
def organize(
    media_dir: Path = typer.Argument(..., help="Directory with media files"),
    auto_tag: bool = typer.Option(True, "--auto-tag/--no-auto-tag", help="Auto-tag files"),
    transcribe: bool = typer.Option(False, "--transcribe", help="Transcribe for search"),
):
    """
    Intelligently organize media with auto-tagging
    
    Examples:
        sf media-org organize /path/to/footage
        sf media-org organize /path/to/footage --transcribe
    """
    
    if not media_dir.exists():
        console.print(f"[red]Directory not found: {media_dir}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Organizing media in {media_dir}...[/cyan]\n")
    
    organizer = SmartMediaOrganizer()
    
    with console.status("[cyan]Analyzing and tagging files...[/cyan]"):
        files = organizer.organize_with_tags(media_dir, auto_tag=auto_tag, transcribe=transcribe)
    
    # Display results
    console.print(f"\n[green]✓ Organized {len(files)} files[/green]\n")
    
    # Show tags
    table = Table(title="Organized Media")
    table.add_column("File", style="cyan", width=30)
    table.add_column("Tags", style="yellow", width=30)
    table.add_column("Type", style="green", width=15)
    table.add_column("Quality", style="white", width=10)
    
    for file in files[:20]:  # Show first 20
        tags_str = ", ".join([t.name for t in file.tags[:3]])
        if len(file.tags) > 3:
            tags_str += "..."
        
        table.add_row(
            file.path.name,
            tags_str,
            file.content_type,
            f"{file.quality_score:.0f}/100"
        )
    
    console.print(table)
    
    if len(files) > 20:
        console.print(f"\n[dim]... and {len(files) - 20} more files[/dim]")


@app.command()
def search(
    media_dir: Path = typer.Argument(..., help="Directory to search"),
    query: str = typer.Argument(..., help="Search query"),
    search_transcripts: bool = typer.Option(True, "--transcripts/--no-transcripts", help="Search transcripts"),
):
    """
    Search media by tags, filename, or transcript content
    
    Examples:
        sf media-org search /path/to/footage "talking head"
        sf media-org search /path/to/footage "python tutorial" --transcripts
    """
    
    if not media_dir.exists():
        console.print(f"[red]Directory not found: {media_dir}[/red]")
        raise typer.Exit(1)
    
    console.print(f"[cyan]Searching for: '{query}'[/cyan]\n")
    
    organizer = SmartMediaOrganizer()
    results = organizer.search(media_dir, query, search_transcripts=search_transcripts)
    
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    console.print(f"[green]Found {len(results)} result(s)[/green]\n")
    
    # Display results
    table = Table(title="Search Results")
    table.add_column("File", style="cyan", width=30)
    table.add_column("Match Score", style="yellow", width=12)
    table.add_column("Tags", style="white", width=25)
    table.add_column("Type", style="green", width=15)
    
    for file in results[:20]:
        match_score = file.metadata.get("match_score", 0)
        tags_str = ", ".join([t.name for t in file.tags[:2]])
        
        table.add_row(
            file.path.name,
            f"{match_score:.2f}",
            tags_str,
            file.content_type
        )
    
    console.print(table)
    
    if len(results) > 20:
        console.print(f"\n[dim]... and {len(results) - 20} more results[/dim]")


@app.command()
def tag(
    file_path: Path = typer.Argument(..., help="Media file"),
    tags: List[str] = typer.Option([], "--tag", "-t", help="Tags to add"),
    remove: List[str] = typer.Option([], "--remove", "-r", help="Tags to remove"),
):
    """Add or remove tags from media files"""
    
    # This would update the metadata file
    console.print(f"[cyan]Tagging {file_path.name}...[/cyan]")
    
    # TODO: Implement tag management
    console.print("[yellow]Tag management coming soon[/yellow]")


if __name__ == "__main__":
    app()


