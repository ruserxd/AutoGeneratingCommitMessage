import json
import torch
import warnings
from transformers import RobertaTokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset

warnings.filterwarnings("ignore")

def main():
    # 檢查並設定 GPU
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"使用設備: {device}")
    if torch.cuda.is_available():
        print(f"GPU 名稱: {torch.cuda.get_device_name(0)}")
        print(f"GPU 記憶體: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        print("警告：未偵測到 GPU，將使用 CPU 訓練")

    # 初始化 tokenizer 和模型
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    model = T5ForConditionalGeneration.from_pretrained('Salesforce/codet5-base')
    model = model.to(device)

    # 指定資料路徑
    json_file_path = './Tavernari-git-commit-message-dt/Tavernari-git-commit-message-dt_commit_message.json'

    # 讀取 JSON 檔案
    with open(json_file_path, 'r', encoding='utf-8') as f:
        training_data = json.load(f)

    print(f"📊 原始資料: {len(training_data)} 筆")

    # 顯示前幾筆資料
    for i, item in enumerate(training_data[:3]):
        print(f"第{i+1}筆:")
        print(f"  Input: {item['input'][:100]}...")
        print(f"  Output: {item['output']}")

    # 註解處理函數
    def handle_comments(diff):
        lines = diff.split('\n')
        processed_lines = [line for line in lines if not line.strip().startswith('//')]
        return '\n'.join(processed_lines)

    def preprocess(examples):
        """完全修正的預處理函數"""
        
        # 處理 input
        processed_inputs = [handle_comments(item) for item in examples["input"]]
        
        # Tokenize inputs
        model_inputs = tokenizer(
            processed_inputs,
            max_length=256,
            truncation=True,
            padding=True
        )
        
        # Tokenize targets
        labels = tokenizer(
            examples["output"],
            max_length=64,
            truncation=True,
            padding=True
        )
        
        # 設定 labels
        label_ids = []
        for label_seq in labels["input_ids"]:
            label_with_ignore = [
                -100 if token == tokenizer.pad_token_id else token 
                for token in label_seq
            ]
            label_ids.append(label_with_ignore)
        
        model_inputs["labels"] = label_ids
        return model_inputs

    # 建立資料集
    print(f"\n🔄 預處理資料...")
    dataset = Dataset.from_list(training_data).map(preprocess, batched=True)
    
    # 檢查第一筆處理後的資料
    sample = dataset[0]
    print(f"\n🔍 第一筆處理後的資料:")
    print(f"Input IDs length: {len(sample['input_ids'])}")
    print(f"Labels length: {len(sample['labels'])}")
    print(f"Input text: {tokenizer.decode(sample['input_ids'], skip_special_tokens=True)[:100]}...")
    
    # 解碼 labels（排除 -100）
    valid_labels = [t for t in sample['labels'] if t != -100]
    print(f"Label text: {tokenizer.decode(valid_labels, skip_special_tokens=True)}")

    # 訓練設定
    training_args = TrainingArguments(
        output_dir="./commit-model",
        num_train_epochs=2,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=2,
        save_steps=50,
        logging_steps=5,
        save_total_limit=2,
        load_best_model_at_end=False,
        
        # 學習率設定
        learning_rate=5e-5,
        warmup_steps=10,
        
        # 資料載入設定
        dataloader_num_workers=0,
        dataloader_pin_memory=False,
        
        # GPU 優化
        fp16=torch.cuda.is_available(),
        no_cuda=False,
        
        # 其他設定
        weight_decay=0.01,
        logging_dir='./logs',
        report_to=None,
    )

    # 資料整理器
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        padding=True
    )

    # 建立訓練器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=data_collator
    )

    # 開始訓練
    print(f"\n🚀 開始訓練...")
    print(f"資料集大小: {len(training_data)} 筆")
    print(f"批次大小: {training_args.per_device_train_batch_size}")
    print(f"梯度累積: {training_args.gradient_accumulation_steps}")
    print(f"有效批次大小: {training_args.per_device_train_batch_size * training_args.gradient_accumulation_steps}")

    # 訓練
    train_result = trainer.train()
    
    print(f"\n📊 訓練結果:")
    print(f"最終 Loss: {train_result.training_loss:.4f}")

    # 保存模型
    trainer.save_model("./commit-model")
    tokenizer.save_pretrained("./commit-model")

    print(f"\n✅ 訓練完成！模型已保存到 ./commit-model")

if __name__ == '__main__':
    main()