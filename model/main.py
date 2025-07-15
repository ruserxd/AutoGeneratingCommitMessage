from transformers import T5ForConditionalGeneration, RobertaTokenizer
import torch

def test_model():
    """測試模型生成功能"""    
    model_path = "./commit-model"
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    model = T5ForConditionalGeneration.from_pretrained(model_path)
    model.eval()
    
    # 測試用的 diff
    test_diff = """diff --git a/src/main/java/com/thealgorithms/datastructures/heaps/HeapElement.java b/src/main/java/com/thealgorithms/datastructures/heaps/HeapElement.java\nindex 7c457a340645..20f33bd2d146 100644\n--- a/src/main/java/com/thealgorithms/datastructures/heaps/HeapElement.java\n+++ b/src/main/java/com/thealgorithms/datastructures/heaps/HeapElement.java\n@@ -1,14 +1,24 @@\n package com.thealgorithms.datastructures.heaps;\n \n /**\n- * Class for heap elements.<br>\n+ * Class representing an element in a heap.\n  *\n  * <p>\n- * A heap element contains two attributes: a key which will be used to build the\n- * tree (int or double, either primitive type or object) and any kind of\n- * IMMUTABLE object the user sees fit to carry any information he/she likes. Be\n- * aware that the use of a mutable object might jeopardize the integrity of this\n- * information.\n+ * A heap element contains two attributes: a key used for ordering in the heap\n+ * (which can be of type int or double, either as primitive types or as wrapper objects)\n+ * and an additional immutable object that can store any supplementary information the user desires.\n+ * Note that using mutable objects may compromise the integrity of this information.\n+ * </p>\n+ *\n+ * <p>\n+ * The key attribute is used to determine the order of elements in the heap,\n+ * while the additionalInfo attribute can carry user-defined data associated with the key.\n+ * </p>\n+ *\n+ * <p>\n+ * This class provides multiple constructors to accommodate various key types and includes\n+ * methods to retrieve the key and additional information.\n+ * </p>\n  *\n  * @author Nicolas Renard\n  */\n@@ -19,9 +29,10 @@ public class HeapElement {\n \n     // Constructors\n     /**\n-     * @param key : a number of primitive type 'double'\n-     * @param info : any kind of IMMUTABLE object. May be null, since the\n-     * purpose is only to carry additional information of use for the user\n+     * Creates a HeapElement with the specified key and additional information.\n+     *\n+     * @param key  the key of the element (primitive type double)\n+     * @param info any immutable object containing additional information, may be null\n      */\n     public HeapElement(double key, Object info) {\n         this.key = key;\n@@ -29,9 +40,10 @@ public HeapElement(double key, Object info) {\n     }\n \n     /**\n-     * @param key : a number of primitive type 'int'\n-     * @param info : any kind of IMMUTABLE object. May be null, since the\n-     * purpose is only to carry additional information of use for the user\n+     * Creates a HeapElement with the specified key and additional information.\n+     *\n+     * @param key  the key of the element (primitive type int)\n+     * @param info any immutable object containing additional information, may be null\n      */\n     public HeapElement(int key, Object info) {\n         this.key = key;\n@@ -39,9 +51,10 @@ public HeapElement(int key, Object info) {\n     }\n \n     /**\n-     * @param key : a number of object type 'Integer'\n-     * @param info : any kind of IMMUTABLE object. May be null, since the\n-     * purpose is only to carry additional information of use for the user\n+     * Creates a HeapElement with the specified key and additional information.\n+     *\n+     * @param key  the key of the element (object type Integer)\n+     * @param info any immutable object containing additional information, may be null\n      */\n     public HeapElement(Integer key, Object info) {\n         this.key = key;\n@@ -49,9 +62,10 @@ public HeapElement(Integer key, Object info) {\n     }\n \n     /**\n-     * @param key : a number of object type 'Double'\n-     * @param info : any kind of IMMUTABLE object. May be null, since the\n-     * purpose is only to carry additional information of use for the user\n+     * Creates a HeapElement with the specified key and additional information.\n+     *\n+     * @param key  the key of the element (object type Double)\n+     * @param info any immutable object containing additional information, may be null\n      */\n     public HeapElement(Double key, Object info) {\n         this.key = key;\n@@ -59,7 +73,9 @@ public HeapElement(Double key, Object info) {\n     }\n \n     /**\n-     * @param key : a number of primitive type 'double'\n+     * Creates a HeapElement with the specified key.\n+     *\n+     * @param key the key of the element (primitive type double)\n      */\n     public HeapElement(double key) {\n         this.key = key;\n@@ -67,7 +83,9 @@ public HeapElement(double key) {\n     }\n \n     /**\n-     * @param key : a number of primitive type 'int'\n+     * Creates a HeapElement with the specified key.\n+     *\n+     * @param key the key of the element (primitive type int)\n      */\n     public HeapElement(int key) {\n         this.key = key;\n@@ -75,7 +93,9 @@ public HeapElement(int key) {\n     }\n \n     /**\n-     * @param key : a number of object type 'Integer'\n+     * Creates a HeapElement with the specified key.\n+     *\n+     * @param key the key of the element (object type Integer)\n      */\n     public HeapElement(Integer key) {\n         this.key = key;\n@@ -83,7 +103,9 @@ public HeapElement(Integer key) {\n     }\n \n     /**\n-     * @param key : a number of object type 'Double'\n+     * Creates a HeapElement with the specified key.\n+     *\n+     * @param key the key of the element (object type Double)\n      */\n     public HeapElement(Double key) {\n         this.key = key;\n@@ -92,46 +114,57 @@ public HeapElement(Double key) {\n \n     // Getters\n     /**\n-     * @return the object containing the additional info provided by the user.\n+     * Returns the object containing the additional information provided by the user.\n+     *\n+     * @return the additional information\n      */\n     public Object getInfo() {\n         return additionalInfo;\n     }\n \n     /**\n-     * @return the key value of the element\n+     * Returns the key value of the element.\n+     *\n+     * @return the key of the element\n      */\n     public double getKey() {\n         return key;\n     }\n \n     // Overridden object methods\n+    /**\n+     * Returns a string representation of the heap element.\n+     *\n+     * @return a string describing the key and additional information\n+     */\n+    @Override\n     public String toString() {\n-        return \"Key: \" + key + \" - \" + additionalInfo.toString();\n+        return \"Key: \" + key + \" - \" + (additionalInfo != null ? additionalInfo.toString() : \"No additional info\");\n     }\n \n     /**\n-     * @param otherHeapElement\n-     * @return true if the keys on both elements are identical and the\n-     * additional info objects are identical.\n+     * Compares this heap element to another object for equality.\n+     *\n+     * @param o the object to compare with\n+     * @return true if the keys and additional information are identical, false otherwise\n      */\n     @Override\n     public boolean equals(Object o) {\n-        if (o != null) {\n-            if (!(o instanceof HeapElement)) {\n-                return false;\n-            }\n-            HeapElement otherHeapElement = (HeapElement) o;\n-            return ((this.key == otherHeapElement.key) && (this.additionalInfo.equals(otherHeapElement.additionalInfo)));\n+        if (o instanceof HeapElement otherHeapElement) {\n+            return this.key == otherHeapElement.key && (this.additionalInfo != null ? this.additionalInfo.equals(otherHeapElement.additionalInfo) : otherHeapElement.additionalInfo == null);\n         }\n         return false;\n     }\n \n+    /**\n+     * Returns a hash code value for the heap element.\n+     *\n+     * @return a hash code value for this heap element\n+     */\n     @Override\n     public int hashCode() {\n-        int result = 0;\n-        result = 31 * result + (int) key;\n-        result = 31 * result + (additionalInfo != null ? additionalInfo.hashCode() : 0);\n+        int result = 31 * (int) key;\n+        result += (additionalInfo != null) ? additionalInfo.hashCode() : 0;\n         return result;\n     }\n }\ndiff --git a/src/test/java/com/thealgorithms/datastructures/heaps/HeapElementTest.java b/src/test/java/com/thealgorithms/datastructures/heaps/HeapElementTest.java\nnew file mode 100644\nindex 000000000000..d04a9de8a94b\n--- /dev/null\n+++ b/src/test/java/com/thealgorithms/datastructures/heaps/HeapElementTest.java\n@@ -0,0 +1,55 @@\n+package com.thealgorithms.datastructures.heaps;\n+\n+import static org.junit.jupiter.api.Assertions.assertEquals;\n+import static org.junit.jupiter.api.Assertions.assertNotEquals;\n+import static org.junit.jupiter.api.Assertions.assertNull;\n+\n+import org.junit.jupiter.api.Test;\n+\n+class HeapElementTest {\n+\n+    @Test\n+    void testConstructorAndGetters() {\n+        HeapElement element = new HeapElement(5.0, \"Info\");\n+        assertEquals(5.0, element.getKey());\n+        assertEquals(\"Info\", element.getInfo());\n+    }\n+\n+    @Test\n+    void testConstructorWithNullInfo() {\n+        HeapElement element = new HeapElement(10);\n+        assertEquals(10, element.getKey());\n+        assertNull(element.getInfo());\n+    }\n+\n+    @Test\n+    void testToString() {\n+        HeapElement element = new HeapElement(7.5, \"TestInfo\");\n+        assertEquals(\"Key: 7.5 - TestInfo\", element.toString());\n+\n+        HeapElement elementWithoutInfo = new HeapElement(3);\n+        assertEquals(\"Key: 3.0 - No additional info\", elementWithoutInfo.toString());\n+    }\n+\n+    @Test\n+    void testEquals() {\n+        HeapElement element1 = new HeapElement(2.5, \"Data\");\n+        HeapElement element2 = new HeapElement(2.5, \"Data\");\n+        HeapElement element3 = new HeapElement(3.0, \"DifferentData\");\n+\n+        assertEquals(element1, element2); // Same key and info\n+        assertNotEquals(element1, element3); // Different key\n+        assertNotEquals(null, element1); // Check for null\n+        assertNotEquals(\"String\", element1); // Check for different type\n+    }\n+\n+    @Test\n+    void testHashCode() {\n+        HeapElement element1 = new HeapElement(4, \"HashMe\");\n+        HeapElement element2 = new HeapElement(4, \"HashMe\");\n+        HeapElement element3 = new HeapElement(4, \"DifferentHash\");\n+\n+        assertEquals(element1.hashCode(), element2.hashCode()); // Same key and info\n+        assertNotEquals(element1.hashCode(), element3.hashCode()); // Different info\n+    }\n+},
"""

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