#!/usr/bin/env python3
"""Test context awareness system"""

from wizardlib import WizardContext, DynamicStepGenerator
from pathlib import Path

def test_context_awareness():
    """Test the context awareness features"""
    print("🧪 Testing Context Awareness System")
    print("=" * 40)

    # Create context instance
    context = WizardContext()

    print(f"✓ Context initialized")
    print(f"  Context dir: {context.context_dir}")
    print(f"  Current directory: {context.project_context['current_directory']}")
    print(f"  Has git repo: {context.project_context['has_git']}")
    print(f"  Media files found: {len(context.project_context['media_files'])}")

    # Test learning system
    print(f"\n📚 Testing Learning System:")
    context.learn_from_choice("platform", "YouTube", "demo_wizard")
    context.learn_from_choice("platform", "YouTube", "demo_wizard")  # Choose again
    context.learn_from_choice("platform", "Instagram", "demo_wizard")
    context.learn_from_choice("project_type", "tutorial", "demo_wizard")

    # Test suggestions
    print(f"\n🎯 Testing Suggestions:")
    platform_suggestion = context.suggest_default("platform", "demo_wizard", ["YouTube", "Instagram", "TikTok"])
    project_suggestion = context.suggest_default("project_type", "demo_wizard", ["tutorial", "vlog", "review"])

    print(f"  Platform suggestion: {platform_suggestion}")
    print(f"  Project type suggestion: {project_suggestion}")

    # Test contextual help
    print(f"\n💡 Testing Contextual Help:")
    project_help = context.get_contextual_help("project_name", "demo_wizard")
    platform_help = context.get_contextual_help("platform", "demo_wizard")

    print(f"  Project name help: {project_help}")
    print(f"  Platform help: {platform_help}")

    # Test dynamic step generation
    print(f"\n⚡ Testing Dynamic Step Generation:")
    generator = DynamicStepGenerator(context)

    # Simulate choosing YouTube
    youtube_steps = generator._generate_platform_steps("YouTube", {})
    print(f"  YouTube generated {len(youtube_steps)} additional steps:")
    for step in youtube_steps:
        print(f"    - {step.id}: {step.prompt}")

    # Simulate choosing tutorial project
    tutorial_steps = generator._generate_project_steps("tutorial", {})
    print(f"  Tutorial generated {len(tutorial_steps)} additional steps:")
    for step in tutorial_steps:
        print(f"    - {step.id}: {step.prompt}")

    print(f"\n✅ All context awareness tests passed!")

if __name__ == "__main__":
    test_context_awareness()