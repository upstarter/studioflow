#!/usr/bin/env python3
"""
StudioFlow AI Provider - Simple, universal AI integration
Works with ANY AI through stdin/stdout or API calls
"""

import sys
import json
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    def generate(self, prompt: str, context: Dict = None) -> str:
        """Generate response from AI"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available"""
        pass

class StdinProvider(AIProvider):
    """Universal provider that uses stdin/stdout - works with any CLI tool"""

    def __init__(self, command: list = None):
        """
        Initialize with custom command
        Examples:
            - ['claude']  # Claude CLI
            - ['openai', 'api', 'chat.completions.create']  # OpenAI CLI
            - ['ollama', 'run', 'llama2']  # Ollama local
            - ['cat']  # For testing - just echoes
        """
        self.command = command or self._detect_available()

    def _detect_available(self) -> list:
        """Auto-detect available AI CLI tools"""
        tools = [
            (['claude'], 'Claude'),
            (['openai'], 'OpenAI'),
            (['ollama', 'run', 'llama2'], 'Ollama'),
            (['gpt'], 'GPT CLI'),
        ]

        for cmd, name in tools:
            try:
                subprocess.run([cmd[0], '--version'],
                             capture_output=True, check=False, timeout=1)
                print(f"✓ Found {name} CLI")
                return cmd
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue

        # Fallback to manual input
        return None

    def generate(self, prompt: str, context: Dict = None) -> str:
        """Send prompt to AI via stdin and get response"""

        if not self.command:
            # No AI CLI found - return template
            return self._template_response(prompt)

        # Build full prompt with context
        full_prompt = self._build_prompt(prompt, context)

        try:
            # Run AI command with prompt
            result = subprocess.run(
                self.command,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return self._template_response(prompt)

        except (subprocess.TimeoutExpired, Exception) as e:
            print(f"⚠️ AI provider error: {e}")
            return self._template_response(prompt)

    def _build_prompt(self, prompt: str, context: Dict = None) -> str:
        """Build structured prompt with context"""

        parts = []

        if context:
            if 'project' in context:
                parts.append(f"Project: {context['project']}")
            if 'style' in context:
                parts.append(f"Style: {context['style']}")
            if 'duration' in context:
                parts.append(f"Target Duration: {context['duration']} minutes")
            if 'platform' in context:
                parts.append(f"Platform: {context['platform']}")

        if parts:
            parts.append("")  # Empty line

        parts.append(prompt)

        return "\n".join(parts)

    def _template_response(self, prompt: str) -> str:
        """Fallback template when no AI available"""
        return f"""[AI Generated Content Placeholder]

Your request: {prompt}

To enable AI generation:
1. Install an AI CLI tool:
   - Claude: pip install anthropic-claude-cli
   - OpenAI: pip install openai-cli
   - Ollama: https://ollama.ai

2. Or pipe to your preferred AI:
   sf-ai script "topic" | claude
   sf-ai script "topic" | gpt-4

Template content follows...
"""

    def is_available(self) -> bool:
        """Check if provider is available"""
        return self.command is not None

class APIProvider(AIProvider):
    """Direct API integration (optional)"""

    def __init__(self, api_key: str = None, endpoint: str = None):
        self.api_key = api_key or self._load_from_env()
        self.endpoint = endpoint

    def _load_from_env(self) -> Optional[str]:
        """Load API key from environment or config"""
        import os

        # Try common environment variables
        for var in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'AI_API_KEY']:
            if var in os.environ:
                return os.environ[var]

        # Try config file
        config_file = Path.home() / '.studioflow' / 'ai_config.json'
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
                return config.get('api_key')

        return None

    def generate(self, prompt: str, context: Dict = None) -> str:
        """Generate via API call"""

        if not self.api_key:
            return StdinProvider().generate(prompt, context)

        # This is where you'd implement actual API calls
        # For now, falls back to stdin provider
        return StdinProvider().generate(prompt, context)

    def is_available(self) -> bool:
        return self.api_key is not None

class SmartAI:
    """Smart AI that auto-selects best available provider"""

    def __init__(self):
        self.provider = self._select_provider()

    def _select_provider(self) -> AIProvider:
        """Select best available provider"""

        # Try API first (if configured)
        api = APIProvider()
        if api.is_available():
            print("🤖 Using API provider")
            return api

        # Try stdin provider
        stdin = StdinProvider()
        if stdin.is_available():
            print("🤖 Using CLI provider")
            return stdin

        # Fallback to template provider
        print("📝 Using template provider (no AI configured)")
        return StdinProvider([])  # Empty command = templates only

    def generate_script(self, topic: str, style: str = "educational",
                       duration: int = 10, platform: str = "youtube") -> str:
        """Generate a video script"""

        prompt = f"""Generate a {style} video script about: {topic}

Requirements:
- Opening hook (first 15 seconds must grab attention)
- Clear structure with timestamps
- Target duration: {duration} minutes
- Platform: {platform}
- Include B-roll suggestions
- Add engagement elements (questions, CTAs)
- Speaking pace: 150 words/minute

Format as markdown with clear sections."""

        context = {
            'project': topic,
            'style': style,
            'duration': duration,
            'platform': platform
        }

        return self.provider.generate(prompt, context)

    def generate_titles(self, topic: str, count: int = 10) -> str:
        """Generate viral video titles"""

        prompt = f"""Generate {count} viral YouTube titles for a video about: {topic}

Requirements:
- Maximum 60 characters
- Use psychological triggers (curiosity, urgency, value)
- Mix different styles (question, list, how-to, shocking)
- Include numbers where appropriate
- Avoid clickbait that doesn't deliver

Format: One title per line, best first."""

        return self.provider.generate(prompt, {'project': topic})

    def generate_description(self, topic: str, script: str = None) -> str:
        """Generate YouTube description"""

        prompt = f"""Generate a YouTube description for a video about: {topic}

Include:
- Compelling summary (2-3 sentences)
- Timestamps (if script provided)
- Relevant links section
- Social media links
- SEO keywords naturally integrated
- Call to action
- Hashtags (3-5 relevant ones)

Keep under 5000 characters."""

        context = {'project': topic}
        if script:
            context['script'] = script[:500]  # Include script preview

        return self.provider.generate(prompt, context)

    def analyze_transcript(self, transcript: str) -> str:
        """Analyze transcript for improvements"""

        prompt = f"""Analyze this video transcript and suggest improvements:

{transcript[:1000]}...

Provide:
1. Pacing analysis (too fast/slow?)
2. Engagement opportunities missed
3. Clarity improvements
4. Suggested B-roll moments
5. Better hooks or CTAs

Be specific and actionable."""

        return self.provider.generate(prompt)

# Global AI instance
ai = SmartAI()

if __name__ == "__main__":
    # Test the AI provider
    print("Testing AI Provider...")
    print("=" * 60)

    response = ai.generate_script("Python Tips", style="tutorial", duration=5)
    print(response)