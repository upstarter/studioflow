"""
Local LLM integration using Ollama for content generation
Optimized for YouTube titles, viral hooks, and marketing copy
"""

import json
import subprocess
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import requests
from rich.console import Console

console = Console()


class ModelType(Enum):
    """Ollama models optimized for different tasks"""
    VIRAL = "llama3.1:13b"      # Best for viral titles/hooks
    FAST = "mistral:7b"          # Quick iterations
    TECHNICAL = "qwen2.5:14b"    # Technical content
    TINY = "phi3:mini"           # Ultra-fast drafts


@dataclass
class ModelProfile:
    """Model configuration and prompting strategy"""
    name: str
    model_id: str
    temperature: float
    top_p: float
    system_prompt: str
    max_tokens: int = 500


class LocalLLMService:
    """Local LLM service using Ollama"""

    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.models = self._setup_models()
        self._ensure_ollama_running()

    def _setup_models(self) -> Dict[str, ModelProfile]:
        """Configure models with optimal prompts for content creation"""
        return {
            "viral": ModelProfile(
                name="Viral Content Generator",
                model_id=ModelType.VIRAL.value,
                temperature=0.9,
                top_p=0.95,
                system_prompt="""You are a viral content strategist who creates engaging YouTube titles and hooks.
Your titles trigger curiosity, use power words, and follow proven viral formulas.
Always create titles that:
- Are 50-60 characters (optimal for YouTube)
- Include numbers when possible
- Create curiosity gaps
- Use emotional triggers
- Avoid clickbait that doesn't deliver"""
            ),
            "fast": ModelProfile(
                name="Quick Ideas Generator",
                model_id=ModelType.FAST.value,
                temperature=0.7,
                top_p=0.9,
                system_prompt="""You are a creative marketer generating quick content ideas.
Be concise, punchy, and creative. Focus on variety and speed."""
            ),
            "technical": ModelProfile(
                name="Technical Content Writer",
                model_id=ModelType.TECHNICAL.value,
                temperature=0.3,
                top_p=0.9,
                system_prompt="""You are a technical content creator for developers and creators.
Be accurate, detailed, and include specific examples. Focus on educational value."""
            ),
            "description": ModelProfile(
                name="Description Writer",
                model_id=ModelType.FAST.value,
                temperature=0.5,
                top_p=0.9,
                system_prompt="""You write engaging YouTube descriptions optimized for SEO.
Include timestamps, key points, and calls-to-action. Use relevant keywords naturally.""",
                max_tokens=1000
            )
        }

    def _ensure_ollama_running(self):
        """Check if Ollama is running, start if not"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                console.print("[green]✓ Ollama is running[/green]")
                return True
        except:
            console.print("[yellow]Starting Ollama service...[/yellow]")
            subprocess.run(["ollama", "serve"], capture_output=True, background=True)
            return True

    def _call_ollama(self, model: str, prompt: str, system: str = "",
                     temperature: float = 0.7, max_tokens: int = 500) -> str:
        """Make API call to Ollama"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                }
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                console.print(f"[red]Ollama error: {response.status_code}[/red]")
                return ""
        except Exception as e:
            console.print(f"[red]Failed to call Ollama: {e}[/red]")
            return ""

    def generate_titles(self, topic: str, style: str = "viral", count: int = 10) -> List[Dict[str, Any]]:
        """
        Generate YouTube titles optimized for CTR

        Args:
            topic: Video topic/keywords
            style: Generation style (viral, educational, entertainment)
            count: Number of titles to generate
        """
        profile = self.models.get(style, self.models["viral"])

        # Proven title formulas
        formulas = [
            f"Generate a title using 'How to' format for: {topic}",
            f"Create a title with a number (like '5 ways') for: {topic}",
            f"Make a controversial/surprising title about: {topic}",
            f"Create a 'mistakes to avoid' title for: {topic}",
            f"Generate a 'secret/hidden' revelation title about: {topic}",
            f"Create a comparison title (X vs Y) for: {topic}",
            f"Make a 'Complete Guide' title for: {topic}",
            f"Create a question-based title about: {topic}",
            f"Generate a 'Why' explanation title for: {topic}",
            f"Create a results/transformation title for: {topic}"
        ]

        titles = []
        console.print(f"[cyan]Generating {count} titles with {profile.name}...[/cyan]")

        for i, formula in enumerate(formulas[:count]):
            prompt = f"{formula}\n\nRequirements:\n- 50-60 characters\n- Use power words\n- Create curiosity\n- Be specific, not vague"

            response = self._call_ollama(
                model=profile.model_id,
                prompt=prompt,
                system=profile.system_prompt,
                temperature=profile.temperature,
                max_tokens=100
            )

            if response:
                # Clean up the response
                title = response.strip().replace('"', '').replace('\n', ' ')

                # Estimate CTR based on formula type
                ctr_estimates = {
                    0: "12-15%",  # How-to
                    1: "10-13%",  # Numbered
                    2: "15-18%",  # Controversial
                    3: "11-14%",  # Mistakes
                    4: "13-16%",  # Secrets
                    5: "9-12%",   # Comparison
                    6: "8-11%",   # Guide
                    7: "10-13%",  # Question
                    8: "9-12%",   # Why
                    9: "11-14%"   # Results
                }

                titles.append({
                    "title": title[:60],  # Ensure length limit
                    "formula": formula.split(' ')[2],  # Extract formula type
                    "ctr_estimate": ctr_estimates.get(i, "10-12%"),
                    "length": len(title)
                })

        return titles

    def generate_hooks(self, topic: str, style: str = "viral", count: int = 5) -> List[str]:
        """Generate viral hooks for video intros"""
        profile = self.models.get(style, self.models["viral"])

        prompt = f"""Generate {count} different viral hooks for a video about: {topic}

Each hook should:
- Be 5-10 seconds when spoken
- Create immediate curiosity
- Promise value
- Use pattern interrupts

Format each as a separate paragraph."""

        response = self._call_ollama(
            model=profile.model_id,
            prompt=prompt,
            system=profile.system_prompt,
            temperature=0.9,
            max_tokens=500
        )

        if response:
            hooks = [h.strip() for h in response.split('\n\n') if h.strip()]
            return hooks[:count]
        return []

    def generate_description(self, title: str, topic: str, duration: int = 600) -> str:
        """Generate SEO-optimized YouTube description"""
        profile = self.models["description"]

        # Calculate timestamp sections
        sections = duration // 120  # Section every 2 minutes

        prompt = f"""Create a YouTube description for:
Title: {title}
Topic: {topic}
Duration: {duration // 60} minutes

Include:
1. Hook paragraph (2-3 sentences)
2. Timestamps (create {sections} logical sections)
3. Key takeaways (3-5 bullet points)
4. Relevant hashtags (5-7)
5. Call to action

Make it SEO-friendly with natural keyword usage."""

        response = self._call_ollama(
            model=profile.model_id,
            prompt=prompt,
            system=profile.system_prompt,
            temperature=0.5,
            max_tokens=1000
        )

        return response if response else ""

    def generate_tags(self, title: str, topic: str, count: int = 20) -> List[str]:
        """Generate YouTube tags for SEO"""
        profile = self.models["fast"]

        prompt = f"""Generate {count} YouTube tags for:
Title: {title}
Topic: {topic}

Include:
- Primary keywords (exact match)
- Long-tail keywords
- Related topics
- Common misspellings
- Trending variations

Output as comma-separated list."""

        response = self._call_ollama(
            model=profile.model_id,
            prompt=prompt,
            system="You are an SEO expert specializing in YouTube optimization.",
            temperature=0.3,
            max_tokens=200
        )

        if response:
            tags = [tag.strip() for tag in response.split(',')]
            return tags[:count]
        return []

    def check_models(self) -> Dict[str, bool]:
        """Check which models are installed"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )

            installed = result.stdout
            status = {}

            for model_type in ModelType:
                status[model_type.value] = model_type.value in installed

            return status
        except:
            return {m.value: False for m in ModelType}

    def install_model(self, model_type: ModelType):
        """Install a specific model"""
        console.print(f"[cyan]Installing {model_type.value}...[/cyan]")

        try:
            subprocess.run(
                ["ollama", "pull", model_type.value],
                check=True
            )
            console.print(f"[green]✓ Installed {model_type.value}[/green]")
            return True
        except subprocess.CalledProcessError:
            console.print(f"[red]Failed to install {model_type.value}[/red]")
            return False


def setup_ollama():
    """One-time setup to install optimal models"""
    console.print("[bold cyan]Setting up Ollama for StudioFlow[/bold cyan]\n")

    service = LocalLLMService()
    status = service.check_models()

    # Recommend models based on available VRAM
    console.print("Checking installed models...")

    for model, installed in status.items():
        if installed:
            console.print(f"[green]✓[/green] {model}")
        else:
            console.print(f"[yellow]○[/yellow] {model} (not installed)")

    # Install missing recommended models
    recommended = [ModelType.VIRAL, ModelType.FAST]

    for model_type in recommended:
        if not status.get(model_type.value, False):
            if console.input(f"\nInstall {model_type.value} for content generation? [y/N]: ").lower() == 'y':
                service.install_model(model_type)

    console.print("\n[green]Setup complete! You can now use local LLMs for content generation.[/green]")


if __name__ == "__main__":
    # Demo the service
    service = LocalLLMService()

    # Check what's installed
    models = service.check_models()
    console.print("\n[bold]Installed Models:[/bold]")
    for model, installed in models.items():
        status = "[green]✓[/green]" if installed else "[red]✗[/red]"
        console.print(f"{status} {model}")

    # Generate sample titles
    console.print("\n[bold]Sample Title Generation:[/bold]")
    titles = service.generate_titles("Python automation tutorial", count=3)
    for i, title_data in enumerate(titles, 1):
        console.print(f"{i}. {title_data['title']}")
        console.print(f"   CTR: {title_data['ctr_estimate']} | Formula: {title_data['formula']}")