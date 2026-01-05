#!/usr/bin/env python3
"""
OBS Core - WebSocket connection and state management
High-quality production automation for StudioFlow
"""

import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import obsws_python as obs

# Configuration
OBS_HOST = "localhost"
OBS_PORT = 4455
OBS_PASSWORD = None  # Set if you have password protection

class OBSController:
    """Smart OBS WebSocket controller with state caching"""

    def __init__(self, host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD):
        self.host = host
        self.port = port
        self.password = password
        self.client = None
        self.connected = False

        # State cache to avoid repeated requests
        self.state = {
            'scenes': [],
            'current_scene': None,
            'recording': False,
            'streaming': False,
            'sources': {},
            'stats': {}
        }

        # Recording metadata
        self.recording_project = None
        self.recording_markers = []
        self.recording_start_time = None

    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            if self.password:
                self.client = obs.ReqClient(host=self.host, port=self.port, password=self.password)
            else:
                self.client = obs.ReqClient(host=self.host, port=self.port)

            self.connected = True
            self.refresh_state()
            return True

        except Exception as e:
            print(f"Failed to connect to OBS: {e}", file=sys.stderr)
            print("Make sure OBS is running and WebSocket server is enabled", file=sys.stderr)
            print("Tools -> WebSocket Server Settings -> Enable WebSocket Server", file=sys.stderr)
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from OBS"""
        if self.client:
            # No explicit disconnect in obsws_python
            self.client = None
            self.connected = False

    def refresh_state(self):
        """Refresh cached state from OBS"""
        if not self.connected:
            return

        try:
            # Get scenes
            scenes_response = self.client.get_scene_list()
            self.state['scenes'] = [s['sceneName'] for s in scenes_response.scenes]
            self.state['current_scene'] = scenes_response.current_program_scene_name

            # Get recording status
            rec_status = self.client.get_record_status()
            self.state['recording'] = rec_status.output_active

            # Get streaming status
            stream_status = self.client.get_stream_status()
            self.state['streaming'] = stream_status.output_active

            # Get stats
            stats = self.client.get_stats()
            self.state['stats'] = {
                'fps': stats.active_fps,
                'cpu_usage': stats.cpu_usage,
                'memory_usage': stats.memory_usage,
                'render_missed_frames': stats.output_skipped_frames,
                'output_total_frames': stats.output_total_frames
            }

        except Exception as e:
            print(f"Error refreshing state: {e}", file=sys.stderr)

    def get_scenes(self):
        """Get list of available scenes"""
        if not self.connected:
            return []

        self.refresh_state()
        return self.state['scenes']

    def switch_scene(self, scene_name):
        """Switch to a specific scene"""
        if not self.connected:
            return False

        try:
            self.client.set_current_program_scene(scene_name)
            self.state['current_scene'] = scene_name
            return True
        except Exception as e:
            print(f"Error switching scene: {e}", file=sys.stderr)
            return False

    def start_recording(self):
        """Start recording"""
        if not self.connected:
            return False

        try:
            self.client.start_record()
            self.state['recording'] = True
            self.recording_start_time = datetime.now()
            return True
        except Exception as e:
            print(f"Error starting recording: {e}", file=sys.stderr)
            return False

    def stop_recording(self):
        """Stop recording"""
        if not self.connected:
            return False

        try:
            result = self.client.stop_record()
            self.state['recording'] = False

            # Return the output path
            return result.output_path if hasattr(result, 'output_path') else None

        except Exception as e:
            print(f"Error stopping recording: {e}", file=sys.stderr)
            return None

    def toggle_recording(self):
        """Toggle recording on/off"""
        if self.state['recording']:
            return self.stop_recording()
        else:
            return self.start_recording()

    def add_marker(self, marker_type='good', description=''):
        """Add a marker during recording (for later editing reference)"""
        if not self.state['recording']:
            return False

        timestamp = (datetime.now() - self.recording_start_time).total_seconds()

        marker = {
            'time': timestamp,
            'type': marker_type,  # 'good', 'bad', 'short', 'thumbnail'
            'description': description,
            'timestamp': datetime.now().isoformat()
        }

        self.recording_markers.append(marker)
        return marker

    def save_markers(self, output_file=None):
        """Save recording markers to JSON file"""
        if not self.recording_markers:
            return None

        if not output_file and self.recording_project:
            output_file = f"{self.recording_project}_markers.json"

        if output_file:
            with open(output_file, 'w') as f:
                json.dump({
                    'project': self.recording_project,
                    'start_time': self.recording_start_time.isoformat() if self.recording_start_time else None,
                    'markers': self.recording_markers
                }, f, indent=2)

            return output_file

        return None

    def get_sources(self, scene_name=None):
        """Get sources in current or specified scene"""
        if not self.connected:
            return []

        try:
            if not scene_name:
                scene_name = self.state['current_scene']

            items = self.client.get_scene_item_list(scene_name)
            return [item['sourceName'] for item in items.scene_items]

        except Exception as e:
            print(f"Error getting sources: {e}", file=sys.stderr)
            return []

    def set_source_visibility(self, source_name, visible=True, scene_name=None):
        """Show/hide a source in a scene"""
        if not self.connected:
            return False

        try:
            if not scene_name:
                scene_name = self.state['current_scene']

            # Get scene item ID
            items = self.client.get_scene_item_list(scene_name)
            item_id = None

            for item in items.scene_items:
                if item['sourceName'] == source_name:
                    item_id = item['sceneItemId']
                    break

            if item_id:
                self.client.set_scene_item_enabled(
                    scene_name=scene_name,
                    scene_item_id=item_id,
                    scene_item_enabled=visible
                )
                return True

            return False

        except Exception as e:
            print(f"Error setting source visibility: {e}", file=sys.stderr)
            return False

    def create_scene(self, scene_name):
        """Create a new scene"""
        if not self.connected:
            return False

        try:
            self.client.create_scene(scene_name)
            self.state['scenes'].append(scene_name)
            return True
        except Exception as e:
            print(f"Error creating scene: {e}", file=sys.stderr)
            return False

    def get_recording_folder(self):
        """Get the current recording output folder"""
        if not self.connected:
            return None

        try:
            # This might vary based on OBS version
            # You may need to get this from profile settings
            return Path.home() / "Videos"
        except Exception as e:
            print(f"Error getting recording folder: {e}", file=sys.stderr)
            return None

    def get_performance_stats(self):
        """Get current performance statistics"""
        if not self.connected:
            return {}

        self.refresh_state()
        return self.state['stats']

    def is_dropping_frames(self):
        """Check if we're dropping frames"""
        stats = self.get_performance_stats()
        if stats.get('output_total_frames', 0) > 0:
            drop_percentage = (stats.get('render_missed_frames', 0) /
                             stats.get('output_total_frames', 1)) * 100
            return drop_percentage > 1.0  # Alert if >1% frame drop
        return False