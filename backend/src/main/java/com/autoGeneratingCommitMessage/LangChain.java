package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
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
  private final OllamaChatModel whyModel;

  // 建構子
  public LangChain() {
    // 初始化 Commit Message 的模型
    this.commitModel = OllamaChatModel.builder()
        .modelName("tavernari/git-commit-message:latest")
        .baseUrl("http://localhost:11434")
        .temperature(0.4)
        .timeout(Duration.ofSeconds(300))
        .build();
    this.whyModel = OllamaChatModel.builder()
            .modelName("Llama3.1")
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


  public String generateWhyMessageByNoIntegrate(String data) {
    if (data == null || data.trim().isEmpty()) {
      log.warn("收到空的資料，無法生成 Why Message");
      return "無法生成 Why Message";
    }

    System.out.println(data);
    log.info("開始生成未整合過的 Why Message...");

    try {
      // 直接生成 Commit Message
      String whyMessage = whyModel.generate("以下是某個檔案的程式碼變更，請根據程式碼變更內容，推測開發者的修改原因:"+data+"只需用英文生成一段簡單的修改原因即可，不要有其他多餘的內容，包含程式碼");
      log.info("成功生成\n{}", whyMessage);
      return whyMessage;
    } catch (Exception e) {
      log.warn("生成 Why Message 時發生錯誤: {}", e.getMessage());
      return "生成 Why Message 失敗: " + e.getMessage();
    }
  }

  private static String readDiffFile(String filePath) throws IOException {
    return Files.readString(Paths.get(filePath));
  }

  public static void main(String[] args) throws IOException {
    LangChain langChain = new LangChain();
    langChain.generateCommitMessageByNoIntegrate(readDiffFile("src/main/resources/diffData/car_diff.txt"));
  }
}