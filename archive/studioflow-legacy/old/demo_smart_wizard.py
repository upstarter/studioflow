#!/usr/bin/env python3
"""
Demo of Smart Context Awareness and Dynamic Step Generation
"""

from wizardlib import create_wizard, WizardStep, InputType

def create_smart_project_wizard():
    """Demo wizard showcasing context awareness and dynamic steps"""

    # This wizard will:
    # 1. Learn from user choices and suggest them next time
    # 2. Detect project context from filesystem
    # 3. Generate platform-specific steps dynamically
    # 4. Provide contextual help based on current situation

    wizard = (
        create_wizard("🤖 Smart StudioFlow Project Creator")
        .description("AI-powered project creation with context awareness")

        # Basic project info
        .text_input("project_name", "Project name:",
                   help_text="Choose a descriptive name for your video project")

        # Platform choice - will trigger dynamic platform-specific steps
        .choice("platform", "Target platform:",
               options=["YouTube", "Instagram", "TikTok", "Multiple"],
               help_text="Different platforms require different optimization")

        # Project type - will trigger dynamic project-specific steps
        .choice("project_type", "Project type:",
               options=["tutorial", "livestream", "review", "vlog", "gaming"],
               help_text="Affects workflow and tool recommendations")

        # Tools needed - will trigger dynamic tool configuration steps
        .multi_choice("tools_needed", "Tools you'll use:",
                     options=["obs", "resolve", "youtube", "audio"],
                     help_text="We'll configure these tools automatically")

        .confirm("enable_optimization", "Enable AI optimization features?",
                default=True,
                help_text="Auto-generates titles, thumbnails, descriptions")

        .build()
    )

    return wizard

def demo_context_awareness():
    """Run demo showing context awareness features"""
    print("🤖 Smart Context Awareness Demo")
    print("=" * 50)
    print()
    print("This wizard demonstrates:")
    print("✓ Learning from your choices")
    print("✓ Suggesting intelligent defaults")
    print("✓ Detecting project context from filesystem")
    print("✓ Generating steps dynamically based on your answers")
    print("✓ Providing contextual help")
    print()
    print("Run this wizard multiple times to see it learn your preferences!")
    print()

    wizard = create_smart_project_wizard()
    result = wizard.run()

    if result:
        print("\n" + "=" * 50)
        print("🎉 Smart Wizard Complete!")
        print("=" * 50)

        # Show what the wizard learned
        print("\n📊 Context Awareness Results:")
        print(f"✓ Project created: {result.get('project_name', 'Unknown')}")
        print(f"✓ Platform chosen: {result.get('platform', 'Unknown')}")
        print(f"✓ Project type: {result.get('project_type', 'Unknown')}")

        # Check if platform-specific steps were generated
        if result.get('youtube_category'):
            print(f"✓ YouTube category: {result.get('youtube_category')}")
        if result.get('instagram_format'):
            print(f"✓ Instagram format: {result.get('instagram_format')}")
        if result.get('tiktok_style'):
            print(f"✓ TikTok style: {result.get('tiktok_style')}")

        # Check if project-specific steps were generated
        if result.get('tutorial_complexity'):
            print(f"✓ Tutorial complexity: {result.get('tutorial_complexity')}")
        if result.get('stream_duration'):
            print(f"✓ Stream duration: {result.get('stream_duration')}")

        print(f"\n💾 Preferences saved for next time!")
        print(f"📈 Next run will suggest your frequent choices as defaults")
        print(f"🧠 Context awareness will continue learning from your usage")

        return result
    else:
        print("\n❌ Wizard cancelled")
        return None

if __name__ == "__main__":
    demo_context_awareness()