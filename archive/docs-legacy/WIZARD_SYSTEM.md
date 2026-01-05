# StudioFlow AI-Powered Wizard System Documentation 🧙🤖

## Overview

The StudioFlow Wizard System is a next-generation interactive framework that combines human intuition with artificial intelligence. Built on the powerful `WizardLib` framework, it provides **immense power with ultimate simplicity** through natural language processing, smart context awareness, and predictive intelligence.

## 🚀 Quick Start

```bash
# Discovery commands
sf wizard list           # Show all available wizards
sf wizard recent         # Show recent wizard sessions

# Run the wizard launcher
sf-wizard               # Interactive wizard selection

# Or run specific wizards directly
sf-wizard setup         # AI-powered first-time setup
sf-wizard project       # Intelligent project creation
sf-wizard workflow      # Dynamic workflow builder
sf-wizard platform      # Platform optimization wizard
sf-wizard trouble       # AI troubleshooting assistant
```

## 🧠 AI-Powered Features

### **Natural Language Processing**
Describe what you want in plain English:
```
Input: "I want to create a beginner tutorial about Python for YouTube"
AI Analysis:
  → Detected intents: tutorial, youtube, beginner
  → Suggested platform: YouTube
  → Suggested complexity: Beginner
  → Auto-configured YouTube settings
```

### **Smart Context Awareness**
- **Project Detection**: Analyzes current directory for Git repos, media files
- **Usage Learning**: Remembers your preferences and suggests defaults
- **Intelligent Defaults**: AI suggests optimal settings with confidence scores
- **Contextual Help**: Provides relevant tips based on your situation

### **Dynamic Step Generation**
Wizards adapt in real-time based on your choices:
- Choose **YouTube** → Adds category, length, monetization steps
- Choose **TikTok** → Adds style, audience, trending options
- Choose **Tutorial** → Adds complexity, code examples, pacing
- Choose **Livestream** → Adds duration, interaction, chat settings

### **Error Prevention & Recovery**
AI predicts and prevents issues before they happen:
- **Platform Mismatches**: "TikTok doesn't support 10+ minute videos"
- **Skill Level Warnings**: "Advanced tutorials challenging for beginners"
- **Tool Optimization**: "DaVinci Resolve may be overkill for TikTok"
- **Auto-Fix**: High-severity issues offer automatic corrections

## 📋 Available Wizards

### 1. 🚀 Setup Wizard (`sf-wizard setup`)

**Purpose**: AI-powered first-time configuration of StudioFlow environment

**AI Features**:
- **Smart Platform Detection**: Analyzes your goals to suggest optimal platform
- **Tool Auto-Discovery**: Automatically detects installed software
- **Intelligent Storage Setup**: Recommends storage structure based on workflow
- **API Key Validation**: Verifies credentials and suggests improvements

**Enhanced Flow**:
```
🚀 StudioFlow AI-Powered Initial Setup
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: ████████████████████ 1/15

💬 Natural Language Mode: Describe your content creation goals
❓ What kind of content do you want to create?:
   "I want to make educational programming tutorials for YouTube"

🧠 AI Analysis: Found intents: tutorial, youtube, programming
   → Suggested platform: YouTube
   → Suggested tools: OBS, Resolve, VS Code
   → Suggested workflow: Educational

🤖 AI Suggestion: YouTube platform recommended (confidence: 95%)
   Based on: Educational content performs best on YouTube long-form

❓ Creator name? [Detected from Git]: YourName
💡 Tip: Consider using your Git username as project base
```

### 2. 📁 Project Wizard (`sf-wizard project`)

**Purpose**: Intelligent project creation with AI optimization

**AI Features**:
- **Natural Language Project Description**: Describe your project in plain English
- **Smart Template Selection**: AI chooses optimal project template
- **Viral Title Generation**: AI suggests titles optimized for discoverability
- **Platform-Specific Optimization**: Auto-configures for chosen platform

**Enhanced Flow**:
```
📁 AI-Powered Project Creator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Progress: ████░░░░░░░░░░░░░░░░ 2/8

💬 Natural Language Mode: Describe your project
❓ Describe your project in natural language:
   "Short viral video about cooking secrets for TikTok"

🧠 AI Analysis: Found intents: cooking, viral, short
   → Suggested platform: TikTok
   → Suggested style: Viral/Trending
   → Viral elements detected: curiosity, secrets

🤖 AI Generated Title: "The Secret Cooking Tricks Nobody Talks About"
   Viral score: 8.5/10 (curiosity + social proof)

🔄 Generating 4 additional steps for TikTok...
   → TikTok content style
   → Target audience age
   → Trending audio options
   → Optimal posting time
```

### 3. ⚙️ Workflow Wizard (`sf-wizard workflow`)

**Purpose**: Build intelligent automation workflows

**AI Features**:
- **Workflow Intelligence**: Suggests optimal tool chains
- **Dependency Detection**: Identifies required tools and settings
- **Performance Optimization**: Recommends workflow improvements
- **Error Prevention**: Validates workflow compatibility

### 4. 📺 Platform Wizard (`sf-wizard platform`)

**Purpose**: Platform-specific optimization with AI insights

**AI Features**:
- **Algorithm Analysis**: Current platform algorithm insights
- **Optimal Timing**: AI-suggested posting schedules
- **Content Optimization**: Platform-specific best practices
- **Trending Analysis**: Real-time trend recommendations

### 5. 🔧 Troubleshooting Wizard (`sf-wizard trouble`)

**Purpose**: AI-powered problem diagnosis and resolution

**AI Features**:
- **Smart Diagnostics**: Analyzes system state for issues
- **Solution Prediction**: Suggests fixes with confidence scores
- **Automatic Repairs**: One-click fixes for common problems
- **Learning System**: Improves suggestions based on success rates

## 🛠️ WizardLib Framework

### Core Classes

#### `InteractiveWizard`
Main wizard orchestrator with AI capabilities:
```python
wizard = InteractiveWizard(
    title="My AI Wizard",
    description="Powered by artificial intelligence",
    enable_context=True,      # Smart context awareness
    auto_save=True           # Automatic session saves
)
```

#### `WizardContext`
Smart context awareness system:
```python
context = WizardContext()
# Automatically detects:
# - Current directory context
# - Git repository information
# - Media files present
# - Previous user preferences
# - Usage patterns and history
```

#### `AIProcessor`
Natural language processing and intelligence:
```python
ai = AIProcessor()
result = ai.parse_natural_language("Create a tutorial about Python")
# Returns: intents, platform suggestions, complexity level
```

#### `DynamicStepGenerator`
Real-time step generation:
```python
generator = DynamicStepGenerator(context)
# Automatically generates platform-specific steps
# Based on user choices and AI analysis
```

### Building AI-Powered Wizards

#### Basic AI Wizard
```python
from wizardlib import create_wizard, AIProcessor

ai = AIProcessor()

wizard = (
    create_wizard("🤖 AI-Powered Creator")
    .description("Natural language project creation")

    # Natural language input with AI processing
    .text_input("description",
               "Describe your project:",
               parser="nlp",
               nlp_handler=ai.parse_natural_language)

    # AI-suggested platforms based on description
    .choice("platform", "Target platform:",
           options=["YouTube", "Instagram", "TikTok"])

    .build()
)
```

#### Advanced AI Features
```python
# Enable all AI capabilities
wizard.ai_defaults_enabled = True     # Smart defaults
wizard.ai_error_prevention = True     # Error prediction
wizard.enable_context = True          # Context awareness

# The wizard will now:
# - Suggest intelligent defaults based on context
# - Predict and prevent errors before they occur
# - Learn from user choices for future suggestions
# - Generate additional steps dynamically
```

## 📊 AI Analytics & Learning

### Usage Patterns
The system learns from your choices:
```json
{
  "frequent_choices": {
    "platform": {"YouTube": 15, "TikTok": 3},
    "project_type": {"tutorial": 12, "review": 6}
  },
  "success_patterns": {
    "YouTube + tutorial": 0.92,
    "TikTok + viral": 0.87
  }
}
```

### Smart Defaults Generation
AI suggests defaults with confidence scores:
```python
{
  "value": "YouTube",
  "confidence": 0.89,
  "reason": "Tutorial directory suggests educational content"
}
```

### Error Prediction
AI prevents issues before they happen:
```python
{
  "type": "platform_mismatch",
  "severity": "high",
  "message": "TikTok doesn't support 10+ minute videos",
  "auto_fix": {"video_length": "Short (< 1 min)"}
}
```

## 🔧 Advanced Configuration

### Environment Variables
```bash
export WIZARD_AI_ENABLED=true          # Enable AI features
export WIZARD_CONTEXT_DIR=~/.wizards   # Context storage
export WIZARD_AUTO_SAVE=true           # Auto-save sessions
export WIZARD_VERBOSE_AI=true          # Show AI reasoning
```

### Configuration File (`~/.config/studioflow/wizard.yml`)
```yaml
ai:
  enabled: true
  confidence_threshold: 0.6
  natural_language: true
  error_prevention: true

context:
  learning_enabled: true
  auto_save: true
  session_retention: 30d

ui:
  progress_style: modern
  theme: ai_enhanced
  show_ai_reasoning: true
```

## 🚀 Performance & Optimization

### Speed Benchmarks
```
AI Analysis:               < 0.01s
Context Detection:         < 0.01s
Smart Default Generation:  < 0.01s
Error Prediction:          < 0.01s
50-step Wizard:            0.05s
Complex AI Processing:     0.03s
```

### Memory Usage
```
Base wizard:               ~1MB
AI processor:              ~2MB
Context system:            ~0.5MB
Large wizard (50 steps):   ~3MB
```

## 🎯 Best Practices

### For Users
1. **Be descriptive** in natural language inputs
2. **Trust AI suggestions** - they're based on proven patterns
3. **Review AI warnings** - they prevent real issues
4. **Use discovery commands** to find relevant wizards

### For Developers
1. **Enable AI features** by default for better UX
2. **Provide contextual help** for complex steps
3. **Use semantic step IDs** for better AI understanding
4. **Test error scenarios** that AI should catch

## 🔮 Future Roadmap

### Short Term (Next Release)
- **Voice Input**: Speech-to-text for natural language steps
- **Visual Recognition**: Image analysis for project context
- **Advanced Analytics**: Detailed success pattern analysis
- **Multi-language**: Support for international users

### Long Term (Next Year)
- **Cloud Intelligence**: Shared learning across users
- **Video Analysis**: Understanding existing content
- **Predictive Workflows**: AI suggests entire workflows
- **Integration APIs**: Third-party AI service integration

## 📚 Examples & Tutorials

### Complete AI Wizard Example
See `/mnt/projects/studioflow/ai_wizard_demo.py` for a full example showcasing:
- Natural language processing
- Smart defaults with confidence scores
- Dynamic step generation
- Error prevention and auto-fix
- Viral content optimization

### Testing AI Features
See `/mnt/projects/studioflow/test_context.py` for testing:
- Context awareness system
- Learning and suggestion mechanisms
- Dynamic step generation
- Error prediction capabilities

---

**The StudioFlow AI-Powered Wizard System represents the future of interactive command-line experiences - combining human intuition with machine intelligence for unprecedented usability and power.** 🤖✨