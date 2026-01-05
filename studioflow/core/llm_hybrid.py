"""
Hybrid LLM Service - Smart routing between Claude API and Ollama
Uses Claude for quality-critical tasks, Ollama for bulk/speed tasks
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import os
from anthropic import Anthropic
from rich.console import Console

from studioflow.core.llm_local import LocalLLMService

console = Console()


class TaskPriority(Enum):
    """Determine which LLM to use based on task"""
    QUALITY_CRITICAL = "claude"     # Final titles, important content
    BULK_GENERATION = "ollama"       # Many variations, brainstorming
    SPEED_CRITICAL = "ollama"        # Real-time suggestions
    COMPLEX_REASONING = "claude"     # Strategy, analysis
    SIMPLE_TASKS = "ollama"         # Tags, basic descriptions


class HybridLLMService:
    """
    Intelligently routes between Claude API and Ollama

    Strategy:
    - Claude: Quality-critical, complex reasoning, final versions
    - Ollama: Bulk generation, brainstorming, drafts, offline work
    """

    def __init__(self, claude_api_key: Optional[str] = None):
        # Initialize both services
        self.local_llm = LocalLLMService()

        # Claude API (optional)
        self.claude_available = False
        if claude_api_key or os.getenv("ANTHROPIC_API_KEY"):
            try:
                self.claude = Anthropic(api_key=claude_api_key or os.getenv("ANTHROPIC_API_KEY"))
                self.claude_available = True
                console.print("[green]✓ Claude API connected[/green]")
            except:
                console.print("[yellow]⚠ Claude API not available, using Ollama only[/yellow]")

    def generate_titles(self,
                       topic: str,
                       quality: str = "draft",
                       count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate titles with smart routing

        Args:
            quality: "draft" (Ollama), "final" (Claude), "hybrid" (both)
        """

        if quality == "final" and self.claude_available:
            # Use Claude for final quality
            return self._claude_titles(topic, count)

        elif quality == "hybrid" and self.claude_available:
            # Generate many with Ollama, refine best with Claude
            console.print("[cyan]Stage 1: Generating drafts with Ollama...[/cyan]")
            drafts = self.local_llm.generate_titles(topic, count=count * 2)

            # Pick top 5 based on CTR estimates
            top_drafts = sorted(drafts,
                              key=lambda x: float(x['ctr_estimate'].split('-')[0]),
                              reverse=True)[:5]

            console.print(f"[cyan]Stage 2: Refining top {len(top_drafts)} with Claude...[/cyan]")
            refined = []
            for draft in top_drafts:
                improved = self._claude_improve_title(draft['title'], topic)
                refined.append({
                    'title': improved,
                    'ctr_estimate': "15-20%",  # Claude refined = higher CTR
                    'quality': 'claude-refined'
                })

            # Combine refined + best drafts
            return refined + drafts[:count-len(refined)]

        else:
            # Use Ollama (draft quality or Claude not available)
            return self.local_llm.generate_titles(topic, count=count)

    def _claude_titles(self, topic: str, count: int = 10) -> List[Dict[str, Any]]:
        """Generate high-quality titles with Claude"""
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.8,
                system="""You are a YouTube title optimization expert. Create titles that:
- Maximize CTR (12-20% target)
- Are 50-60 characters
- Use psychological triggers
- Follow platform best practices
- Avoid clickbait that disappoints""",
                messages=[{
                    "role": "user",
                    "content": f"""Generate {count} viral YouTube titles for: {topic}

For each title provide:
1. The title (50-60 chars)
2. CTR estimate (realistic percentage)
3. Psychological trigger used

Format as numbered list."""
                }]
            )

            # Parse Claude's response
            titles = []
            lines = response.content[0].text.strip().split('\n')

            for line in lines:
                if line and any(char.isdigit() for char in line[:3]):
                    # Extract title from numbered list
                    title_text = line.split('.', 1)[1].strip() if '.' in line else line
                    titles.append({
                        'title': title_text[:60],
                        'ctr_estimate': "14-18%",  # Claude quality
                        'quality': 'claude',
                        'model': 'claude-3.5-sonnet'
                    })

            return titles[:count]

        except Exception as e:
            console.print(f"[red]Claude API error: {e}[/red]")
            console.print("[yellow]Falling back to Ollama...[/yellow]")
            return self.local_llm.generate_titles(topic, count=count)

    def _claude_improve_title(self, draft_title: str, topic: str) -> str:
        """Use Claude to improve an Ollama-generated title"""
        try:
            response = self.claude.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=100,
                temperature=0.5,
                messages=[{
                    "role": "user",
                    "content": f"""Improve this YouTube title for maximum CTR:

Draft: {draft_title}
Topic: {topic}

Make it more compelling while keeping it under 60 characters.
Return only the improved title, nothing else."""
                }]
            )

            return response.content[0].text.strip()[:60]

        except:
            return draft_title  # Return original if API fails

    def batch_generate(self,
                       topics: List[str],
                       titles_per_topic: int = 5) -> Dict[str, List[Dict]]:
        """
        Bulk generation - always uses Ollama for speed

        This is where Ollama shines - no rate limits!
        """
        results = {}

        console.print(f"[cyan]Batch generating for {len(topics)} topics...[/cyan]")

        with console.status("Generating...") as status:
            for topic in topics:
                status.update(f"Processing: {topic}")
                # Always use Ollama for batch - no rate limits
                results[topic] = self.local_llm.generate_titles(
                    topic,
                    count=titles_per_topic
                )

        console.print(f"[green]✓ Generated {len(topics) * titles_per_topic} titles[/green]")
        return results

    def analyze_competitor(self, competitor_title: str) -> Dict[str, Any]:
        """
        Complex analysis task - prefer Claude if available
        """
        if self.claude_available:
            try:
                response = self.claude.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=500,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": f"""Analyze this YouTube title: "{competitor_title}"

Provide:
1. Estimated CTR range
2. Psychological triggers used
3. Target audience
4. Why it works (or doesn't)
5. How to improve it

Be specific and analytical."""
                    }]
                )

                return {
                    'analysis': response.content[0].text,
                    'model': 'claude-3.5-sonnet'
                }

            except Exception as e:
                console.print(f"[yellow]Claude unavailable, using Ollama[/yellow]")

        # Fallback to Ollama
        return self._ollama_analyze(competitor_title)

    def _ollama_analyze(self, title: str) -> Dict[str, Any]:
        """Fallback analysis with Ollama"""
        # Use the technical model for analysis
        response = self.local_llm._call_ollama(
            model="qwen2.5:14b",  # Better for analysis
            prompt=f"Analyze this YouTube title for effectiveness: '{title}'",
            system="You are a YouTube analytics expert.",
            temperature=0.3
        )

        return {
            'analysis': response,
            'model': 'qwen2.5:14b'
        }

    def recommend_approach(self, task: str) -> str:
        """Recommend whether to use Claude or Ollama for a task"""

        recommendations = {
            # Use Claude for:
            "final_title": "Use Claude - Maximum quality for published content",
            "thumbnail_text": "Use Claude - Need perfect copy",
            "strategy": "Use Claude - Complex reasoning required",
            "script_outline": "Use Claude - Needs structure and depth",

            # Use Ollama for:
            "brainstorming": "Use Ollama - Generate many ideas quickly",
            "variations": "Use Ollama - No rate limits for bulk generation",
            "tags": "Use Ollama - Simple task, speed matters",
            "drafts": "Use Ollama - Initial versions, will refine later",
            "testing": "Use Ollama - Rapid iteration needed",

            # Hybrid approach:
            "video_package": "Use Hybrid - Ollama for drafts, Claude for finals",
            "content_calendar": "Use Hybrid - Ollama for ideas, Claude for best ones"
        }

        return recommendations.get(task, "Use Ollama for speed, Claude for quality")


def compare_outputs():
    """Demo comparing Claude vs Ollama outputs"""

    console.print("[bold cyan]Claude vs Ollama Comparison Demo[/bold cyan]\n")

    service = HybridLLMService()
    topic = "Python automation tutorial"

    # Generate with both
    console.print(f"Topic: {topic}\n")

    console.print("[bold]Ollama Generation:[/bold]")
    ollama_titles = service.generate_titles(topic, quality="draft", count=3)
    for i, t in enumerate(ollama_titles, 1):
        console.print(f"{i}. {t['title']}")

    if service.claude_available:
        console.print("\n[bold]Claude Generation:[/bold]")
        claude_titles = service.generate_titles(topic, quality="final", count=3)
        for i, t in enumerate(claude_titles, 1):
            console.print(f"{i}. {t['title']}")

        console.print("\n[bold]Hybrid Approach:[/bold]")
        hybrid_titles = service.generate_titles(topic, quality="hybrid", count=3)
        for i, t in enumerate(hybrid_titles, 1):
            console.print(f"{i}. {t['title']} [{t.get('quality', 'draft')}]")

    # Show recommendations
    console.print("\n[bold]Task Recommendations:[/bold]")
    tasks = ["final_title", "brainstorming", "variations", "video_package"]
    for task in tasks:
        rec = service.recommend_approach(task)
        console.print(f"• {task}: {rec}")


if __name__ == "__main__":
    compare_outputs()