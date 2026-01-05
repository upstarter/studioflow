"""YouTube Commands"""

import typer
from pathlib import Path
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from studioflow.core.state import StateManager
from studioflow.core.youtube_api import YouTubeAPIService
from studioflow.core.viral import ViralOptimizer


console = Console()
app = typer.Typer()


@app.command()
def upload(
    video_path: Path = typer.Argument(..., help="Path to video file"),
    title: str = typer.Option(..., "--title", "-t", help="Video title"),
    description: str = typer.Option("", "--description", "-d", help="Video description"),
    tags: str = typer.Option("", "--tags", help="Comma-separated tags"),
    privacy: str = typer.Option("private", "--privacy", "-p", help="Privacy: private/unlisted/public"),
    thumbnail: Optional[Path] = typer.Option(None, "--thumbnail", help="Thumbnail image path")
):
    """
    Upload video to YouTube

    Examples:
        sf youtube upload video.mp4 --title "My Video" --description "Description"
        sf youtube upload final.mp4 -t "Tutorial" --tags "python,coding" --privacy unlisted
        sf youtube upload render.mp4 -t "Vlog" --thumbnail thumb.jpg
    """
    if not video_path.exists():
        console.print(f"[red]Video file not found: {video_path}[/red]")
        raise typer.Exit(1)

    # Parse tags
    tags_list = [tag.strip() for tag in tags.split(",")] if tags else []

    # Initialize YouTube API
    service = YouTubeAPIService()

    # Check for credentials
    credentials_file = service.config_dir / 'credentials.json'
    if not credentials_file.exists():
        console.print("\n[yellow]YouTube API Setup Required:[/yellow]")
        console.print("1. Go to: https://console.cloud.google.com/")
        console.print("2. Create new project or select existing")
        console.print("3. Enable 'YouTube Data API v3'")
        console.print("4. Create OAuth 2.0 credentials")
        console.print("5. Download credentials.json")
        console.print(f"6. Place in: {credentials_file}")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        # Add upload task
        task = progress.add_task(
            f"Uploading {video_path.name} to YouTube...",
            total=None
        )

        # Upload video
        result = service.upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags_list,
            privacy=privacy,
            thumbnail_path=thumbnail
        )

        progress.update(task, completed=True)

    if not result["success"]:
        console.print(f"[red]Upload failed: {result.get('error')}[/red]")
        raise typer.Exit(1)

    # Display success
    console.print("\n[green]✓ Video uploaded successfully![/green]\n")

    table = Table(title="Upload Details")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Video ID", result["id"])
    table.add_row("URL", result["url"])
    table.add_row("Title", result["title"])
    table.add_row("Status", result["status"])

    console.print(table)
    console.print(f"\n[bold]View your video:[/bold] {result['url']}")

    if privacy == "private":
        console.print("[yellow]Note: Video is private. Change visibility in YouTube Studio.[/yellow]")

    return result


@app.command()
def optimize(
    topic: str = typer.Argument(..., help="Video topic/keyword"),
    style: str = typer.Option("educational", "--style", "-s", help="Style: educational/entertainment/tutorial/review"),
    platform: str = typer.Option("youtube", "--platform", help="Platform: youtube/instagram/tiktok"),
    count: int = typer.Option(10, "--count", "-n", help="Number of titles to generate")
):
    """
    Generate viral-optimized titles and metadata

    Examples:
        sf youtube optimize "Python Tutorial"
        sf youtube optimize "Gaming Setup" --style review --count 20
        sf youtube optimize "Cooking" --platform instagram
    """
    optimizer = ViralOptimizer()

    # Generate titles
    console.print(f"\n[bold cyan]Generating viral titles for:[/bold cyan] {topic}\n")

    titles = optimizer.generate_titles(
        topic=topic,
        style=style,
        platform=platform,
        count=count
    )

    # Display titles
    table = Table(title=f"Top {count} Viral Titles")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="white")
    table.add_column("CTR", style="green", justify="right")
    table.add_column("Trigger", style="yellow")
    table.add_column("Length", style="cyan", justify="right")

    for i, title_data in enumerate(titles, 1):
        table.add_row(
            str(i),
            title_data["title"],
            title_data["ctr_prediction"],
            title_data["trigger"],
            str(title_data["length"])
        )

    console.print(table)

    # Show best title
    best_title = titles[0]
    console.print(f"\n[bold green]🏆 Best Title:[/bold green] {best_title['title']}")
    console.print(f"[dim]Predicted CTR: {best_title['ctr_prediction']}[/dim]\n")

    # Generate description
    description = optimizer.optimize_description(
        title=best_title["title"],
        topic=topic,
        platform=platform
    )

    console.print("[bold]Optimized Description:[/bold]")
    console.print(Panel(description[:500] + "...", title="Description Preview"))

    # Generate hooks
    hooks = optimizer.generate_hooks(topic)
    console.print("\n[bold]Video Hook Options:[/bold]")
    for i, hook in enumerate(hooks[:5], 1):
        console.print(f"  {i}. {hook}")

    return {
        "titles": titles,
        "description": description,
        "hooks": hooks
    }


@app.command()
def analyze(
    project_name: Optional[str] = typer.Option(None, "--project", "-p", help="Project name"),
    competitors: bool = typer.Option(False, "--competitors", "-c", help="Analyze competitors")
):
    """
    Analyze channel performance and competitors

    Examples:
        sf youtube analyze
        sf youtube analyze --competitors
    """
    service = YouTubeAPIService()

    # Get channel analytics
    console.print("\n[bold]Fetching channel analytics...[/bold]\n")

    analytics = service.get_channel_analytics()

    if not analytics["success"]:
        if "Authentication failed" in analytics.get("error", ""):
            console.print("[yellow]YouTube API not configured. Run 'sf youtube upload' to set up.[/yellow]")
        else:
            console.print(f"[red]Failed to fetch analytics: {analytics.get('error')}[/red]")
        raise typer.Exit(1)

    # Display channel stats
    stats = analytics["statistics"]

    table = Table(title=f"Channel: {analytics['channel_title']}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white", justify="right")
    table.add_row("Subscribers", f"{stats['subscribers']:,}")
    table.add_row("Total Views", f"{stats['total_views']:,}")
    table.add_row("Total Videos", str(stats['total_videos']))
    table.add_row("Avg Views/Video", f"{stats['total_views'] // max(stats['total_videos'], 1):,}")

    console.print(table)

    # Competitor analysis
    if competitors:
        state = StateManager()
        topic = project_name or state.current_project or "python tutorial"

        console.print(f"\n[bold]Analyzing competitors for:[/bold] {topic}\n")

        competitor_videos = service.search_competitors(topic, max_results=5)

        if competitor_videos:
            comp_table = Table(title="Top Competitor Videos")
            comp_table.add_column("Title", style="white")
            comp_table.add_column("Channel", style="cyan")
            comp_table.add_column("Published", style="dim")

            for video in competitor_videos:
                comp_table.add_row(
                    video["title"][:50] + "..." if len(video["title"]) > 50 else video["title"],
                    video["channel"],
                    video["published"][:10]
                )

            console.print(comp_table)

    return analytics


@app.command()
def titles(
    topic: str = typer.Argument(..., help="Video topic"),
    viral: bool = typer.Option(False, "--viral", "-v", help="Generate viral titles"),
    style: str = typer.Option("educational", "--style", "-s", help="Content style")
):
    """
    Quick title generation

    Examples:
        sf youtube titles "Python Tutorial"
        sf youtube titles "Gaming Setup" --viral
        sf youtube titles "Recipe" --style entertainment
    """
    if viral:
        # Use viral optimizer
        optimizer = ViralOptimizer()
        titles = optimizer.generate_titles(topic, style=style, count=5)

        console.print("\n[bold red]🔥 Viral Titles:[/bold red]")
        for i, title_data in enumerate(titles, 1):
            console.print(f"  {i}. {title_data['title']} [dim]({title_data['ctr_prediction']})[/dim]")
    else:
        # Simple title generation
        templates = [
            f"How to {topic} - Complete Guide",
            f"{topic} Tutorial for Beginners",
            f"Master {topic} in 2025",
            f"The Ultimate {topic} Guide",
            f"{topic}: Everything You Need to Know"
        ]

        console.print("\n[bold]Generated Titles:[/bold]")
        for i, title in enumerate(templates, 1):
            console.print(f"  {i}. {title}")

    return titles if viral else templates