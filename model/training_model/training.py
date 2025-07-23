import torch
from datasets import Dataset
from transformers import (
  T5ForConditionalGeneration,
  RobertaTokenizer,
  TrainingArguments,
  Trainer,
  EarlyStoppingCallback
)
import numpy as np
import json
import random
import os


# 設置GPU記憶體限制
def setup_gpu_limits():
  """設置GPU使用限制"""

  # 檢查是否有MPS支援（M1/M2/M3/M4 Mac）
  if torch.backends.mps.is_available():
    device = torch.device("mps")
    print("🎯 使用 MPS (Apple Silicon GPU)")

    # 設置MPS記憶體分配策略
    os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO'] = '0.7'  # 使用70%的GPU記憶體

    # 啟用記憶體效率模式
    torch.mps.empty_cache()  # 清空快取

  elif torch.cuda.is_available():
    device = torch.device("cuda")
    print("🎯 使用 CUDA GPU")

    # 設置CUDA記憶體限制（以GB為單位）
    torch.cuda.set_per_process_memory_fraction(0.7)  # 使用70%的GPU記憶體
    torch.cuda.empty_cache()

  else:
    device = torch.device("cpu")
    print("💻 使用 CPU")

  return device


model_path = "./commit-model"


class ValidationTrainer:
  def __init__(self, model_name='Salesforce/codet5-base'):
    self.model_name = model_name
    self.device = setup_gpu_limits()  # 設置GPU限制

    self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
    self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    # 將模型移到指定設備
    self.model = self.model.to(self.device)

    # 設置pad_token
    if self.tokenizer.pad_token is None:
      self.tokenizer.pad_token = self.tokenizer.eos_token

  # 訓練集 70% 驗證集 20% 測試集 10%
  def load_and_split_data(self, data_path, test_size=0.2, val_size=0.1):
    """載入數據並分割為訓練/驗證/測試集"""

    with open(data_path, 'r', encoding='utf-8') as f:
      data = json.load(f)

    # 實現數據分割
    random.seed(42)  # 固定隨機種子
    data_shuffled = data.copy()
    random.shuffle(data_shuffled)

    total_size = len(data_shuffled)
    test_count = int(total_size * test_size)
    val_count = int(total_size * val_size)

    # 分割數據
    test_data = data_shuffled[:test_count]
    val_data = data_shuffled[test_count:test_count + val_count]
    train_data = data_shuffled[test_count + val_count:]

    print(f"📊 數據分割結果:")
    print(f"  訓練集: {len(train_data)} 筆")
    print(f"  驗證集: {len(val_data)} 筆")
    print(f"  測試集: {len(test_data)} 筆")

    return train_data, val_data, test_data

  def preprocess_data(self, data, max_input_length=512, max_target_length=128):
    """預處理數據"""

    def tokenize_function(examples):
      inputs = examples['input']
      targets = examples['output']

      # Tokenize輸入
      model_inputs = self.tokenizer(
          inputs,
          max_length=max_input_length,
          padding='max_length',
          truncation=True,
          return_tensors=None
      )

      # Tokenize標籤
      with self.tokenizer.as_target_tokenizer():
        labels = self.tokenizer(
            targets,
            max_length=max_target_length,
            padding='max_length',
            truncation=True,
            return_tensors=None
        )

      model_inputs["labels"] = labels["input_ids"]
      return model_inputs

    # 轉換為Dataset格式
    dataset = Dataset.from_list(data)

    # 應用tokenization
    tokenized_dataset = dataset.map(
        tokenize_function,
        batched=True,
        remove_columns=dataset.column_names
    )

    return tokenized_dataset

  def compute_metrics(self, eval_pred):
    """計算評估指標"""
    predictions, labels = eval_pred

    if isinstance(predictions, tuple):
      predictions = predictions[0]  # 取第一個元素（logits）

    # 確保 predictions 是 numpy array
    if hasattr(predictions, 'cpu'):
      predictions = predictions.cpu().numpy()
    elif not isinstance(predictions, np.ndarray):
      predictions = np.array(predictions)

    # 處理預測結果的argmax
    if predictions.ndim == 3:
      predictions = np.argmax(predictions, axis=-1)

    # 解碼預測結果
    decoded_preds = self.tokenizer.batch_decode(
        predictions,
        skip_special_tokens=True
    )

    # 處理標籤（替換-100為pad_token_id）
    labels = np.where(labels != -100, labels, self.tokenizer.pad_token_id)
    decoded_labels = self.tokenizer.batch_decode(
        labels,
        skip_special_tokens=True
    )

    # 計算BLEU分數
    try:
      from nltk.translate.bleu_score import sentence_bleu

      bleu_scores = []
      for pred, label in zip(decoded_preds, decoded_labels):
        pred_tokens = pred.split()
        label_tokens = label.split()

        if len(label_tokens) == 0:
          score = 0.0
        else:
          score = sentence_bleu(
              [label_tokens],
              pred_tokens,
              weights=(1, 0, 0, 0)  # 只計算1-gram
          )
        bleu_scores.append(score)

      return {
        'bleu': np.mean(bleu_scores),
        'avg_length': np.mean([len(pred.split()) for pred in decoded_preds])
      }
    except ImportError:
      overlap_scores = []
      for pred, label in zip(decoded_preds, decoded_labels):
        pred_words = set(pred.split())
        label_words = set(label.split())
        if len(label_words) > 0:
          overlap = len(pred_words & label_words) / len(label_words)
        else:
          overlap = 0
        overlap_scores.append(overlap)

      return {
        'word_overlap': np.mean(overlap_scores),
        'avg_length': np.mean([len(pred.split()) for pred in decoded_preds])
      }

  def train_with_validation(self, train_data, val_data, output_dir=model_path):
    """使用驗證集進行訓練"""

    # 預處理數據
    train_dataset = self.preprocess_data(train_data)
    val_dataset = self.preprocess_data(val_data)

    # 設定訓練參數 - 針對M4 Pro優化
    training_args = TrainingArguments(
        output_dir=output_dir,

        # 基本參數 - 降低batch size以節省記憶體
        num_train_epochs=10,
        per_device_train_batch_size=1,  # 從2降到1
        per_device_eval_batch_size=1,  # 從2降到1
        gradient_accumulation_steps=4,  # 從2增加到4來補償batch size減少

        # 學習率和優化器
        learning_rate=5e-5,
        warmup_steps=100,
        weight_decay=0.01,

        # 評估和保存
        eval_strategy="steps",
        eval_steps=100,  # 增加評估間隔
        save_strategy="steps",
        save_steps=100,  # 增加保存間隔
        save_total_limit=2,  # 減少保存的checkpoint數量

        # 監控和日誌
        logging_dir=f'{output_dir}/logs',
        logging_steps=25,
        report_to="none",

        # Early stopping
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,

        # 記憶體優化設置
        dataloader_pin_memory=False,
        remove_unused_columns=True,  # 移除不使用的欄位
        fp16=False,  # M4 Pro使用MPS時建議關閉fp16
        dataloader_num_workers=0,  # 設為0避免多進程問題

        # 梯度檢查點以節省記憶體
        gradient_checkpointing=True,
    )

    # 創建Trainer
    trainer = Trainer(
        model=self.model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        tokenizer=self.tokenizer,
        compute_metrics=self.compute_metrics,
        callbacks=[
          EarlyStoppingCallback(
              early_stopping_patience=5,  # 增加patience
              early_stopping_threshold=0.01
          )
        ]
    )

    # 開始訓練
    print("🚀 開始訓練（含驗證）...")
    print(f"💾 使用設備: {self.device}")

    # 定期清理記憶體
    def cleanup_memory():
      if self.device.type == "mps":
        torch.mps.empty_cache()
      elif self.device.type == "cuda":
        torch.cuda.empty_cache()

    trainer.train()
    cleanup_memory()  # 訓練完成後清理記憶體

    # 保存最終模型
    trainer.save_model()
    self.tokenizer.save_pretrained(output_dir)

    # 返回訓練歷史
    return trainer.state.log_history

  def evaluate_model(self, test_data, model_path=model_path):
    """在測試集上評估模型"""

    # 載入訓練好的模型
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    model = model.to(self.device)
    model.eval()

    test_dataset = self.preprocess_data(test_data)

    # 創建評估trainer
    trainer = Trainer(
        model=model,
        tokenizer=self.tokenizer,
        compute_metrics=self.compute_metrics
    )

    # 評估
    print("📊 在測試集上評估...")
    results = trainer.evaluate(test_dataset)

    print(f"測試集結果:")
    for key, value in results.items():
      print(f"  {key}: {value:.4f}")

    return results

  def plot_training_curves(self, log_history):
    """繪製訓練曲線"""
    import matplotlib.pyplot as plt

    # 提取訓練和驗證loss
    train_losses = []
    val_losses = []
    train_steps = []
    val_steps = []

    for log in log_history:
      if 'loss' in log and 'step' in log:
        train_losses.append(log['loss'])
        train_steps.append(log['step'])
      if 'eval_loss' in log and 'step' in log:
        val_losses.append(log['eval_loss'])
        val_steps.append(log['step'])

    # 繪製圖表
    plt.figure(figsize=(12, 4))

    # 訓練loss
    plt.subplot(1, 2, 1)
    if train_losses:
      plt.plot(train_steps, train_losses, label='Training Loss')
      plt.xlabel('Steps')
      plt.ylabel('Loss')
      plt.title('Training Loss')
      plt.legend()

    # 驗證loss
    plt.subplot(1, 2, 2)
    if val_losses:
      plt.plot(val_steps, val_losses, label='Validation Loss', color='orange')
      plt.xlabel('Steps')
      plt.ylabel('Loss')
      plt.title('Validation Loss')
      plt.legend()

    plt.tight_layout()
    plt.savefig('./training_curves.png')
    plt.show()

  def generate_commit_message(self, diff_text, model_path=model_path):
    """生成commit message"""

    # 載入模型
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    model = model.to(self.device)
    model.eval()

    # 預處理輸入
    inputs = self.tokenizer(
        diff_text,
        max_length=512,
        padding='max_length',
        truncation=True,
        return_tensors='pt'
    )

    # 將輸入移到正確的設備
    inputs = {k: v.to(self.device) for k, v in inputs.items()}

    # 生成輸出
    with torch.no_grad():
      outputs = model.generate(
          inputs['input_ids'],
          attention_mask=inputs['attention_mask'],
          max_length=128,
          num_beams=4,
          temperature=0.7,
          do_sample=True,
          pad_token_id=self.tokenizer.pad_token_id
      )

    # 解碼結果
    commit_message = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
    return commit_message


def monitor_memory_usage():
  """監控記憶體使用情況"""
  if torch.backends.mps.is_available():
    # M4 Pro記憶體監控
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    print(f"💾 RAM使用量: {memory_info.rss / 1024 / 1024 / 1024:.2f} GB")

    # MPS沒有直接的記憶體查詢API，但可以通過系統監控
    torch.mps.empty_cache()

  elif torch.cuda.is_available():
    allocated = torch.cuda.memory_allocated() / 1024 ** 3
    cached = torch.cuda.memory_reserved() / 1024 ** 3
    print(f"💾 GPU記憶體 - 已分配: {allocated:.2f} GB, 快取: {cached:.2f} GB")


def main():
  # 創建訓練器
  trainer = ValidationTrainer()

  # 監控初始記憶體使用
  print("🔍 初始記憶體狀態:")
  monitor_memory_usage()

  # 載入和分割數據
  train_data, val_data, test_data = trainer.load_and_split_data(
      "spider-data/training-data/spring-boot/spring-boot-training.json"
  )

  # 訓練模型
  print("\n🔍 訓練前記憶體狀態:")
  monitor_memory_usage()

  log_history = trainer.train_with_validation(train_data, val_data)

  print("\n🔍 訓練後記憶體狀態:")
  monitor_memory_usage()

  # 繪製訓練曲線
  trainer.plot_training_curves(log_history)

  # 在測試集上評估
  trainer.evaluate_model(test_data)

  print("\n🔍 最終記憶體狀態:")
  monitor_memory_usage()


if __name__ == "__main__":
  main()