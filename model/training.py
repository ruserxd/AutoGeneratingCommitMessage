import json
import torch
from transformers import RobertaTokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset

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

    # 將模型移至 GPU
    model = model.to(device)

    # 指定資料路徑
    json_file_path = './spider-data/training-data/spring-projects_spring-boot_20250713_235938.json'

    # 讀取 JSON 檔案
    with open(json_file_path, 'r', encoding='utf-8') as f:
        training_data = json.load(f)

    # 註解處理函數
    def handle_comments(diff):
        lines = diff.split('\n')
        processed_lines = [line for line in lines if not line.strip().startswith('//')]
        return '\n'.join(processed_lines)

    # 預處理函數
    def preprocess(examples):
        # 處理 input 欄位
        processed_inputs = [handle_comments(item) for item in examples["input"]]
        inputs = tokenizer(processed_inputs, max_length=512, truncation=True, padding=True)
        
        # 處理 output 欄位 - 現在是字串而不是字典
        outputs = tokenizer(examples["output"], max_length=128, truncation=True, padding=True)
        inputs["labels"] = outputs["input_ids"]
        
        return inputs

    # 建立資料集
    dataset = Dataset.from_list(training_data).map(preprocess, batched=True)

    # 訓練設定
    training_args = TrainingArguments(
        output_dir="./commit-model",
        num_train_epochs=3,
        per_device_train_batch_size=4,
        save_steps=50,
        logging_steps=10,
        save_total_limit=2,
        load_best_model_at_end=False,
        
        # 安全使用多進程
        dataloader_num_workers=2,
        dataloader_pin_memory=True,
        
        # GPU 優化
        fp16=torch.cuda.is_available(),
        no_cuda=False,
    )

    # 建立訓練器
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
    )

    # 開始訓練
    print(f"開始訓練，使用資料集: {json_file_path}")
    print(f"資料集大小: {len(training_data)} 筆")
    print(f"訓練設備: {device}")

    trainer.train()

    # 保存模型
    trainer.save_model("./commit-model")
    tokenizer.save_pretrained("./commit-model")

    print("訓練完成！模型已保存到 ./commit-model")

if __name__ == '__main__':
    main()