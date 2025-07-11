from transformers import T5ForConditionalGeneration, RobertaTokenizer


model_path = "./commit-model"  
tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
model = T5ForConditionalGeneration.from_pretrained(model_path)

text = """diff --git a/src/main/java/com/example/DataParser.java b/src/main/java/com/example/DataParser.java
index 3456789..cdefghi 100644
--- a/src/main/java/com/example/DataParser.java
+++ b/src/main/java/com/example/DataParser.java
@@ -5,6 +5,10 @@ public class DataParser {
     public int parseNumber(String value) {
-        return Integer.parseInt(value);
+        try {
+            return Integer.parseInt(value);
+        } catch (NumberFormatException e) {
+            return 0; // Default value on parsing failure
+        }
     }
 }"""

input_ids = tokenizer(text, return_tensors="pt", max_length=512, truncation=True, padding=True).input_ids
output = model.generate(input_ids, max_length=156, min_length=50 ,num_beams=5, no_repeat_ngram_size=3, early_stopping=True)


decoded_output = tokenizer.decode(output[0], skip_special_tokens=True)
try:
    commit_message, why = decoded_output.split("\nWhy: ", 1)
    print("Commit Message:", commit_message)
    print("Why:", why)
except ValueError:
    print("Generated Output:", decoded_output)
    print("Warning: Output format incorrect, unable to split into commit message and why")