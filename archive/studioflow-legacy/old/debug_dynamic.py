#!/usr/bin/env python3
"""Debug dynamic step generation"""

from wizardlib import create_wizard, WizardStep, InputType

def test_dynamic_steps():
    """Test that dynamic steps are being generated correctly"""
    print("🔍 Debug: Dynamic Step Generation")
    print("=" * 40)

    wizard = (
        create_wizard("Debug Wizard")
        .text_input("name", "Project name:")
        .choice("platform", "Platform:", ["YouTube", "Instagram", "TikTok"])
        .build()
    )

    print(f"Initial steps: {len(wizard.steps)}")
    for i, step in enumerate(wizard.steps):
        print(f"  {i+1}. {step.id}: {step.prompt}")

    # Manually test step generation
    from wizardlib import WizardContext, DynamicStepGenerator
    context = WizardContext()
    generator = DynamicStepGenerator(context)

    # Simulate YouTube choice
    print(f"\nSimulating YouTube platform choice...")
    youtube_steps = generator.generate_steps("debug wizard", {"platform": "YouTube"})
    print(f"Generated {len(youtube_steps)} additional steps:")
    for step in youtube_steps:
        print(f"  - {step.id}: {step.prompt}")

    print(f"\nRunning wizard to test integration...")
    # The wizard should automatically add YouTube-specific steps after platform choice

if __name__ == "__main__":
    test_dynamic_steps()