"""
Unit tests for PromptOptimizer node
"""

import unittest
import json
import os
import sys
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.prompt_optimizer.prompt_optimizer_node import PromptOptimizer


class TestPromptOptimizer(unittest.TestCase):
    """Test cases for PromptOptimizer node"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.optimizer = PromptOptimizer()
        
        # Create a test image array (RGB, 128x128)
        self.test_image = np.random.randint(0, 255, (1, 128, 128, 3), dtype=np.uint8)
        
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any temporary images created during tests
        if hasattr(self, 'optimizer'):
            self.optimizer._cleanup_temp_images()
    
    def test_node_initialization(self):
        """Test node initializes correctly"""
        self.assertIsNotNone(self.optimizer)
        self.assertIsInstance(self.optimizer.model_configs, dict)
        self.assertTrue(len(self.optimizer.model_configs) > 0)
    
    def test_input_types(self):
        """Test INPUT_TYPES class method returns correct structure"""
        input_types = PromptOptimizer.INPUT_TYPES()
        
        # Check required inputs
        self.assertIn('required', input_types)
        self.assertIn('target_model', input_types['required'])
        self.assertIn('prompt', input_types['required'])
        
        # Check optional inputs
        self.assertIn('optional', input_types)
        self.assertIn('image', input_types['optional'])
        self.assertIn('ollama_host', input_types['optional'])
        self.assertIn('ollama_model', input_types['optional'])
        
    def test_return_types(self):
        """Test node return types are correct"""
        self.assertEqual(PromptOptimizer.RETURN_TYPES, ("STRING", "STRING", "STRING"))
        self.assertEqual(PromptOptimizer.RETURN_NAMES, ("positive_prompt", "negative_prompt", "original_prompt"))
        self.assertEqual(PromptOptimizer.FUNCTION, "optimize_prompt")
        self.assertEqual(PromptOptimizer.CATEGORY, "gamedev/prompt")
    
    def test_load_model_configs(self):
        """Test model configurations load correctly"""
        configs = self.optimizer._load_model_configs()
        
        # Check some expected models are present
        self.assertIn('flux_dev', configs)
        self.assertIn('wan22', configs)
        self.assertIn('mmaudio', configs)
        
        # Check config structure
        flux_config = configs.get('flux_dev', {})
        self.assertIn('name', flux_config)
        self.assertIn('supports_negative', flux_config)
        self.assertIn('positive_messages', flux_config)
        
    def test_model_negative_support(self):
        """Test models correctly indicate negative prompt support"""
        configs = self.optimizer.model_configs
        
        # Models that should NOT support negative prompts
        no_negative_models = ['flux_dev', 'flux_krea', 'flux_kontext', 'mmaudio', 'ace_step']
        for model in no_negative_models:
            if model in configs:
                self.assertFalse(configs[model].get('supports_negative', False),
                               f"{model} should not support negative prompts")
        
        # Models that SHOULD support negative prompts
        negative_models = ['wan22', 'wan21']
        for model in negative_models:
            if model in configs:
                self.assertTrue(configs[model].get('supports_negative', False),
                              f"{model} should support negative prompts")
    
    def test_save_image_for_ollama(self):
        """Test image saving for Ollama processing"""
        # Save test image
        image_path = self.optimizer._save_image_for_ollama(self.test_image)
        
        # Check file was created
        self.assertIsNotNone(image_path)
        self.assertTrue(os.path.exists(image_path))
        self.assertTrue(image_path.endswith('.png'))
        
        # Check file is tracked for cleanup
        self.assertIn(image_path, self.optimizer.temp_images)
        
        # Clean up
        self.optimizer._cleanup_temp_images()
        self.assertFalse(os.path.exists(image_path))
    
    def test_save_image_handles_different_formats(self):
        """Test image saving handles different array formats"""
        # Test float32 image (0-1 range)
        float_image = np.random.rand(1, 64, 64, 3).astype(np.float32)
        path1 = self.optimizer._save_image_for_ollama(float_image)
        self.assertIsNotNone(path1)
        self.assertTrue(os.path.exists(path1))
        
        # Test uint8 image (0-255 range)  
        uint8_image = np.random.randint(0, 255, (1, 64, 64, 3), dtype=np.uint8)
        path2 = self.optimizer._save_image_for_ollama(uint8_image)
        self.assertIsNotNone(path2)
        self.assertTrue(os.path.exists(path2))
        
        # Test single image without batch dimension
        single_image = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
        path3 = self.optimizer._save_image_for_ollama(single_image)
        self.assertIsNotNone(path3)
        self.assertTrue(os.path.exists(path3))
        
        # Clean up all
        self.optimizer._cleanup_temp_images()
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')
    def test_optimize_with_ollama_mock(self, mock_ollama):
        """Test Ollama optimization with mocked client"""
        # Setup mock
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {
                "content": "Optimized prompt response"
            }
        }
        
        # Test optimization
        messages = [{"role": "system", "content": "Test system prompt"}]
        result = self.optimizer._optimize_with_ollama(
            messages,
            "test prompt",
            None,
            "localhost:11434",
            "test-model"
        )
        
        # Check mock was called
        mock_ollama.Client.assert_called_once()
        mock_client.chat.assert_called_once()
        
        # Check result
        self.assertEqual(result, "Optimized prompt response")
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama', None)
    def test_optimize_without_ollama(self):
        """Test behavior when Ollama is not installed"""
        messages = [{"role": "system", "content": "Test"}]
        result = self.optimizer._optimize_with_ollama(
            messages,
            "test prompt",
            None,
            "localhost:11434",
            "test-model"
        )
        
        # Should return original prompt when Ollama not available
        self.assertEqual(result, "test prompt")
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')
    def test_optimize_prompt_flux_dev(self, mock_ollama):
        """Test full prompt optimization for flux_dev model"""
        # Setup mock
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {
                "content": "A majestic dragon with scales, flying through clouds, digital art, 8K"
            }
        }
        
        # Test optimization
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="flux_dev",
            prompt="a dragon"
        )
        
        # Check results
        self.assertIn("dragon", positive)
        self.assertEqual(negative, "")  # flux_dev doesn't support negative
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')
    def test_optimize_prompt_wan22_with_negative(self, mock_ollama):
        """Test prompt optimization for wan22 with negative prompt support"""
        # Setup mock for both positive and negative calls
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        
        # Mock responses for positive and negative
        mock_client.chat.side_effect = [
            {
                "message": {
                    "content": "A golden retriever running through meadow, slow motion tracking shot"
                }
            },
            {
                "message": {
                    "content": "--no motion blur --no shaky camera --no distortion"
                }
            }
        ]
        
        # Test optimization
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="wan22",
            prompt="dog running"
        )
        
        # Check results
        self.assertIn("retriever", positive)
        self.assertIn("--no", negative)
        
        # Check both calls were made
        self.assertEqual(mock_client.chat.call_count, 2)
    
    def test_unknown_model_handling(self):
        """Test handling of unknown model types"""
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="unknown_model_xyz",
            prompt="test prompt"
        )
        
        # Should return original prompt for unknown models
        self.assertEqual(positive, "test prompt")
        self.assertEqual(negative, "")
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')
    def test_optimize_with_image(self, mock_ollama):
        """Test optimization with image input"""
        # Setup mock
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {
                "content": "A red ball on green grass, photorealistic, outdoor lighting"
            }
        }
        
        # Test with image
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="flux_dev",
            prompt="a ball",
            image=self.test_image
        )
        
        # Check image was saved
        self.assertEqual(len(self.optimizer.temp_images), 0)  # Should be cleaned up after
        
        # Check chat was called with image
        call_args = mock_client.chat.call_args
        messages = call_args[1]['messages']
        
        # Last message should have image path
        last_message = messages[-1]
        self.assertIn('images', last_message)
    
    def test_cleanup_on_deletion(self):
        """Test temporary files are cleaned up on object deletion"""
        # Create a new optimizer and save an image
        optimizer2 = PromptOptimizer()
        image_path = optimizer2._save_image_for_ollama(self.test_image)
        self.assertTrue(os.path.exists(image_path))
        
        # Delete optimizer
        del optimizer2
        
        # File should be cleaned up
        self.assertFalse(os.path.exists(image_path))
    
    def test_message_structure(self):
        """Test message structure for different models"""
        for model_name, config in self.optimizer.model_configs.items():
            # Check positive messages
            positive_messages = config.get('positive_messages', [])
            self.assertIsInstance(positive_messages, list)
            
            if positive_messages:
                # Check system message
                self.assertEqual(positive_messages[0]['role'], 'system')
                self.assertIn('content', positive_messages[0])
                
                # Check examples (should have pairs of user/assistant)
                for i in range(1, len(positive_messages), 2):
                    if i < len(positive_messages) - 1:
                        self.assertEqual(positive_messages[i]['role'], 'user')
                        self.assertEqual(positive_messages[i+1]['role'], 'assistant')
            
            # Check negative messages if supported
            if config.get('supports_negative', False):
                negative_messages = config.get('negative_messages', [])
                self.assertIsInstance(negative_messages, list)
                
                if negative_messages:
                    self.assertEqual(negative_messages[0]['role'], 'system')
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')
    def test_ollama_error_handling(self, mock_ollama):
        """Test error handling when Ollama fails"""
        # Setup mock to raise exception
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        mock_client.chat.side_effect = Exception("Connection failed")
        
        # Test optimization - should return original prompt on error
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="flux_dev",
            prompt="test prompt"
        )
        
        self.assertEqual(positive, "test prompt")
        self.assertEqual(negative, "")
    
    @patch('nodes.prompt_optimizer.prompt_optimizer_node.ollama')  
    def test_empty_response_handling(self, mock_ollama):
        """Test handling of empty Ollama responses"""
        # Setup mock with empty response
        mock_client = MagicMock()
        mock_ollama.Client.return_value = mock_client
        mock_client.chat.return_value = {
            "message": {
                "content": ""  # Empty response
            }
        }
        
        # Test optimization
        positive, negative, original = self.optimizer.optimize_prompt(
            target_model="flux_dev",
            prompt="original prompt"
        )
        
        # Should return original on empty response
        self.assertEqual(positive, "original prompt")
    
    def test_node_registration(self):
        """Test node is properly registered for ComfyUI"""
        from nodes.prompt_optimizer import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
        
        self.assertIn("PromptOptimizer", NODE_CLASS_MAPPINGS)
        self.assertEqual(NODE_CLASS_MAPPINGS["PromptOptimizer"], PromptOptimizer)
        
        self.assertIn("PromptOptimizer", NODE_DISPLAY_NAME_MAPPINGS)
        self.assertEqual(NODE_DISPLAY_NAME_MAPPINGS["PromptOptimizer"], "Prompt Optimizer (Ollama)")


class TestModelConfigurations(unittest.TestCase):
    """Test model configuration file integrity"""
    
    def setUp(self):
        """Load model configurations"""
        config_path = Path(__file__).parent.parent / "nodes" / "prompt_optimizer" / "model_configs.json"
        with open(config_path, 'r') as f:
            self.configs = json.load(f).get("models", {})
    
    def test_all_models_have_required_fields(self):
        """Test all models have required configuration fields"""
        required_fields = ['name', 'supports_negative', 'positive_messages']
        
        for model_id, config in self.configs.items():
            for field in required_fields:
                self.assertIn(field, config, f"Model {model_id} missing field {field}")
    
    def test_negative_support_consistency(self):
        """Test models with negative support have negative messages"""
        for model_id, config in self.configs.items():
            if config.get('supports_negative', False):
                self.assertIn('negative_messages', config,
                            f"Model {model_id} supports negative but has no negative_messages")
                self.assertTrue(len(config['negative_messages']) > 0,
                              f"Model {model_id} has empty negative_messages")
    
    def test_message_count_consistency(self):
        """Test each model has appropriate number of examples"""
        for model_id, config in self.configs.items():
            positive_messages = config.get('positive_messages', [])
            
            # Should have system message plus at least 3 examples (6 messages total)
            self.assertGreaterEqual(len(positive_messages), 7,
                                  f"Model {model_id} needs at least 3 examples")
            
            # Check alternating user/assistant pattern after system
            for i in range(1, len(positive_messages), 2):
                if i < len(positive_messages):
                    self.assertEqual(positive_messages[i]['role'], 'user',
                                   f"Model {model_id} message {i} should be user")
                if i + 1 < len(positive_messages):
                    self.assertEqual(positive_messages[i+1]['role'], 'assistant',
                                   f"Model {model_id} message {i+1} should be assistant")


if __name__ == '__main__':
    unittest.main()