import os
import time
import glob
from datetime import datetime

# 設置 multiprocessing 啟動方法
import multiprocessing as mp
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    pass

import torch
import json
import random
import logging
import wandb
from datasets import Dataset
from transformers import (
    T5ForConditionalGeneration,
    RobertaTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForSeq2Seq,
)

# 禁用 tokenizers 並行處理
os.environ["TOKENIZERS_PARALLELISM"] = "false"

class FixedT5Trainer:
    def __init__(self):
        self.setup_logging()
        self.load_config()
        self.setup_device()
        self.setup_wandb()
        self.log_initial_info()
        self.load_model()

    def setup_logging(self):
        """設置簡化日誌"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            force=True
        )
        self.logger = logging.getLogger(__name__)
        print("=" * 60)
        print("🚀 修復版 GPU 訓練開始")
        print("=" * 60)

    def load_config(self):
        """載入配置"""
        self.model_name = os.getenv('MODEL_NAME', 'Salesforce/codet5-base')
        self.max_input_length = int(os.getenv('MAX_INPUT_LENGTH', '512'))
        self.max_output_length = int(os.getenv('MAX_OUTPUT_LENGTH', '128'))

        # 批次大小設置
        self.batch_size = int(os.getenv('BATCH_SIZE', '4'))
        self.gradient_accumulation_steps = int(os.getenv('GRAD_ACCUM', '8'))

        # 學習率設置
        self.learning_rate = float(os.getenv('LEARNING_RATE', '1e-4'))
        self.epochs = int(os.getenv('EPOCHS', '8'))
        self.warmup_ratio = float(os.getenv('WARMUP_RATIO', '0.1'))

        self.output_dir = os.getenv('OUTPUT_DIR', './commit-model')

        self.config_info = {
            "model": self.model_name,
            "max_input_length": self.max_input_length,
            "max_output_length": self.max_output_length,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "effective_batch_size": self.batch_size * self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "warmup_ratio": self.warmup_ratio,
            "output_dir": self.output_dir
        }

        print("📋 修復版配置參數:")
        print(f"  模型: {self.model_name}")
        print(f"  有效批次大小: {self.batch_size * self.gradient_accumulation_steps}")
        print(f"  學習率: {self.learning_rate}")
        print(f"  訓練輪數: {self.epochs}")

    def setup_device(self):
        """設置設備並處理 CUDA 初始化"""
        # 更安全的 CUDA 初始化
        if torch.cuda.is_available():
            try:
                self.device = torch.device("cuda")
                gpu_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3

                self.device_info = {
                    "device": str(self.device),
                    "gpu_name": gpu_name,
                    "gpu_memory_gb": round(gpu_memory, 1)
                }

                print(f"🚀 GPU: {gpu_name} ({gpu_memory:.1f} GB)")

                # 更保守的記憶體管理
                torch.cuda.empty_cache()
                torch.cuda.set_per_process_memory_fraction(0.8)

            except Exception as e:
                print(f"⚠️ CUDA 初始化問題: {e}")
                self.device = torch.device("cpu")
                self.device_info = {"device": "cpu", "cuda_error": str(e)}
        else:
            self.device = torch.device("cpu")
            self.device_info = {"device": "cpu"}
            print("⚠️ 使用 CPU")

    def setup_wandb(self):
        """初始化 WandB"""
        try:
            wandb.init(
                project="commit-message-generator-fixed",
                name=f"fixed-t5-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                config=self.config_info
            )
            print("📊 WandB 初始化完成")
        except Exception as e:
            print(f"⚠️ WandB 初始化失敗: {e}")

    def log_initial_info(self):
        """記錄初始化資訊"""
        try:
            wandb.log({"status": "initialization_complete"})
            wandb.log({"config": self.config_info})
            wandb.log({"device_info": self.device_info})
        except:
            pass  # WandB 記錄失敗不影響訓練

    def load_model(self):
        """載入模型"""
        print(f"🔄 載入模型: {self.model_name}")
        start_time = time.time()

        try:
            self.tokenizer = RobertaTokenizer.from_pretrained(self.model_name)

            # 更安全的模型載入
            if self.device.type == 'cuda':
                try:
                    self.model = T5ForConditionalGeneration.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float32
                    ).to(self.device)
                except Exception as e:
                    print(f"⚠️ GPU 載入失敗，改用 CPU: {e}")
                    self.device = torch.device("cpu")
                    self.model = T5ForConditionalGeneration.from_pretrained(
                        self.model_name,
                        torch_dtype=torch.float32
                    )
            else:
                self.model = T5ForConditionalGeneration.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float32
                )

            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

            load_time = time.time() - start_time
            print(f"✅ 模型載入完成 ({load_time:.2f}s)")

        except Exception as e:
            print(f"❌ 模型載入失敗: {e}")
            raise

    def get_training_data_paths(self, data_directory="training-data"):
        """獲取訓練數據路徑"""
        pattern = os.path.join(data_directory, "*.json")
        data_paths = glob.glob(pattern)

        if not data_paths:
            print(f"⚠️ 在 {data_directory} 目錄中未找到 JSON 文件")
            return []

        data_paths.sort()
        print(f"📂 發現 {len(data_paths)} 個訓練文件")
        return data_paths

    def analyze_and_filter_data(self, data, data_type="資料"):
        """分析並過濾數據質量"""
        print(f"🔍 分析{data_type}質量...")

        filtered_data = []
        stats = {
            "total": len(data),
            "too_short_input": 0,
            "too_long_input": 0,
            "too_short_output": 0,
            "too_long_output": 0,
            "valid": 0
        }

        for item in data:
            try:
                if not isinstance(item, dict) or 'input' not in item or 'output' not in item:
                    continue

                input_text = str(item['input']).strip()
                output_text = str(item['output']).strip()

                input_len = len(input_text.split())
                output_len = len(output_text.split())

                # 過濾條件
                if input_len < 10:
                    stats["too_short_input"] += 1
                    continue
                if input_len > 200:
                    stats["too_long_input"] += 1
                    continue
                if output_len < 3:
                    stats["too_short_output"] += 1
                    continue
                if output_len > 50:
                    stats["too_long_output"] += 1
                    continue

                filtered_data.append({
                    'input_text': input_text,
                    'target_text': output_text
                })
                stats["valid"] += 1

            except Exception as e:
                continue

        print(f"📊 {data_type}過濾統計:")
        print(f"  總數: {stats['total']}")
        print(f"  有效: {stats['valid']}")

        try:
            wandb.log({f"{data_type}_filter_stats": stats})
        except:
            pass

        return filtered_data

    def load_data(self, data_paths):
        """載入資料"""
        print("📂 載入資料...")
        all_data = []

        for path in data_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                all_data.extend(data)
                print(f"✅ {os.path.basename(path)}: {len(data):,} 筆")
            except Exception as e:
                print(f"❌ 載入失敗 {path}: {e}")

        random.seed(42)
        random.shuffle(all_data)

        total = len(all_data)
        train_size = int(total * 0.85)
        train_data = all_data[:train_size]
        val_data = all_data[train_size:]

        print(f"📊 數據分割: 訓練 {len(train_data):,} / 驗證 {len(val_data):,}")
        return train_data, val_data

    def preprocess_data(self, data, data_type="資料"):
        """修復版資料預處理"""
        print(f"🔄 預處理{data_type}...")

        processed_data = self.analyze_and_filter_data(data, data_type)

        if not processed_data:
            raise ValueError(f"沒有有效的{data_type}")

        def tokenize_function(examples):
            inputs = examples['input_text']
            targets = examples['target_text']

            model_inputs = self.tokenizer(
                inputs,
                max_length=self.max_input_length,
                padding=False,
                truncation=True,
                return_tensors=None
            )

            with self.tokenizer.as_target_tokenizer():
                labels = self.tokenizer(
                    targets,
                    max_length=self.max_output_length,
                    padding=False,
                    truncation=True,
                    return_tensors=None
                )

            model_inputs["labels"] = labels["input_ids"]
            return model_inputs

        dataset = Dataset.from_list(processed_data)

        # 禁用多進程處理避免 CUDA 錯誤
        print(f"🔧 使用單進程 tokenization (修復 CUDA multiprocessing 問題)")
        tokenized_dataset = dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=dataset.column_names,
            desc=f"Tokenizing {data_type}",
            num_proc=None  # 禁用多進程
        )

        return tokenized_dataset

    def train(self, data_directory="training-data"):
        """修復版訓練流程"""
        print("🚀 開始修復版訓練...")
        training_start_time = time.time()

        try:
            data_paths = self.get_training_data_paths(data_directory)
            if not data_paths:
                raise ValueError("未找到訓練數據")

            train_data, val_data = self.load_data(data_paths)
            train_dataset = self.preprocess_data(train_data, "訓練資料")
            val_dataset = self.preprocess_data(val_data, "驗證資料") if val_data else None

            data_collator = DataCollatorForSeq2Seq(
                tokenizer=self.tokenizer,
                model=self.model,
                padding=True,
                return_tensors="pt"
            )

            total_steps = (len(train_dataset) // (self.batch_size * self.gradient_accumulation_steps)) * self.epochs
            warmup_steps = int(total_steps * self.warmup_ratio)

            print(f"📈 訓練步數: {total_steps}")
            print(f"🔥 Warmup 步數: {warmup_steps}")

            # 修復版訓練參數
            training_args = TrainingArguments(
                output_dir=self.output_dir,
                num_train_epochs=self.epochs,

                # 批次設置
                per_device_train_batch_size=self.batch_size,
                per_device_eval_batch_size=self.batch_size,
                gradient_accumulation_steps=self.gradient_accumulation_steps,

                # 學習率設置
                learning_rate=self.learning_rate,
                lr_scheduler_type="cosine",
                warmup_steps=warmup_steps,
                weight_decay=0.01,

                # 更保守的並行設置
                fp16=False,  # 暫時禁用混合精度避免問題
                bf16=False,

                # 禁用所有多進程功能
                max_grad_norm=1.0,
                dataloader_num_workers=0,  # 禁用多進程
                dataloader_pin_memory=False,  # 禁用 pin memory

                # 評估和保存
                eval_strategy="steps" if val_dataset else "no",
                eval_steps=100 if val_dataset else None,
                save_steps=200,
                logging_steps=25,

                # 模型保存
                save_total_limit=3,
                load_best_model_at_end=True if val_dataset else False,
                metric_for_best_model="eval_loss" if val_dataset else None,
                greater_is_better=False,

                # 其他設置
                remove_unused_columns=True,
                prediction_loss_only=True,
                seed=42,
                report_to="wandb" if wandb.run else None,
                logging_dir=f"{self.output_dir}/logs",
                run_name=f"fixed-training-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )

            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=train_dataset,
                eval_dataset=val_dataset,
                data_collator=data_collator,
                tokenizer=self.tokenizer,
            )

            print("🎯 開始訓練...")
            train_result = trainer.train()
            training_time = time.time() - training_start_time

            print(f"🎉 訓練完成! 耗時: {training_time:.2f} 秒")

            # 保存模型
            trainer.save_model()
            self.tokenizer.save_pretrained(self.output_dir)
            print(f"✅ 模型已保存: {self.output_dir}")

            # 記錄結果
            try:
                final_results = {
                    "training_time": training_time,
                    "final_loss": getattr(train_result, 'training_loss', None),
                    "total_steps": total_steps,
                    "model_saved": True
                }
                wandb.log({"final_results": final_results})
            except:
                pass

        except Exception as e:
            print(f"❌ 訓練錯誤: {e}")
            try:
                wandb.log({"training_error": str(e)})
            except:
                pass
            raise
        finally:
            try:
                wandb.finish()
            except:
                pass

def main():
    """主函數"""
    try:
        trainer = FixedT5Trainer()
        trainer.train(data_directory="training-data")
        print("✅ 修復版訓練完成!")

    except Exception as e:
        print(f"❌ 訓練失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()