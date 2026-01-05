#!/usr/bin/env python3
"""
StudioFlow Capture Tools - Screenshot and screen recording pipeline
Simple but effective tools for content creators
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import numpy as np

class CaptureManager:
    """Manages screenshot capture workflow with essential quality features"""

    def __init__(self):
        # Simple 3-stage pipeline
        self.capture_dir = Path("/mnt/ingest/captures")
        self.working_dir = Path("/mnt/resolve/captures")
        self.final_dir = Path("/mnt/render/captures")

        # Create essential directories
        self.dirs = {
            "hot": self.capture_dir / "today",
            "inbox": self.capture_dir / "inbox",
            "working": self.working_dir,
            "final": self.final_dir
        }

        for dir_path in self.dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)

        # Standard resolutions
        self.resolutions = {
            "4k": (3840, 2160),
            "1080p": (1920, 1080),
            "720p": (1280, 720),
            "square": (1080, 1080),
            "vertical": (1080, 1920)
        }

        # Browser crop presets (removes UI chrome)
        self.browser_crops = {
            "chrome": {"top": 120, "bottom": 0, "left": 0, "right": 0},
            "firefox": {"top": 110, "bottom": 0, "left": 0, "right": 0},
            "safari": {"top": 100, "bottom": 0, "left": 0, "right": 0},
            "arc": {"top": 130, "bottom": 0, "left": 0, "right": 0},
            "edge": {"top": 120, "bottom": 0, "left": 0, "right": 0}
        }

    def quick_capture(self, name: Optional[str] = None) -> str:
        """Quick screenshot with auto-naming"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if name:
            filename = f"{timestamp}_{name}.png"
        else:
            filename = f"{timestamp}.png"

        filepath = self.dirs["hot"] / filename

        # Use gnome-screenshot for quick capture
        cmd = ["gnome-screenshot", "-f", str(filepath)]
        subprocess.run(cmd, check=True)

        print(f"📸 Captured: {filepath.name}")
        return str(filepath)

    def crop_browser_chrome(self, image_path: str, browser: str = "chrome",
                           output_path: Optional[str] = None) -> str:
        """Remove browser UI, keep content only - biggest quality impact"""
        img = Image.open(image_path)
        crop_settings = self.browser_crops.get(browser, self.browser_crops["chrome"])

        # Calculate crop box
        width, height = img.size
        crop_box = (
            crop_settings["left"],
            crop_settings["top"],
            width - crop_settings["right"],
            height - crop_settings["bottom"]
        )

        cropped = img.crop(crop_box)

        if not output_path:
            output_path = image_path.replace(".png", "_cropped.png")

        cropped.save(output_path, "PNG", optimize=True)
        print(f"✂️  Cropped browser chrome: {Path(output_path).name}")
        return output_path

    def standardize_resolution(self, image_path: str, target: str = "1080p",
                              background: str = "black") -> str:
        """Resize to standard resolution with padding if needed"""
        img = Image.open(image_path)
        target_size = self.resolutions[target]

        # Create new image with target size and background
        new_img = Image.new("RGB", target_size, background)

        # Calculate position to center the original image
        img.thumbnail(target_size, Image.Resampling.LANCZOS)

        # Center the image
        x = (target_size[0] - img.width) // 2
        y = (target_size[1] - img.height) // 2

        new_img.paste(img, (x, y))

        output_path = image_path.replace(".png", f"_{target}.png")
        new_img.save(output_path, "PNG", optimize=True)

        print(f"📐 Standardized to {target}: {Path(output_path).name}")
        return output_path

    def create_comparison_grid(self, images: List[str], layout: str = "horizontal",
                               labels: Optional[List[str]] = None,
                               output_name: Optional[str] = None) -> str:
        """Create side-by-side or grid comparison - essential for AI tool videos"""
        if not images:
            raise ValueError("No images provided")

        # Load all images
        imgs = [Image.open(img) for img in images]

        # Standardize sizes first
        max_width = max(img.width for img in imgs)
        max_height = max(img.height for img in imgs)

        # Resize all to same dimensions
        resized = []
        for img in imgs:
            new_img = Image.new("RGB", (max_width, max_height), "black")
            # Center the image
            x = (max_width - img.width) // 2
            y = (max_height - img.height) // 2
            new_img.paste(img, (x, y))
            resized.append(new_img)

        # Determine grid layout
        if layout == "horizontal":
            cols = len(resized)
            rows = 1
        elif layout == "vertical":
            cols = 1
            rows = len(resized)
        elif layout == "grid":
            cols = min(3, len(resized))
            rows = (len(resized) + cols - 1) // cols
        else:
            cols = 2
            rows = (len(resized) + 1) // 2

        # Create the grid with padding
        padding = 20
        grid_width = cols * max_width + (cols + 1) * padding
        grid_height = rows * max_height + (rows + 1) * padding

        grid = Image.new("RGB", (grid_width, grid_height), "#1a1a1a")
        draw = ImageDraw.Draw(grid)

        # Place images in grid
        for idx, img in enumerate(resized):
            col = idx % cols
            row = idx // cols
            x = padding + col * (max_width + padding)
            y = padding + row * (max_height + padding)
            grid.paste(img, (x, y))

            # Add labels if provided
            if labels and idx < len(labels):
                label_y = y - 15
                # Try to use a font, fallback to default
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                except:
                    font = ImageFont.load_default()

                # Add text with background for readability
                text = labels[idx]
                bbox = draw.textbbox((x, label_y), text, font=font)
                draw.rectangle([bbox[0]-5, bbox[1]-2, bbox[2]+5, bbox[3]+2], fill="#333333")
                draw.text((x, label_y), text, fill="white", font=font)

        # Save the grid
        if not output_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"comparison_{timestamp}.png"

        output_path = self.working_dir / output_name
        grid.save(output_path, "PNG", optimize=True)

        print(f"🔲 Created comparison grid: {output_path.name}")
        return str(output_path)

    def add_annotation(self, image_path: str, annotations: List[Dict],
                      output_path: Optional[str] = None) -> str:
        """Add highlights, arrows, and text annotations"""
        img = Image.open(image_path)
        draw = ImageDraw.Draw(img, "RGBA")

        for ann in annotations:
            ann_type = ann.get("type", "highlight")

            if ann_type == "highlight":
                # Draw semi-transparent rectangle
                coords = ann["coords"]  # [x1, y1, x2, y2]
                draw.rectangle(coords, outline="#FF0000", width=3)
                # Add semi-transparent fill
                overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                overlay_draw = ImageDraw.Draw(overlay)
                overlay_draw.rectangle(coords, fill=(255, 0, 0, 50))
                img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
                draw = ImageDraw.Draw(img)

            elif ann_type == "arrow":
                # Draw arrow pointing to something
                start = tuple(ann["from"])
                end = tuple(ann["to"])
                draw.line([start, end], fill="#FF0000", width=3)
                # Draw arrowhead
                self._draw_arrowhead(draw, start, end)

            elif ann_type == "text":
                # Add text with background
                pos = tuple(ann["pos"])
                text = ann["text"]
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                                             ann.get("size", 20))
                except:
                    font = ImageFont.load_default()

                # Add background for readability
                bbox = draw.textbbox(pos, text, font=font)
                padding = 5
                draw.rectangle([bbox[0]-padding, bbox[1]-padding,
                               bbox[2]+padding, bbox[3]+padding],
                              fill=ann.get("bg_color", "#000000"))
                draw.text(pos, text, fill=ann.get("color", "#FFFFFF"), font=font)

            elif ann_type == "circle":
                # Circle around important elements
                center = ann["center"]
                radius = ann["radius"]
                bbox = [center[0]-radius, center[1]-radius,
                       center[0]+radius, center[1]+radius]
                draw.ellipse(bbox, outline="#FF0000", width=3)

        if not output_path:
            output_path = image_path.replace(".png", "_annotated.png")

        img.save(output_path, "PNG", optimize=True)
        print(f"✏️  Added annotations: {Path(output_path).name}")
        return output_path

    def _draw_arrowhead(self, draw, start: Tuple, end: Tuple):
        """Helper to draw arrowhead"""
        import math
        angle = math.atan2(end[1] - start[1], end[0] - start[0])
        arrow_length = 15
        arrow_angle = math.pi / 6

        # Calculate arrowhead points
        x1 = end[0] - arrow_length * math.cos(angle - arrow_angle)
        y1 = end[1] - arrow_length * math.sin(angle - arrow_angle)
        x2 = end[0] - arrow_length * math.cos(angle + arrow_angle)
        y2 = end[1] - arrow_length * math.sin(angle + arrow_angle)

        draw.polygon([end, (x1, y1), (x2, y2)], fill="#FF0000")

    def batch_process(self, project_name: str, operations: List[str] = None):
        """Process all captures in today folder with standard operations"""
        if operations is None:
            operations = ["crop", "standardize"]

        project_dir = self.working_dir / project_name
        project_dir.mkdir(exist_ok=True)

        processed = []
        for img_file in self.dirs["hot"].glob("*.png"):
            output_path = str(img_file)

            if "crop" in operations:
                output_path = self.crop_browser_chrome(output_path)

            if "standardize" in operations:
                output_path = self.standardize_resolution(output_path)

            # Move to project folder
            final_path = project_dir / Path(output_path).name
            shutil.move(output_path, final_path)
            processed.append(str(final_path))

        print(f"\n✅ Processed {len(processed)} captures to {project_dir.name}/")
        return processed

    def organize_day(self, project_name: Optional[str] = None):
        """Move today's captures to project folder"""
        if not project_name:
            project_name = datetime.now().strftime("%Y%m%d_project")

        project_dir = self.working_dir / project_name
        project_dir.mkdir(exist_ok=True)

        moved = 0
        for file in self.dirs["hot"].glob("*"):
            if file.is_file():
                shutil.move(str(file), project_dir / file.name)
                moved += 1

        print(f"📁 Organized {moved} files to {project_name}/")
        return project_dir


class CaptureWorkflow:
    """High-level workflow automation"""

    def __init__(self):
        self.manager = CaptureManager()

    def ai_comparison_workflow(self, tool_names: List[str]):
        """Complete workflow for AI tool comparison videos"""
        print(f"\n🎬 Starting AI Comparison Workflow for: {', '.join(tool_names)}")

        captures = []

        # Step 1: Capture each tool
        for tool in tool_names:
            input(f"\n📸 Set up {tool} and press Enter to capture...")
            capture = self.manager.quick_capture(tool.lower().replace(" ", "_"))
            captures.append(capture)

        # Step 2: Crop browser chrome from all
        print("\n✂️  Removing browser UI...")
        cropped = []
        for capture in captures:
            cropped_path = self.manager.crop_browser_chrome(capture)
            cropped.append(cropped_path)

        # Step 3: Standardize resolution
        print("\n📐 Standardizing resolution...")
        standardized = []
        for img in cropped:
            std_path = self.manager.standardize_resolution(img, "1080p")
            standardized.append(std_path)

        # Step 4: Create comparison grid
        print("\n🔲 Creating comparison grid...")
        grid_path = self.manager.create_comparison_grid(
            standardized,
            layout="horizontal",
            labels=tool_names
        )

        print(f"\n✅ Comparison ready: {grid_path}")
        return grid_path

    def tutorial_workflow(self, topic: str):
        """Workflow for tutorial/how-to videos"""
        print(f"\n📚 Starting Tutorial Workflow: {topic}")

        step_num = 1
        captures = []

        while True:
            action = input(f"\nStep {step_num} - [c]apture, [a]nnotate last, [f]inish: ").lower()

            if action == "c":
                capture = self.manager.quick_capture(f"{topic}_step{step_num:02d}")
                cropped = self.manager.crop_browser_chrome(capture)
                captures.append(cropped)
                step_num += 1

            elif action == "a" and captures:
                # Simple annotation for the last capture
                last = captures[-1]
                print("Add annotation (example: highlight,100,100,300,200):")
                ann_input = input("Format: type,x1,y1,x2,y2: ")

                if ann_input:
                    parts = ann_input.split(",")
                    if parts[0] == "highlight" and len(parts) == 5:
                        annotations = [{
                            "type": "highlight",
                            "coords": [int(parts[1]), int(parts[2]),
                                       int(parts[3]), int(parts[4])]
                        }]
                        annotated = self.manager.add_annotation(last, annotations)
                        captures[-1] = annotated

            elif action == "f":
                break

        # Standardize all captures
        print("\n📐 Standardizing all captures...")
        final_captures = []
        for capture in captures:
            std = self.manager.standardize_resolution(capture, "1080p")
            final_captures.append(std)

        print(f"\n✅ Tutorial complete: {len(final_captures)} steps captured")
        return final_captures


def setup_capture_tools():
    """Initial setup for capture tools"""
    print("🎬 Setting up StudioFlow Capture Tools...")

    manager = CaptureManager()

    # Create quick access symlinks
    symlinks = [
        (manager.dirs["hot"], Path.home() / "Captures" / "Today"),
        (manager.working_dir, Path.home() / "Captures" / "Working"),
        (manager.final_dir, Path.home() / "Captures" / "Ready")
    ]

    for source, target in symlinks:
        target.parent.mkdir(exist_ok=True)
        if not target.exists():
            target.symlink_to(source)
            print(f"  ✓ Created symlink: {target}")

    # Add bash aliases
    bashrc = Path.home() / ".bashrc"
    aliases = [
        "alias cap='python3 -m studioflow.extensions.capture_tools capture'",
        "alias caps='cd /mnt/ingest/captures/today'",
        "alias capgrid='python3 -m studioflow.extensions.capture_tools grid'",
        "alias caporg='python3 -m studioflow.extensions.capture_tools organize'"
    ]

    with open(bashrc, "r") as f:
        content = f.read()

    for alias in aliases:
        if alias not in content:
            with open(bashrc, "a") as f:
                f.write(f"\n{alias}")
            print(f"  ✓ Added alias: {alias.split('=')[0]}")

    print("\n✅ Capture Tools ready!")
    print("\nQuick commands:")
    print("  cap [name]  - Quick capture")
    print("  caps        - Go to captures folder")
    print("  capgrid     - Create comparison grid")
    print("  caporg      - Organize today's captures")

    return manager


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]
        manager = CaptureManager()

        if command == "capture":
            name = sys.argv[2] if len(sys.argv) > 2 else None
            manager.quick_capture(name)

        elif command == "crop":
            if len(sys.argv) > 2:
                manager.crop_browser_chrome(sys.argv[2])

        elif command == "grid":
            # Find recent captures
            recent = sorted(manager.dirs["hot"].glob("*.png"))[-3:]
            if recent:
                manager.create_comparison_grid([str(f) for f in recent])

        elif command == "organize":
            project = sys.argv[2] if len(sys.argv) > 2 else None
            manager.organize_day(project)

        elif command == "setup":
            setup_capture_tools()

    else:
        setup_capture_tools()