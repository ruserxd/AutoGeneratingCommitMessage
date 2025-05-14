package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import java.time.Duration;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * LangChain 組件，負責與 Ollama 模型交互並生成 Commit Message 包含處理前端提供的 Git 狀態和生成格式化輸出的功能
 */
@Slf4j
@Component
public class LangChain {

  // LLM 模型配置
  private final OllamaChatModel commitModel;
  private final OllamaChatModel summaryModel;

  // 建構子
  public LangChain() {
    // 初始化 Commit Message 的模型
    this.commitModel = OllamaChatModel.builder()
        .modelName("tavernari/git-commit-message:latest")
        .baseUrl("http://localhost:11434")
        .temperature(0.4)
        .timeout(Duration.ofSeconds(300))
        .build();
    // 整合 Commit Message 的模型
    this.summaryModel = OllamaChatModel.builder()
        .modelName("llama3.1")
        .baseUrl("http://localhost:11434")
        .temperature(0.4)
        .timeout(Duration.ofSeconds(300))
        .build();
  }

  /**
   * 生成 Commit Message 未進行整合
   *
   * @param diffInfo 前端提供的 Git diff 資訊
   * @return 生成的 Commit Message
   */
  public String generateCommitMessageByNoIntegrate(String diffInfo) {
    if (diffInfo == null || diffInfo.trim().isEmpty()) {
      log.warn("收到空的 diff 資訊，無法生成 Commit Message");
      return "無法生成 Commit Message: 尚無檔案變更";
    }

    log.info("開始生成未整合過的 Commit Message...");

    try {
      // 直接生成 Commit Message
      String commitMessage = commitModel.generate(diffInfo);
      log.info("成功生成\n{}", commitMessage);
      return commitMessage;
    } catch (Exception e) {
      log.warn("生成 Commit Message 時發生錯誤: {}", e.getMessage());
      return "生成 Commit Message 失敗: " + e.getMessage();
    }
  }

  public static void main(String[] args) {
    LangChain langChain = new LangChain();
    String commitMessage = langChain.generateCommitMessageByNoIntegrate(
        "diff --git a/Car.java b/Car.java\n"
            + "index 218bbe3..0972a20 100644\n"
            + "--- a/Car.java\n"
            + "+++ b/Car.java\n"
            + "@@ -1,3 +1,35 @@\n"
            + " public class Car {\n"
            + "+    String id;\n"
            + "+    String name;\n"
            + "+    String year;\n"
            + " \n"
            + "+    public Car(String id, String name, String year) {\n"
            + "+        this.id = id;\n"
            + "+        this.name = name;\n"
            + "+        this.year = year;\n"
            + "+    }\n"
            + "+\n"
            + "+    public String getId() {\n"
            + "+        return id;\n"
            + "+    }\n"
            + "+\n"
            + "+    public void setId(String id) {\n"
            + "+        this.id = id;\n"
            + "+    }\n"
            + "+\n"
            + "+    public String getName() {\n"
            + "+        return name;\n"
            + "+    }\n"
            + "+\n"
            + "+    public void setName(String name) {\n"
            + "+        this.name = name;\n"
            + "+    }\n"
            + "+\n"
            + "+    public String getYear() {\n"
            + "+        return year;\n"
            + "+    }\n"
            + "+\n"
            + "+    public void setYear(String year) {\n"
            + "+        this.year = year;\n"
            + "+    }\n"
            + " }\n"
            + "\\ No newline at end of file\n"
            + "diff --git a/People.java b/People.java\n"
            + "new file mode 100644\n"
            + "index 0000000..1177eb8\n"
            + "--- /dev/null\n"
            + "+++ b/People.java\n"
            + "@@ -0,0 +1,35 @@\n"
            + "+public class People {\n"
            + "+  String id;\n"
            + "+  String name;\n"
            + "+  String birthday;\n"
            + "+\n"
            + "+  public People(String id, String name, String birthday) {\n"
            + "+    this.id = id;\n"
            + "+    this.name = name;\n"
            + "+    this.birthday = birthday;\n"
            + "+  }\n"
            + "+\n"
            + "+  public String getId() {\n"
            + "+    return id;\n"
            + "+  }\n"
            + "+\n"
            + "+  public String getName() {\n"
            + "+    return name;\n"
            + "+  }\n"
            + "+\n"
            + "+  public String getBirthday() {\n"
            + "+    return birthday;\n"
            + "+  }\n"
            + "+\n"
            + "+  public void setId(String id) {\n"
            + "+    this.id = id;\n"
            + "+  }\n"
            + "+\n"
            + "+  public void setName(String name) {\n"
            + "+    this.name = name;\n"
            + "+  }\n"
            + "+\n"
            + "+  public void setBirthday(String birthday) {\n"
            + "+    this.birthday = birthday;\n"
            + "+  }\n"
            + "+}\n"
            + "diff --git a/Shop.java b/Shop.java\n"
            + "new file mode 100644\n"
            + "index 0000000..5b70055\n"
            + "--- /dev/null\n"
            + "+++ b/Shop.java\n"
            + "@@ -0,0 +1,25 @@\n"
            + "+public class Shop {\n"
            + "+  String id;\n"
            + "+  String name;\n"
            + "+\n"
            + "+  public Shop(String id, String name) {\n"
            + "+    this.id = id;\n"
            + "+    this.name = name;\n"
            + "+  }\n"
            + "+\n"
            + "+  public String getId() {\n"
            + "+    return id;\n"
            + "+  }\n"
            + "+\n"
            + "+  public String getName() {\n"
            + "+    return name;\n"
            + "+  }\n"
            + "+\n"
            + "+  public void setId(String id) {\n"
            + "+    this.id = id;\n"
            + "+  }\n"
            + "+\n"
            + "+  public void setName(String name) {\n"
            + "+    this.name = name;\n"
            + "+  }\n"
            + "+}\n"
            + "\\ No newline at end of file");
    log.info(commitMessage);
  }
}