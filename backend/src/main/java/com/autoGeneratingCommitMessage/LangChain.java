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
  private final OllamaChatModel commitModel, stagedModel;

  // 建構子
  public LangChain() {
    // 初始化 Commit Message 的模型
    this.commitModel = OllamaChatModel.builder()
        .modelName("tavernari/git-commit-message:latest")
        .baseUrl("http://localhost:11434")
        .temperature(0.4)
        .timeout(Duration.ofSeconds(300))
        .build();

    this.stagedModel = OllamaChatModel.builder()
        .modelName("deepseek-r1:14b")
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

  /**
   * 生成修改內容摘要
   *
   * @param diffInfo Git diff 資訊
   * @return 修改內容的簡單摘要
   */
  public String generateChangesSummary(String diffInfo) {
    if (diffInfo == null || diffInfo.trim().isEmpty()) {
      log.warn("收到空的 diff 資訊，無法生成修改摘要");
      return "無修改內容";
    }

    log.info("開始生成修改內容摘要...");
    log.info("收到 diff 資訊\n{}", diffInfo);
    try {
      String prompt = """
            分析以下 Git diff 內容，並用繁體中文簡潔地總結修改內容。
            回應格式：
            - 修改了什麼檔案
            - 主要做了什麼改動
            - 限制在 2-3 行以內
            
            Git diff 內容:
            %s
            """.formatted(diffInfo);

      String summary = stagedModel.generate(prompt);
      log.info("成功生成修改摘要: {}", summary);
      return removeThinKTags(summary);
    } catch (Exception e) {
      log.warn("生成修改摘要時發生錯誤: {}", e.getMessage());
      return "生成摘要失敗: " + e.getMessage();
    }
  }

  // 使用正則表達式移除 <think>...</think> 及其內容
  private String removeThinKTags(String text) {
    if (text == null) {
      return null;
    }
    return text.replaceAll("(?s)<think>.*?</think>", "").trim();
  }


  // 測試用
  private static String readDiffFile(String filePath) throws IOException {
    return Files.readString(Paths.get(filePath));
  }

  public static void main(String[] args) throws IOException {
    LangChain langChain = new LangChain();
    langChain.generateCommitMessageByNoIntegrate(readDiffFile("src/main/resources/diffData/car_diff.txt"));
  }
}