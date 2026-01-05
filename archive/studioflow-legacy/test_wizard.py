#!/usr/bin/env python3
"""Test the enhanced wizard features"""

from wizardlib import create_wizard

def test_enhanced_features():
    """Test navigation and validation features"""
    wizard = (
        create_wizard("🧪 Test Enhanced Features")
        .description("Test wizard with new navigation and validation")
        .text_input("name", "What's your name?", default="Test User")
        .text_input("email", "Your email address?", validation="email")
        .choice("platform", "Choose platform:", ["YouTube", "Instagram", "TikTok"])
        .confirm("proceed", "Continue with the test?")
        .build()
    )

    result = wizard.run()
    if result:
        print("\n✅ Test completed successfully!")
        print("Results:", result)
    else:
        print("\n❌ Test was cancelled or failed")

if __name__ == "__main__":
    test_enhanced_features()