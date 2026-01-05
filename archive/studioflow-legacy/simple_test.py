#!/usr/bin/env python3
"""Simple test of wizard features"""

from wizardlib import create_wizard

def simple_test():
    """Simple wizard test"""
    wizard = (
        create_wizard("Simple Test")
        .text_input("name", "Name?", default="User")
        .choice("option", "Pick one:", ["A", "B", "C"])
        .build()
    )

    print("🧪 Testing wizard with auto-save and navigation...")
    print("   (The wizard will auto-save after each step)")
    print("   (Type 'help' to see navigation commands)")

    result = wizard.run()
    if result:
        print(f"\n✅ Completed! Result: {result}")

if __name__ == "__main__":
    simple_test()