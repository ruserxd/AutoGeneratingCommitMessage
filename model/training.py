import json
from transformers import RobertaTokenizer, T5ForConditionalGeneration, Trainer, TrainingArguments, DataCollatorForSeq2Seq
from datasets import Dataset


tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
model = T5ForConditionalGeneration.from_pretrained('Salesforce/codet5-base')

json_file_path = 'Tavernari-git-commit-message-dt.json'  # 資料集
with open(json_file_path, 'r', encoding='utf-8') as f:
    training_data = json.load(f)

# 註解處理
def handle_comments(diff):
    lines = diff.split('\n')
    processed_lines = [line for line in lines if not line.strip().startswith('//')]
    return '\n'.join(processed_lines)

def preprocess(examples):
   
    processed_inputs = [handle_comments(item) for item in examples["input"]]
    inputs = tokenizer(processed_inputs, max_length=512, truncation=True, padding=True)

    commit_messages = [f"{output['commit_message']}\nWhy: {output['why']}" for output in examples["output"]]

    outputs = tokenizer(commit_messages, max_length=128, truncation=True, padding=True)
    inputs["labels"] = outputs["input_ids"]

    return inputs

dataset = Dataset.from_list(training_data).map(preprocess, batched=True)

# 訓練設定
training_args = TrainingArguments(
    output_dir="./commit-model",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=50,
    logging_steps=10
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)
)

trainer.train()
trainer.save_model("./commit-model")