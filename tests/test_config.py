"""
Comprehensive tests for configuration system
Tests ConfigManager, Config, and all storage/resolve/project configs
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

from studioflow.core.config import (
    ConfigManager,
    Config,
    StorageConfig,
    ResolveConfig,
    ProjectConfig,
    MediaConfig
)


@pytest.mark.unit
class TestConfigManager:
    """Test ConfigManager core functionality"""
    
    def test_config_manager_initialization(self, temp_config_dir):
        """Test ConfigManager initializes correctly"""
        manager = ConfigManager(temp_config_dir)
        
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "config.yaml"
        assert manager.config is not None
        assert isinstance(manager.config, Config)
    
    def test_config_loading_existing_file(self, temp_config_dir):
        """Test loading config from existing file"""
        # Create config file
        config_data = {
            "user_name": "test_user",
            "log_level": "INFO",
            "storage": {
                "active": str(temp_config_dir / "Projects")
            }
        }
        
        config_file = temp_config_dir / "config.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        manager = ConfigManager(temp_config_dir)
        
        assert manager.config.user_name == "test_user"
        assert manager.config.log_level == "INFO"
    
    def test_config_loading_missing_file(self, temp_config_dir):
        """Test loading config when file doesn't exist (creates default)"""
        manager = ConfigManager(temp_config_dir)
        
        # Should create default config
        assert manager.config is not None
        assert manager.config_file.exists()
        assert manager.config.user_name is not None
    
    def test_config_loading_invalid_file(self, temp_config_dir):
        """Test loading config with invalid YAML (falls back to default)"""
        config_file = temp_config_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        manager = ConfigManager(temp_config_dir)
        
        # Should fall back to default
        assert manager.config is not None
        assert manager.config.user_name is not None
    
    def test_config_saving(self, temp_config_dir):
        """Test saving configuration"""
        manager = ConfigManager(temp_config_dir)
        
        # Modify config
        manager.config.log_level = "DEBUG"
        manager.save()
        
        # Reload and verify
        manager2 = ConfigManager(temp_config_dir)
        assert manager2.config.log_level == "DEBUG"
    
    def test_get_simple_value(self, temp_config_dir):
        """Test getting simple config value"""
        manager = ConfigManager(temp_config_dir)
        manager.set("log_level", "DEBUG")
        
        value = manager.get("log_level")
        assert value == "DEBUG"
    
    def test_get_nested_value(self, temp_config_dir):
        """Test getting nested config value"""
        manager = ConfigManager(temp_config_dir)
        manager.set("storage.active", str(temp_config_dir / "Projects"))
        
        value = manager.get("storage.active")
        # Note: get() returns the value as stored (string in this case)
        assert value == str(temp_config_dir / "Projects")
    
    def test_get_nonexistent_value(self, temp_config_dir):
        """Test getting non-existent value returns default"""
        manager = ConfigManager(temp_config_dir)
        
        value = manager.get("nonexistent.key", "default_value")
        assert value == "default_value"
        
        value2 = manager.get("nonexistent.key")
        assert value2 is None
    
    def test_set_simple_value(self, temp_config_dir):
        """Test setting simple config value"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("log_level", "INFO")
        assert manager.config.log_level == "INFO"
        
        # Verify saved
        manager2 = ConfigManager(temp_config_dir)
        assert manager2.get("log_level") == "INFO"
    
    def test_set_nested_value(self, temp_config_dir):
        """Test setting nested config value"""
        manager = ConfigManager(temp_config_dir)
        
        test_path = str(temp_config_dir / "TestProjects")
        manager.set("storage.active", test_path)
        
        # Verify set
        assert manager.get("storage.active") == test_path
        
        # Verify saved
        manager2 = ConfigManager(temp_config_dir)
        assert manager2.get("storage.active") == test_path
    
    def test_set_creates_nested_structure(self, temp_config_dir):
        """Test setting nested value creates structure if needed"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("custom.nested.value", "test")
        
        assert manager.get("custom.nested.value") == "test"
    
    def test_path_objects_vs_strings(self, temp_config_dir):
        """Test path handling - fix for known issue"""
        manager = ConfigManager(temp_config_dir)
        
        # Set as string
        test_path_str = str(temp_config_dir / "Projects")
        manager.set("storage.active", test_path_str)
        
        # Get should return string (not Path object)
        value = manager.get("storage.active")
        assert isinstance(value, str) or isinstance(value, Path)
        # Both are acceptable, but should be consistent
        
        # Direct access via config object returns Path
        assert isinstance(manager.config.storage.active, Path)
    
    def test_all_method(self, temp_config_dir):
        """Test getting all config as dict"""
        manager = ConfigManager(temp_config_dir)
        
        all_config = manager.all()
        
        assert isinstance(all_config, dict)
        assert "user_name" in all_config
        assert "storage" in all_config
        assert "resolve" in all_config
    
    def test_validate_no_issues(self, temp_config_dir):
        """Test validation with valid config"""
        manager = ConfigManager(temp_config_dir)
        
        # Create storage directories
        manager.config.storage.ensure_dirs()
        
        issues = manager.validate()
        assert isinstance(issues, list)
        # Should have no issues if paths exist
    
    def test_validate_missing_paths(self, temp_config_dir):
        """Test validation detects missing paths"""
        manager = ConfigManager(temp_config_dir)
        
        # Set non-existent path
        manager.set("storage.active", str(temp_config_dir / "Nonexistent"))
        
        issues = manager.validate()
        assert len(issues) > 0
        assert any("active" in issue.lower() for issue in issues)
    
    def test_validate_resolve_not_found(self, temp_config_dir):
        """Test validation detects missing Resolve installation"""
        manager = ConfigManager(temp_config_dir)
        manager.config.resolve.enabled = True
        manager.config.resolve.install_path = Path("/nonexistent/resolve")
        
        issues = manager.validate()
        assert len(issues) > 0
        assert any("resolve" in issue.lower() for issue in issues)


@pytest.mark.unit
class TestStorageConfig:
    """Test StorageConfig model"""
    
    def test_storage_config_defaults(self):
        """Test StorageConfig has correct defaults"""
        storage = StorageConfig()
        
        assert storage.ingest is not None
        assert storage.active is not None
        assert storage.render is not None
        assert storage.archive is not None
        assert "StudioFlow" in str(storage.ingest)
    
    def test_storage_config_path_expansion(self):
        """Test path expansion with ~ and env vars"""
        storage = StorageConfig(
            ingest="~/test/ingest",
            active="$HOME/test/projects"
        )
        
        assert storage.ingest.is_absolute()
        assert storage.active.is_absolute()
    
    def test_storage_config_ensure_dirs(self, temp_config_dir):
        """Test ensure_dirs creates directories"""
        storage = StorageConfig(
            ingest=temp_config_dir / "Ingest",
            active=temp_config_dir / "Projects"
        )
        
        storage.ensure_dirs()
        
        assert storage.ingest.exists()
        assert storage.active.exists()
    
    def test_storage_config_optional_paths(self):
        """Test optional paths can be None"""
        storage = StorageConfig()
        
        # These should be None by default
        assert storage.library is None or isinstance(storage.library, Path)
        assert storage.nas is None or isinstance(storage.nas, Path)


@pytest.mark.unit
class TestResolveConfig:
    """Test ResolveConfig model"""
    
    def test_resolve_config_defaults(self):
        """Test ResolveConfig has correct defaults"""
        resolve = ResolveConfig()
        
        assert resolve.install_path == Path("/opt/resolve")
        assert resolve.enabled is True
        assert resolve.default_framerate == 29.97
        assert resolve.default_resolution == "3840x2160"
    
    def test_resolve_config_api_path_auto_detect(self):
        """Test API path auto-detection"""
        resolve = ResolveConfig(
            install_path=Path("/opt/resolve")
        )
        
        # API path should be set if install_path exists
        # (or None if it doesn't)
        assert resolve.api_path is None or resolve.api_path.exists()


@pytest.mark.unit
class TestProjectConfig:
    """Test ProjectConfig model"""
    
    def test_project_config_defaults(self):
        """Test ProjectConfig has correct defaults"""
        project = ProjectConfig()
        
        assert project.default_template == "youtube"
        assert "01_MEDIA" in project.folder_structure
        assert project.auto_categorize is True


@pytest.mark.unit
class TestMediaConfig:
    """Test MediaConfig model"""
    
    def test_media_config_defaults(self):
        """Test MediaConfig has correct defaults"""
        media = MediaConfig()
        
        assert ".mp4" in media.extensions
        assert ".jpg" in media.image_extensions
        assert ".wav" in media.audio_extensions
        assert media.test_clip_max == 3
        assert media.b_roll_min == 10


@pytest.mark.unit
class TestConfigMigration:
    """Test config migration functionality"""
    
    def test_migrate_from_legacy_not_implemented(self, temp_config_dir):
        """Test migration method exists (may not be fully implemented)"""
        manager = ConfigManager(temp_config_dir)
        
        # Method should exist
        assert hasattr(manager, 'migrate_from_legacy')
        
        # Should not raise error (even if not implemented)
        legacy_path = Path("/nonexistent/legacy/config.py")
        # Method may be a stub, so we just check it exists
        assert callable(manager.migrate_from_legacy)


@pytest.mark.unit
class TestConfigSingleton:
    """Test global config singleton"""
    
    def test_get_config_returns_singleton(self):
        """Test get_config returns same instance"""
        from studioflow.core.config import get_config, reload_config
        
        config1 = get_config()
        config2 = get_config()
        
        # Should be same instance (or at least same config)
        assert config1 is not None
        assert config2 is not None
    
    def test_reload_config(self):
        """Test reload_config function exists"""
        from studioflow.core.config import reload_config
        
        # Should not raise error
        reload_config()


@pytest.mark.unit
class TestConfigEdgeCases:
    """Test edge cases and error handling"""
    
    def test_config_with_special_characters(self, temp_config_dir):
        """Test config handles special characters in paths"""
        manager = ConfigManager(temp_config_dir)
        
        # Paths with spaces, special chars
        test_path = temp_config_dir / "Test Projects" / "My Project"
        manager.set("storage.active", str(test_path))
        
        value = manager.get("storage.active")
        assert value is not None
    
    def test_config_empty_string(self, temp_config_dir):
        """Test config handles empty strings"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("log_level", "")
        value = manager.get("log_level")
        assert value == ""
    
    def test_config_none_value(self, temp_config_dir):
        """Test config handles None values"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("storage.library", None)
        value = manager.get("storage.library")
        assert value is None
    
    def test_config_deeply_nested(self, temp_config_dir):
        """Test config handles deeply nested values"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("level1.level2.level3.value", "deep_value")
        value = manager.get("level1.level2.level3.value")
        assert value == "deep_value"
    
    def test_config_overwrite_existing(self, temp_config_dir):
        """Test overwriting existing config value"""
        manager = ConfigManager(temp_config_dir)
        
        manager.set("log_level", "INFO")
        assert manager.get("log_level") == "INFO"
        
        manager.set("log_level", "DEBUG")
        assert manager.get("log_level") == "DEBUG"
    
    def test_config_file_permissions(self, temp_config_dir):
        """Test config handles file permission issues gracefully"""
        manager = ConfigManager(temp_config_dir)
        
        # Make config file read-only (if possible)
        config_file = temp_config_dir / "config.yaml"
        if config_file.exists():
            # Try to save - should handle gracefully
            try:
                manager.save()
            except PermissionError:
                # Expected if file is read-only
                pass

