from transformers import T5ForConditionalGeneration, RobertaTokenizer
import torch
import string_formatter


def test_different_temperatures():
  """測試不同溫度參數的效果"""

  # 載入模型
  model_path = "commit-model-ep8-ba4-le1e-10000dt"
  tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
  model = T5ForConditionalGeneration.from_pretrained(model_path)
  model.eval()

  if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.pad_token_id = tokenizer.eos_token_id

  # 測試用的 diff
  test_diff_remove = """
    diff --git a/Car.java b/Car.java
    index 5aa7953..c0cd4ed 100644
    --- a/Car.java
    +++ b/Car.java
    @@ -1,7 +1,7 @@
    public class Car {
    -    String name;
    }
    """

  test_diff_rename = """
  diff --git a/Car.java b/Car.java
  index 5aa7953..c0cd4ed 100644
  --- a/Car.java
  +++ b/Car.java
  @@ -1,7 +1,7 @@
  public class Car {
  -    String name;
  +    String car_name;
  }
  """

  test_diff_add = """
    diff --git a/Car.java b/Car.java
    index 218bbe3..0972a20 100644
    --- a/Car.java
    +++ b/Car.java
    @@ -1,3 +1,35 @@
    public class Car {
    +    String id;
    +
    +    public Car(String id) {
    +        this.id = id;
    +    }
    +
    +    public String getId() {
    +        return id;
    +    }
    """

  # 清理 diff
  cleaned_diff = string_formatter.clean_text(test_diff_add)

  # 🔍 診斷輸入內容
  print("🔍 診斷輸入內容:")
  print("=" * 60)
  print(f"📝 原始 diff 長度: {len(test_diff_add)}")
  print(f"🧹 清理後長度: {len(cleaned_diff)}")
  print(f"🔤 清理後內容:\n{cleaned_diff}")
  print("=" * 60)

  # 溫度參數
  temperatures = [0.2, 0.4]

  # Tokenize 一次就好
  inputs = tokenizer(
      cleaned_diff,
      return_tensors="pt",
      max_length=512,
      truncation=True,
      padding=True
  )

  results = []

  for temp in temperatures:
    print(f"\n🌡️ 溫度: {temp}")

    # 生成多次看變化
    messages = []
    for i in range(3):  # 每個溫度生成3次
      with torch.no_grad():
        output = model.generate(
            inputs.input_ids,
            max_length=512,
            temperature=temp,
            do_sample=True,
            top_p=0.9,
            repetition_penalty=1.2,
            pad_token_id=tokenizer.pad_token_id,
        )

      # 解碼
      decoded = tokenizer.decode(output[0], skip_special_tokens=True)
      messages.append(decoded.strip())

    # 顯示結果
    for i, msg in enumerate(messages, 1):
      print(f"  第{i}次: '{msg}'")

    results.append({
      'temperature': temp,
      'messages': messages
    })

if __name__ == "__main__":
  test_different_temperatures()
