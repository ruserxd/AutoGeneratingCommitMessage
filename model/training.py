from transformers import RobertaTokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset

# 翻譯與模型
tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
model = T5ForConditionalGeneration.from_pretrained('Salesforce/codet5-base')

training_data = [
]


# 準備資料
def preprocess(examples):
    # 處理輸入
    inputs = tokenizer(examples["input"], max_length=512, truncation=True, padding=True)
    
    commit_messages = [item["commit_message"] for item in examples["output"]]
    outputs = tokenizer(commit_messages, max_length=128, truncation=True, padding=True)
    
    inputs["labels"] = outputs["input_ids"]
    return inputs

dataset = Dataset.from_list(training_data).map(preprocess, batched=True)

# 訓練設定
training_args = TrainingArguments(
    output_dir="./commit-model",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=50
)

# 開始訓練
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
)

trainer.train()  
trainer.save_model("./commit-model")