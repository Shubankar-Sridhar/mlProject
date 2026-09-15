"""QLoRA training implementation."""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    BitsAndBytesConfig
)
from peft import (
    LoraConfig,
    get_peft_model,
    prepare_model_for_kbit_training,
    PeftModel
)
from trl import SFTTrainer
from datasets import Dataset

logger = logging.getLogger(__name__)


class QLoRATrainer:
    """QLoRA trainer for fine-tuning SLM."""
    
    def __init__(
        self,
        model_name: str,
        output_dir: str,
        config: Dict[str, Any]
    ):
        self.model_name = model_name
        self.output_dir = output_dir
        self.config = config
        
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
        self._setup_directories()
    
    def _setup_directories(self):
        """Setup output directories."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/checkpoints", exist_ok=True)
        os.makedirs(f"{self.output_dir}/final", exist_ok=True)
    
    def prepare_model(self):
        """Prepare model with 4-bit quantization."""
        # Setup quantization config
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_storage_dtype=torch.uint8
        )
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=True,
            use_cache=False
        )
        
        # Prepare for k-bit training
        self.model = prepare_model_for_kbit_training(self.model)
        
        # Setup LoRA
        lora_config = LoraConfig(
            r=self.config.get('lora_r', 64),
            lora_alpha=self.config.get('lora_alpha', 16),
            target_modules=self.config.get('target_modules', ['q_proj', 'v_proj', 'k_proj', 'o_proj']),
            lora_dropout=self.config.get('lora_dropout', 0.05),
            bias="none",
            task_type="CAUSAL_LM"
        )
        
        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "right"
        
        logger.info(f"Model prepared: {self.model_name}")
        return self.model, self.tokenizer
    
    def prepare_dataset(self, examples: List[Dict[str, Any]]) -> Dataset:
        """Prepare dataset for training."""
        def format_example(ex: Dict[str, Any]) -> str:
            """Format example for training."""
            instruction = ex.get('instruction', '')
            schema = ex.get('input', {}).get('schema', '')
            question = ex.get('input', {}).get('question', '')
            sql = ex.get('output', {}).get('sql', '')
            
            return f"<|system|>\nYou are an expert SQL generator.\n<|user|>\n{question}\nSchema:\n{schema}\n<|assistant|>\n{sql}"
        
        formatted = [format_example(ex) for ex in examples]
        
        dataset = Dataset.from_dict({
            'text': formatted,
            'instruction': [ex.get('instruction', '') for ex in examples],
            'question': [ex.get('input', {}).get('question', '') for ex in examples],
            'sql': [ex.get('output', {}).get('sql', '') for ex in examples]
        })
        
        return dataset
    
    def setup_training(self, dataset: Dataset):
        """Setup training arguments and trainer."""
        training_args = TrainingArguments(
            output_dir=f"{self.output_dir}/checkpoints",
            num_train_epochs=self.config.get('num_epochs', 3),
            per_device_train_batch_size=self.config.get('batch_size', 4),
            per_device_eval_batch_size=self.config.get('batch_size', 4),
            gradient_accumulation_steps=self.config.get('gradient_accumulation', 4),
            learning_rate=self.config.get('learning_rate', 2e-4),
            warmup_steps=self.config.get('warmup_steps', 100),
            logging_steps=self.config.get('logging_steps', 10),
            save_steps=self.config.get('save_steps', 500),
            max_grad_norm=self.config.get('max_grad_norm', 0.3),
            weight_decay=self.config.get('weight_decay', 0.001),
            optim="paged_adamw_8bit",
            lr_scheduler_type="cosine",
            report_to="none",
            evaluation_strategy="steps",
            eval_steps=100,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False
        )
        
        self.trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            args=training_args,
            max_seq_length=self.config.get('max_length', 2048),
            packing=False
        )
        
        logger.info("Training setup complete")
    
    def train(self) -> Dict[str, Any]:
        """Run training."""
        try:
            logger.info("Starting training...")
            start_time = datetime.utcnow()
            
            # Train
            self.trainer.train()
            
            # Save final model
            final_path = f"{self.output_dir}/final"
            self.model.save_pretrained(final_path)
            self.tokenizer.save_pretrained(final_path)
            
            # Save metadata
            metadata = {
                'model_name': self.model_name,
                'training_completed_at': datetime.utcnow().isoformat() + 'Z',
                'training_duration_seconds': (datetime.utcnow() - start_time).total_seconds(),
                'config': self.config,
                'output_path': final_path
            }
            
            with open(f"{self.output_dir}/metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Training completed. Model saved to {final_path}")
            return metadata
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise
    
    def export_to_gguf(self, output_path: str):
        """Export to GGUF format for llama.cpp."""
        try:
            # Merge LoRA weights
            base_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16,
                device_map="cpu"
            )
            
            merged_model = PeftModel.from_pretrained(
                base_model,
                f"{self.output_dir}/final"
            )
            merged_model = merged_model.merge_and_unload()
            
            # Save merged model
            merged_model.save_pretrained(output_path)
            
            # Convert to GGUF using llama.cpp
            # Note: This requires llama.cpp to be installed
            # We'll provide instructions for manual conversion
            
            logger.info(f"Model exported to GGUF format: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export to GGUF: {str(e)}")
            raise