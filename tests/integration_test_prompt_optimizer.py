"""
Integration tests for PromptOptimizer that actually execute with real Ollama calls
These tests skip ComfyUI but test the actual prompt optimization with real data
"""

import unittest
import os
import sys
import tempfile
import time
from pathlib import Path
import torch
import numpy as np
from PIL import Image
from unittest.mock import Mock, patch
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from nodes.prompt_optimizer.prompt_optimizer_node import PromptOptimizer
from tests.comfyui_mock import ComfyUIMockContext, create_test_image_tensor, MockComfyUINode

# Check if ollama is available
try:
    import ollama
    OLLAMA_AVAILABLE = True
    # Test connection
    try:
        ollama.Client().list()
    except Exception:
        OLLAMA_AVAILABLE = False
        print("⚠️ Ollama service not running")
except ImportError:
    OLLAMA_AVAILABLE = False
    print("⚠️ Ollama not installed")


class TestPromptOptimizerIntegration(unittest.TestCase, MockComfyUINode):
    """Integration tests with real Ollama execution"""
    
    @classmethod
    def setUpClass(cls):
        """Set up class-level resources"""
        # Skip all tests if Ollama is not available
        if not OLLAMA_AVAILABLE:
            raise unittest.SkipTest("Ollama not available - install with: pip install ollama")
        
        # Test if qwen2.5vl:7b model is available
        try:
            client = ollama.Client()
            models_response = client.list()
            models = [model.get('model', model.get('name', '')) for model in models_response.get('models', [])]
            if 'qwen2.5vl:7b' not in models:
                raise unittest.SkipTest("qwen2.5vl:7b model not found - run: ollama pull qwen2.5vl:7b")
        except Exception as e:
            raise unittest.SkipTest(f"Cannot connect to Ollama: {e}")
        
        # Test image path
        cls.test_image_path = Path(__file__).parent.parent / "examples" / "input_images" / "single_view" / "railgun" / "frame_001_4x.png"
        
        print(f"Integration tests using Ollama with qwen2.5vl:7b model")
        print(f"Test image available: {cls.test_image_path.exists()}")
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.optimizer = PromptOptimizer()
        
        # Create test image tensor
        self.test_image = create_test_image_tensor(1, 256, 256, 3)
        
        # Load real test image if available
        self.real_image = None
        if self.test_image_path.exists():
            pil_image = Image.open(self.test_image_path).convert('RGB')
            # Resize if needed
            if pil_image.size != (512, 512):
                pil_image = pil_image.resize((512, 512))
            # Convert to tensor format
            image_array = np.array(pil_image, dtype=np.float32) / 255.0
            self.real_image = torch.from_numpy(image_array).unsqueeze(0)  # Add batch dimension
    
    def tearDown(self):
        """Clean up test fixtures"""
        if hasattr(self, 'optimizer'):
            self.optimizer._cleanup_temp_images()
        self.context.__exit__(None, None, None)
    
    def test_flux_dev_optimization_real_ollama(self):
        """Test FLUX Dev prompt optimization with real Ollama"""
        test_prompt = "a majestic dragon"
        
        start_time = time.time()
        positive, negative, original = self.simulate_comfyui_execution(
            self.optimizer,
            "optimize_prompt",
            target_model="flux_dev",
            prompt=test_prompt,
            ollama_host="localhost:11434",
            ollama_model="qwen2.5vl:7b",
            temperature=0.7,
            seed=42  # Fixed seed for reproducible results
        )
        end_time = time.time()
        
        # Verify basic structure
        self.assertIsInstance(positive, str)
        self.assertIsInstance(negative, str)
        self.assertEqual(original, test_prompt)
        
        # Verify optimization occurred
        self.assertNotEqual(positive, test_prompt, "Positive prompt should be optimized")
        self.assertGreater(len(positive), len(test_prompt), "Optimized prompt should be more detailed")
        
        # Verify FLUX Dev supports negative prompts
        self.assertIsInstance(negative, str)  # Could be empty or populated
        
        # Check for reasonable optimization quality
        self.assertIn("dragon", positive.lower(), "Original concept should be preserved")
        self.assertGreater(len(positive.split()), 3, "Optimized prompt should have multiple words")
        
        # Performance check
        elapsed = end_time - start_time
        self.assertLess(elapsed, 30.0, "Optimization should complete within 30 seconds")
        
        print(f"✅ FLUX Dev optimization completed in {elapsed:.2f}s")
        print(f"   Original: '{test_prompt}'")
        print(f"   Optimized: '{positive[:100]}...' ({len(positive)} chars)")
        if negative:
            print(f"   Negative: '{negative[:50]}...' ({len(negative)} chars)")
        
        return positive, negative, elapsed
    
    def test_wan22_optimization_with_negative_real_ollama(self):
        """Test WAN22 prompt optimization with negative prompt support"""
        test_prompt = "dog running in park"
        
        positive, negative, original = self.simulate_comfyui_execution(
            self.optimizer,
            "optimize_prompt",
            target_model="wan22",
            prompt=test_prompt,
            temperature=0.8,
            seed=123
        )
        
        # Verify basic structure
        self.assertIsInstance(positive, str)
        self.assertIsInstance(negative, str) 
        self.assertEqual(original, test_prompt)
        
        # WAN22 should support negative prompts
        config = self.optimizer.model_configs.get("wan22", {})
        if config.get("supports_negative", False):
            # If negative prompts are supported, we might get content
            if negative:
                self.assertGreater(len(negative), 0, "Negative prompt should have content")
                # Check for typical negative prompt indicators
                negative_indicators = ["--no", "blur", "low quality", "distortion"]
                has_indicator = any(indicator in negative.lower() for indicator in negative_indicators)
                if has_indicator:
                    print(f"   Found negative prompt indicators: {negative}")
        
        # Verify optimization quality
        self.assertNotEqual(positive, test_prompt)
        self.assertIn("dog", positive.lower())
        
        print(f"✅ WAN22 optimization completed")
        print(f"   Original: '{test_prompt}'")
        print(f"   Optimized: '{positive[:100]}...' ({len(positive)} chars)")
        if negative:
            print(f"   Negative: '{negative[:100]}...' ({len(negative)} chars)")
    
    def test_optimization_with_real_image(self):
        """Test optimization with real image input"""
        if self.real_image is None:
            self.skipTest("Real test image not available")
        
        test_prompt = "anime character"
        
        positive, negative, original = self.simulate_comfyui_execution(
            self.optimizer,
            "optimize_prompt",
            target_model="flux_dev",
            prompt=test_prompt,
            image=self.real_image,
            temperature=0.7,
            seed=456
        )
        
        # Verify image was processed
        self.assertEqual(len(self.optimizer.temp_images), 0)  # Should be cleaned up
        
        # Verify optimization occurred
        self.assertNotEqual(positive, test_prompt)
        self.assertGreater(len(positive), len(test_prompt))
        
        # With image context, the optimization might be more specific
        self.assertIn("anime", positive.lower()) 
        
        print(f"✅ Image-based optimization completed")
        print(f"   Original: '{test_prompt}'")
        print(f"   With image: '{positive[:100]}...' ({len(positive)} chars)")
    
    def test_different_temperatures_real_ollama(self):
        """Test optimization with different temperature settings"""
        test_prompt = "cyberpunk city"
        temperatures = [0.1, 0.7, 1.5]
        results = []
        
        for temp in temperatures:
            with self.subTest(temperature=temp):
                positive, negative, original = self.simulate_comfyui_execution(
                    self.optimizer,
                    "optimize_prompt",
                    target_model="flux_dev",
                    prompt=test_prompt,
                    temperature=temp,
                    seed=789  # Same seed for comparison
                )
                
                results.append((temp, positive, len(positive)))
                
                # Verify basic properties
                self.assertNotEqual(positive, test_prompt)
                self.assertIn("cyberpunk", positive.lower())
                
                print(f"Temperature {temp}: '{positive[:80]}...' ({len(positive)} chars)")
        
        # Analyze temperature effects
        lengths = [length for _, _, length in results]
        print(f"✅ Temperature variation test completed")
        print(f"   Lengths at different temperatures: {lengths}")
        
        # Generally, higher temperature might produce more varied results
        # but this isn't guaranteed, so we just verify all completed successfully
        self.assertEqual(len(results), len(temperatures))
    
    def test_seed_consistency_real_ollama(self):
        """Test that same seed produces consistent results"""
        test_prompt = "medieval castle"
        seed = 999
        
        # Run optimization twice with same seed
        result1 = self.simulate_comfyui_execution(
            self.optimizer, "optimize_prompt",
            target_model="flux_dev", prompt=test_prompt,
            temperature=0.7, seed=seed
        )
        
        result2 = self.simulate_comfyui_execution(
            self.optimizer, "optimize_prompt", 
            target_model="flux_dev", prompt=test_prompt,
            temperature=0.7, seed=seed
        )
        
        positive1, negative1, original1 = result1
        positive2, negative2, original2 = result2
        
        # Results should be identical with same seed
        self.assertEqual(positive1, positive2, "Same seed should produce identical results")
        self.assertEqual(negative1, negative2, "Same seed should produce identical negative prompts")
        
        print(f"✅ Seed consistency verified")
        print(f"   Seed {seed} produced identical results")
        print(f"   Result: '{positive1[:60]}...'")
    
    def test_multiple_models_real_ollama(self):
        """Test optimization with different target models"""
        test_prompt = "space station"
        
        # Test different models that should be available
        models_to_test = ["flux_dev", "chroma_hd"]
        
        results = {}
        
        for model in models_to_test:
            with self.subTest(model=model):
                if model not in self.optimizer.model_configs:
                    continue
                
                try:
                    positive, negative, original = self.simulate_comfyui_execution(
                        self.optimizer, "optimize_prompt",
                        target_model=model, prompt=test_prompt,
                        temperature=0.7, seed=111
                    )
                    
                    results[model] = {
                        'positive': positive,
                        'negative': negative,
                        'length': len(positive)
                    }
                    
                    # Verify basic properties
                    self.assertNotEqual(positive, test_prompt)
                    self.assertIn("space", positive.lower())
                    
                    print(f"Model {model}: '{positive[:60]}...' ({len(positive)} chars)")
                    
                except Exception as e:
                    print(f"⚠️ Model {model} failed: {e}")
        
        # Verify we got results for at least one model
        self.assertGreater(len(results), 0, "At least one model should work")
        
        print(f"✅ Multi-model test completed for {len(results)} models")
    
    def test_error_handling_real_ollama(self):
        """Test error handling with real Ollama"""
        # Test with invalid model name
        positive, negative, original = self.simulate_comfyui_execution(
            self.optimizer, "optimize_prompt",
            target_model="nonexistent_model", 
            prompt="test prompt"
        )
        
        # Should return original prompt for unknown models
        self.assertEqual(positive, "test prompt")
        self.assertEqual(negative, "")
        self.assertEqual(original, "test prompt")
        
        print(f"✅ Error handling verified for unknown model")
    
    def test_long_prompt_optimization_real_ollama(self):
        """Test optimization with longer input prompts"""
        long_prompt = ("A detailed fantasy scene with multiple characters including "
                      "a wizard casting spells, knights in armor, dragons flying overhead, "
                      "magical forests with glowing trees, ancient castles in the background, "
                      "and mystical creatures wandering through the landscape")
        
        start_time = time.time()
        positive, negative, original = self.simulate_comfyui_execution(
            self.optimizer, "optimize_prompt",
            target_model="flux_dev", prompt=long_prompt,
            temperature=0.7, max_tokens_override=300
        )
        elapsed = time.time() - start_time
        
        # Verify handling of long prompts
        self.assertEqual(original, long_prompt)
        self.assertIsInstance(positive, str)
        
        # With longer input, output might be longer too
        print(f"✅ Long prompt optimization completed in {elapsed:.2f}s")
        print(f"   Input length: {len(long_prompt)} chars")
        print(f"   Output length: {len(positive)} chars")
        print(f"   Optimized: '{positive[:100]}...'")
    
    def test_performance_benchmarking_real_ollama(self):
        """Benchmark performance of real Ollama optimization"""
        test_cases = [
            "cat",
            "red sports car", 
            "mountain landscape at sunset",
            "futuristic robot in cyberpunk city with neon lights"
        ]
        
        results = []
        
        for i, prompt in enumerate(test_cases):
            start_time = time.time()
            
            positive, negative, original = self.simulate_comfyui_execution(
                self.optimizer, "optimize_prompt",
                target_model="flux_dev", prompt=prompt,
                temperature=0.7, seed=i
            )
            
            elapsed = time.time() - start_time
            results.append({
                'prompt': prompt,
                'input_len': len(prompt),
                'output_len': len(positive),
                'time': elapsed,
                'chars_per_sec': len(positive) / elapsed if elapsed > 0 else 0
            })
            
            print(f"   '{prompt}' -> {elapsed:.2f}s ({len(positive)} chars)")
        
        # Calculate averages
        avg_time = sum(r['time'] for r in results) / len(results)
        avg_chars_per_sec = sum(r['chars_per_sec'] for r in results) / len(results)
        
        print(f"✅ Performance benchmark completed")
        print(f"   Average time: {avg_time:.2f}s")
        print(f"   Average output rate: {avg_chars_per_sec:.1f} chars/sec")
        
        # Performance expectations (adjust based on system)
        self.assertLess(avg_time, 15.0, "Average optimization time should be reasonable")
        
        return results


class TestPromptOptimizerConfigurationIntegration(unittest.TestCase, MockComfyUINode):
    """Integration tests for configuration handling"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.context = self.setup_test_environment()
        self.context.__enter__()
        self.optimizer = PromptOptimizer()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.context.__exit__(None, None, None)
    
    def test_model_config_loading_integration(self):
        """Test that model configurations load correctly"""
        # Verify configurations loaded
        self.assertGreater(len(self.optimizer.model_configs), 0)
        
        # Check key models exist
        expected_models = ["flux_dev", "wan22", "chroma_hd"]
        for model in expected_models:
            with self.subTest(model=model):
                self.assertIn(model, self.optimizer.model_configs)
                config = self.optimizer.model_configs[model]
                
                # Verify required fields
                self.assertIn("name", config)
                self.assertIn("supports_negative", config)
                self.assertIn("positive_messages", config)
                
                # Verify message structure
                positive_messages = config["positive_messages"]
                self.assertIsInstance(positive_messages, list)
                if positive_messages:
                    self.assertEqual(positive_messages[0]["role"], "system")
        
        print(f"✅ Loaded {len(self.optimizer.model_configs)} model configurations")
        
        # Print available models
        model_names = list(self.optimizer.model_configs.keys())
        print(f"   Available models: {', '.join(model_names[:5])}...")
    
    def test_image_processing_integration(self):
        """Test image processing pipeline"""
        # Create test image in various formats
        test_cases = [
            ("uint8_batch", np.random.randint(0, 255, (1, 128, 128, 3), dtype=np.uint8)),
            ("float32_batch", np.random.rand(1, 128, 128, 3).astype(np.float32)),
            ("single_image", np.random.rand(128, 128, 3).astype(np.float32)),
        ]
        
        for case_name, image_array in test_cases:
            with self.subTest(case=case_name):
                # Convert to tensor
                if isinstance(image_array, np.ndarray):
                    image_tensor = torch.from_numpy(image_array)
                else:
                    image_tensor = image_array
                
                # Test image saving
                image_path = self.optimizer._save_image_for_ollama(image_tensor)
                
                # Verify file created
                self.assertIsNotNone(image_path)
                self.assertTrue(os.path.exists(image_path))
                self.assertTrue(image_path.endswith('.png'))
                
                # Verify image can be loaded
                saved_image = Image.open(image_path)
                self.assertEqual(saved_image.mode, 'RGB')
                self.assertEqual(len(saved_image.getbands()), 3)
                
                print(f"   {case_name}: saved {saved_image.size} image")
        
        # Clean up
        self.optimizer._cleanup_temp_images()
        
        print(f"✅ Image processing pipeline verified for {len(test_cases)} formats")


if __name__ == '__main__':
    # Run with verbose output  
    unittest.main(verbosity=2)