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

  private static String readDiffFile(String filePath) throws IOException {
    return Files.readString(Paths.get(filePath));
  }

  public static void main(String[] args) throws IOException {
    LangChain langChain = new LangChain();
    String commitMessage = langChain.generateCommitMessageByNoIntegrate(readDiffFile("src/main/resources/diffData/spring_boot_ai_0bbccf8.txt"));
    log.info(commitMessage);
  }
}