from transformers import T5ForConditionalGeneration, RobertaTokenizer

# 翻譯與模型
tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
model = T5ForConditionalGeneration.from_pretrained("commit-model")

# 使用訓練好的模型
text = ""
input_ids = tokenizer(text, return_tensors="pt").input_ids
output = model.generate(input_ids, max_length=50)
print(tokenizer.decode(output[0], skip_special_tokens=True))