"""
Token management for LLM providers
Handles counting, limiting, and tracking token usage
"""

import tiktoken
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path


@dataclass
class TokenBudget:
    """Token limits and usage tracking"""
    daily_limit: int = 100000
    monthly_limit: int = 2000000
    per_request_max: int = 4000

    # Current usage
    daily_used: int = 0
    monthly_used: int = 0
    last_reset_daily: datetime = None
    last_reset_monthly: datetime = None


class TokenManager:
    """
    Manages token counting, limits, and optimization across providers
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path.home() / ".studioflow" / "token_usage.json"
        self.encoders = {}
        self.budgets = self._load_budgets()

        # Initialize encoders for different models
        self._setup_encoders()

    def _setup_encoders(self):
        """Setup tokenizers for accurate counting"""
        # Claude and GPT use cl100k_base
        self.encoders['claude'] = tiktoken.get_encoding("cl100k_base")
        self.encoders['gpt4'] = tiktoken.get_encoding("cl100k_base")

        # Llama models use different tokenizer, approximate with GPT
        # (In production, use proper Llama tokenizer)
        self.encoders['llama'] = tiktoken.get_encoding("cl100k_base")
        self.encoders['mistral'] = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str, model: str = "claude") -> int:
        """
        Accurately count tokens for a given model

        Args:
            text: Input text
            model: Model name for tokenizer selection
        """
        # Get appropriate encoder
        if "claude" in model.lower():
            encoder = self.encoders['claude']
        elif "gpt" in model.lower():
            encoder = self.encoders['gpt4']
        elif "llama" in model.lower():
            encoder = self.encoders['llama']
        else:
            # Default fallback
            encoder = self.encoders['claude']

        return len(encoder.encode(text))

    def estimate_cost(self, input_tokens: int, output_tokens: int,
                     provider: str = "claude") -> float:
        """Calculate estimated cost in dollars"""

        costs = {
            "claude": {
                "input": 0.003,   # $3 per million
                "output": 0.015   # $15 per million
            },
            "gpt4": {
                "input": 0.01,    # $10 per million
                "output": 0.03    # $30 per million
            },
            "gpt3.5": {
                "input": 0.0005,  # $0.50 per million
                "output": 0.0015  # $1.50 per million
            },
            "ollama": {
                "input": 0,       # Free!
                "output": 0
            }
        }

        provider_costs = costs.get(provider, costs["claude"])

        input_cost = (input_tokens / 1_000_000) * provider_costs["input"]
        output_cost = (output_tokens / 1_000_000) * provider_costs["output"]

        return input_cost + output_cost

    def truncate_to_limit(self, text: str, max_tokens: int,
                         model: str = "claude",
                         preserve_end: bool = False) -> str:
        """
        Truncate text to fit within token limit

        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            model: Model for tokenizer
            preserve_end: If True, keeps end of text instead of beginning
        """
        encoder = self.encoders.get(model, self.encoders['claude'])
        tokens = encoder.encode(text)

        if len(tokens) <= max_tokens:
            return text

        if preserve_end:
            # Keep the last max_tokens
            truncated_tokens = tokens[-max_tokens:]
        else:
            # Keep the first max_tokens
            truncated_tokens = tokens[:max_tokens]

        return encoder.decode(truncated_tokens)

    def optimize_prompt(self, prompt: str, context: str,
                       max_total: int = 3000) -> Tuple[str, str]:
        """
        Optimize prompt and context to fit within token budget

        Strategy:
        1. Reserve tokens for prompt (priority)
        2. Use remaining for context
        3. Truncate context if needed
        """
        prompt_tokens = self.count_tokens(prompt)
        context_tokens = self.count_tokens(context)

        # Reserve at least 500 tokens for output
        available = max_total - 500

        if prompt_tokens > available * 0.3:
            # Prompt is too long, truncate it
            prompt = self.truncate_to_limit(prompt, int(available * 0.3))
            prompt_tokens = self.count_tokens(prompt)

        # Use remaining tokens for context
        context_budget = available - prompt_tokens

        if context_tokens > context_budget:
            context = self.truncate_to_limit(context, context_budget)

        return prompt, context

    def check_budget(self, estimated_tokens: int,
                    provider: str = "claude") -> Tuple[bool, str]:
        """
        Check if request fits within budget

        Returns:
            (can_proceed, reason)
        """
        budget = self.budgets.get(provider, TokenBudget())

        # Reset daily counter if needed
        if not budget.last_reset_daily or \
           datetime.now() - budget.last_reset_daily > timedelta(days=1):
            budget.daily_used = 0
            budget.last_reset_daily = datetime.now()

        # Reset monthly counter if needed
        if not budget.last_reset_monthly or \
           datetime.now() - budget.last_reset_monthly > timedelta(days=30):
            budget.monthly_used = 0
            budget.last_reset_monthly = datetime.now()

        # Check limits
        if budget.daily_used + estimated_tokens > budget.daily_limit:
            return False, f"Would exceed daily limit ({budget.daily_limit})"

        if budget.monthly_used + estimated_tokens > budget.monthly_limit:
            return False, f"Would exceed monthly limit ({budget.monthly_limit})"

        if estimated_tokens > budget.per_request_max:
            return False, f"Request too large ({estimated_tokens} > {budget.per_request_max})"

        return True, "OK"

    def track_usage(self, input_tokens: int, output_tokens: int,
                   provider: str, cost: float):
        """Record actual token usage"""
        budget = self.budgets.get(provider, TokenBudget())

        total = input_tokens + output_tokens
        budget.daily_used += total
        budget.monthly_used += total

        # Save to file
        self._save_usage({
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost
        })

    def get_usage_stats(self) -> Dict:
        """Get current usage statistics"""
        stats = {}

        for provider, budget in self.budgets.items():
            stats[provider] = {
                "daily_used": budget.daily_used,
                "daily_limit": budget.daily_limit,
                "daily_remaining": budget.daily_limit - budget.daily_used,
                "monthly_used": budget.monthly_used,
                "monthly_limit": budget.monthly_limit,
                "monthly_remaining": budget.monthly_limit - budget.monthly_used,
                "daily_cost": self.estimate_cost(
                    budget.daily_used // 2,
                    budget.daily_used // 2,
                    provider
                )
            }

        return stats

    def _load_budgets(self) -> Dict[str, TokenBudget]:
        """Load budget configuration"""
        # Default budgets
        return {
            "claude": TokenBudget(
                daily_limit=50000,      # ~$0.75/day
                monthly_limit=1000000,  # ~$15/month
                per_request_max=4000
            ),
            "gpt4": TokenBudget(
                daily_limit=30000,
                monthly_limit=600000,
                per_request_max=4000
            ),
            "ollama": TokenBudget(
                daily_limit=999999999,  # Unlimited!
                monthly_limit=999999999,
                per_request_max=8192
            )
        }

    def _save_usage(self, record: Dict):
        """Append usage record to log file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        log_file = self.config_path.parent / "token_log.jsonl"

        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')


class SmartTokenRouter:
    """
    Routes requests to minimize token usage and cost
    """

    def __init__(self):
        self.token_manager = TokenManager()

    def route_request(self, task: str, content: str) -> Dict:
        """
        Determine optimal routing for a task

        Returns routing decision with provider and strategy
        """
        # Count tokens
        token_count = self.token_manager.count_tokens(content)

        # Define routing rules
        routing_rules = {
            # High quality required, use Claude
            "final_title": {
                "if_tokens_under": 500,
                "use": "claude",
                "else": "llama_then_claude"  # Generate with Llama, refine with Claude
            },

            # Bulk operations, use Ollama
            "batch_titles": {
                "if_tokens_under": 99999,  # Always
                "use": "ollama",
                "else": "ollama"
            },

            # Simple tasks, use fastest
            "tags": {
                "if_tokens_under": 99999,
                "use": "phi3",
                "else": "mistral"
            },

            # Complex reasoning, need Claude
            "strategy": {
                "if_tokens_under": 2000,
                "use": "claude",
                "else": "claude_chunked"  # Split into chunks
            }
        }

        # Get rule for task
        rule = routing_rules.get(task, {
            "if_tokens_under": 1000,
            "use": "ollama",
            "else": "claude"
        })

        # Apply routing logic
        if token_count < rule["if_tokens_under"]:
            provider = rule["use"]
        else:
            provider = rule["else"]

        # Check budget
        can_proceed, reason = self.token_manager.check_budget(
            token_count,
            provider.split('_')[0]  # Extract base provider
        )

        if not can_proceed and "claude" in provider:
            # Fallback to Ollama if Claude budget exceeded
            provider = "ollama"
            can_proceed = True
            reason = "Fell back to Ollama due to budget"

        return {
            "provider": provider,
            "token_count": token_count,
            "estimated_cost": self.token_manager.estimate_cost(
                token_count,
                500,  # Assume 500 output tokens
                provider.split('_')[0]
            ),
            "can_proceed": can_proceed,
            "reason": reason,
            "strategy": self._get_strategy(provider)
        }

    def _get_strategy(self, provider: str) -> str:
        """Get execution strategy for provider decision"""
        strategies = {
            "claude": "direct",
            "ollama": "direct",
            "llama_then_claude": "generate_many_refine_few",
            "claude_chunked": "split_and_combine",
            "phi3": "direct_simple"
        }

        return strategies.get(provider, "direct")


# Demo usage
if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Initialize managers
    token_mgr = TokenManager()
    router = SmartTokenRouter()

    # Test token counting
    test_prompt = "Generate 10 viral YouTube titles about Python automation"
    tokens = token_mgr.count_tokens(test_prompt)
    console.print(f"Token count: {tokens}")

    # Test routing decisions
    tasks = [
        ("final_title", "Create the perfect YouTube title about Python"),
        ("batch_titles", "Generate 100 titles for different topics"),
        ("tags", "Generate 20 tags for SEO"),
        ("strategy", "Analyze my channel and create a 3-month content strategy with detailed plans")
    ]

    table = Table(title="Routing Decisions")
    table.add_column("Task")
    table.add_column("Tokens")
    table.add_column("Provider")
    table.add_column("Strategy")
    table.add_column("Cost")

    for task_name, task_content in tasks:
        decision = router.route_request(task_name, task_content)
        table.add_row(
            task_name,
            str(decision["token_count"]),
            decision["provider"],
            decision["strategy"],
            f"${decision['estimated_cost']:.4f}"
        )

    console.print(table)

    # Show usage stats
    stats = token_mgr.get_usage_stats()
    console.print("\n[bold]Token Usage Stats:[/bold]")
    for provider, data in stats.items():
        console.print(f"{provider}: {data['daily_used']}/{data['daily_limit']} daily")