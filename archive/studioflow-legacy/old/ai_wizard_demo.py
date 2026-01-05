#!/usr/bin/env python3
"""
AI-Powered Wizard Demo - Phase 3 Features
Natural Language Processing, Smart Defaults, Error Prevention
"""

from wizardlib import create_wizard, WizardStep, InputType, AIWizardEnhancer

def create_ai_powered_wizard():
    """Create wizard with full AI capabilities"""

    from wizardlib import AIProcessor
    ai = AIProcessor()

    # Create NLP handler
    def nlp_handler(text: str) -> dict:
        return ai.parse_natural_language(text)

    # Create base wizard
    wizard = (
        create_wizard("🤖 AI-Powered StudioFlow Creator")
        .description("Next-generation wizard with natural language AI")

        # Natural Language Description Step
        .text_input("project_description",
                   "Describe your project in natural language:",
                   help_text="Tell me what you want to create in your own words",
                   parser="nlp",
                   nlp_handler=nlp_handler)  # This enables NLP processing

        # Project name with AI-generated smart default
        .text_input("project_name", "Project name:",
                   help_text="AI will suggest based on your description")

        # Platform choice with AI suggestions
        .choice("platform", "Target platform:",
               options=["YouTube", "Instagram", "TikTok", "Multiple"],
               help_text="AI will recommend based on your description")

        # Project type with AI suggestions
        .choice("project_type", "Project type:",
               options=["tutorial", "livestream", "review", "vlog", "gaming"],
               help_text="AI analyzes your goals to suggest the best type")

        # Build the wizard
        .build()
    )

    return wizard

def demo_ai_features():
    """Demonstrate AI-powered wizard features"""
    print("🤖 AI-Powered Wizard Demo - Phase 3 Features")
    print("=" * 60)
    print()
    print("This wizard demonstrates:")
    print("✓ Natural Language Processing - Describe what you want")
    print("✓ AI-Powered Smart Defaults - Intelligent suggestions")
    print("✓ Error Prevention - AI detects and fixes issues")
    print("✓ Intent Recognition - Understands your goals")
    print("✓ Viral Content Optimization - AI suggests viral elements")
    print()
    print("Example descriptions to try:")
    print('  "I want to create a beginner tutorial about Python for YouTube"')
    print('  "Make a short viral TikTok video about cooking"')
    print('  "Create a professional livestream for gaming content"')
    print()

    wizard = create_ai_powered_wizard()
    result = wizard.run()

    if result:
        print("\n" + "=" * 60)
        print("🎉 AI-Powered Wizard Complete!")
        print("=" * 60)

        # Show AI analysis results
        print("\n🧠 AI Analysis Results:")

        # Show what the AI understood from natural language
        if result.get("project_description"):
            print(f"✓ Original description: {result['project_description']}")

        # Show AI-generated suggestions
        if result.get("ai_suggested_platform"):
            print(f"✓ AI suggested platform: {result['ai_suggested_platform']}")
        if result.get("ai_suggested_project_type"):
            print(f"✓ AI suggested project type: {result['ai_suggested_project_type']}")
        if result.get("ai_suggested_complexity"):
            print(f"✓ AI suggested complexity: {result['ai_suggested_complexity']}")

        # Show viral content potential
        from wizardlib import AIProcessor
        ai = AIProcessor()
        viral_title = ai.generate_viral_title(result, result.get("project_description", ""))
        print(f"✓ AI-generated viral title: '{viral_title}'")

        print(f"\n🚀 Your AI-optimized project is ready!")
        print(f"📈 The AI has analyzed your needs and optimized for maximum impact")

        return result
    else:
        print("\n❌ Wizard cancelled")
        return None

def test_ai_components():
    """Test individual AI components"""
    print("\n🧪 Testing AI Components")
    print("=" * 30)

    from wizardlib import AIProcessor
    ai = AIProcessor()

    # Test NLP
    test_descriptions = [
        "I want to create a beginner tutorial about Python for YouTube",
        "Make a short viral TikTok video about cooking secrets",
        "Create a professional livestream for advanced gaming",
        "Build a review channel for tech products"
    ]

    for desc in test_descriptions:
        print(f"\nInput: '{desc}'")
        analysis = ai.parse_natural_language(desc)
        print(f"  Intents: {analysis['intents']}")
        print(f"  Platform: {analysis['suggested_platform']}")
        print(f"  Type: {analysis['suggested_project_type']}")
        print(f"  Complexity: {analysis['complexity_level']}")
        print(f"  Viral elements: {analysis['viral_elements']}")

    # Test viral title generation
    print(f"\n🎯 Viral Title Generation:")
    for desc in test_descriptions[:2]:
        viral_title = ai.generate_viral_title({"project_name": "Test"}, desc)
        print(f"  '{desc}' → '{viral_title}'")

    # Test error prediction
    print(f"\n⚠️ Error Prevention:")
    test_responses = {
        "platform": "TikTok",
        "video_length": "Long (10+ min)",
        "tutorial_complexity": "Advanced"
    }
    test_context = {"skill_level": "beginner"}
    warnings = ai.predict_errors(test_responses, test_context)
    for warning in warnings:
        print(f"  {warning['severity'].upper()}: {warning['message']}")

if __name__ == "__main__":
    demo_ai_features()
    test_ai_components()