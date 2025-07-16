from transformers import T5ForConditionalGeneration, RobertaTokenizer
import torch
import string_formatter

def test_model():
    """測試模型生成功能"""    
    model_path = "./commit-model"
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    model.eval()
    
    # 測試用的 diff
    text = """
        diff --git a/Car.java b/Car.java
        index 218bbe3..0972a20 100644
        --- a/Car.java
        +++ b/Car.java
        @@ -1,3 +1,35 @@
        public class Car {
        +    String id;
        +    String name;
        +    String year;

        +    public Car(String id, String name, String year) {
        +        this.id = id;
        +        this.name = name;
        +        this.year = year;
        +    }
        +
        +    public String getId() {
        +        return id;
        +    }
        +
        +    public void setId(String id) {
        +        this.id = id;
        +    }
        +
        +    public String getName() {
        +        return name;
        +    }
        +
        +    public void setName(String name) {
        +        this.name = name;
        +    }
        +
        +    public String getYear() {
        +        return year;
        +    }
        +
        +    public void setYear(String year) {
        +        this.year = year;
        +    }
        }
        \ No newline at end of file
        diff --git a/People.java b/People.java
        new file mode 100644
        index 0000000..1177eb8
        --- /dev/null
        +++ b/People.java
        @@ -0,0 +1,35 @@
        +public class People {
        +  String id;
        +  String name;
        +  String birthday;
        +
        +  public People(String id, String name, String birthday) {
        +    this.id = id;
        +    this.name = name;
        +    this.birthday = birthday;
        +  }
        +
        +  public String getId() {
        +    return id;
        +  }
        +
        +  public String getName() {
        +    return name;
        +  }
        +
        +  public String getBirthday() {
        +    return birthday;
        +  }
        +
        +  public void setId(String id) {
        +    this.id = id;
        +  }
        +
        +  public void setName(String name) {
        +    this.name = name;
        +  }
        +
        +  public void setBirthday(String birthday) {
        +    this.birthday = birthday;
        +  }
        +}
        diff --git a/Shop.java b/Shop.java
        new file mode 100644
        index 0000000..5b70055
        --- /dev/null
        +++ b/Shop.java
        @@ -0,0 +1,25 @@
        +public class Shop {
        +  String id;
        +  String name;
        +
        +  public Shop(String id, String name) {
        +    this.id = id;
        +    this.name = name;
        +  }
        +
        +  public String getId() {
        +    return id;
        +  }
        +
        +  public String getName() {
        +    return name;
        +  }
        +
        +  public void setId(String id) {
        +    this.id = id;
        +  }
        +
        +  public void setName(String name) {
        +    this.name = name;
        +  }
        +}"""

    test_diff = string_formatter.clean_text(text)

    print(f"📝 測試輸入:")
    print(test_diff[:200] + "..." if len(test_diff) > 200 else test_diff)
    
    # Tokenization
    inputs = tokenizer(
        test_diff,
        return_tensors="pt",
        max_length=256,  # 縮短長度
        truncation=True,
        padding=True
    )
    
    print(f"🔢 Input tokens: {inputs.input_ids.shape}")
    print(f"🔢 First few tokens: {inputs.input_ids[0][:10]}")
    
    # 生成
    with torch.no_grad():
        output = model.generate(
            inputs.input_ids,
            max_length=25,              # 限制長度
            no_repeat_ngram_size=3,     # 防止3-gram重複
            repetition_penalty=1.3,     # 重複懲罰
            do_sample=True,             # 啟用採樣
            temperature=0.8,            # 降低確定性
            top_p=0.9,                  # top-p採樣
            pad_token_id=tokenizer.pad_token_id,
        )
    
    print(f"🔢 Output tokens: {output.shape}")
    print(f"🔢 Output token ids: {output[0]}")
    
    # 解碼
    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
    
    print(f"\n🎯 模型生成結果:")
    print(f"'{decoded_output}'")
    
    return True

def diagnose_tokenizer():
    """診斷 tokenizer 問題"""
    
    print("\n🔍 診斷 tokenizer...")
    
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    
    # 檢查特殊 tokens
    print(f"Vocab size: {tokenizer.vocab_size}")
    print(f"PAD token: {tokenizer.pad_token} (id: {tokenizer.pad_token_id})")
    print(f"EOS token: {tokenizer.eos_token} (id: {tokenizer.eos_token_id})")
    print(f"UNK token: {tokenizer.unk_token} (id: {tokenizer.unk_token_id})")
    
    # 測試一些奇怪的 token ids
    strange_ids = [36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]
    print(f"\n檢查可疑的 token ids:")
    for token_id in strange_ids:
        try:
            decoded = tokenizer.decode([token_id])
            print(f"  ID {token_id}: '{decoded}'")
        except:
            print(f"  ID {token_id}: ERROR")

if __name__ == "__main__":
    # 診斷 tokenizer
    diagnose_tokenizer()
    
    print("\n" + "="*50)
    
    # 完整測試
    success = test_model()