package com.autoGeneratingCommitMessage;

import com.autoGeneratingCommitMessage.model.FileDiffData;
import dev.langchain4j.model.ollama.OllamaChatModel;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
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
        .timeout(Duration.ofSeconds(600))
        .build();

    this.stagedModel = OllamaChatModel.builder()
        .modelName("deepseek-r1:14b")
        .baseUrl("http://localhost:11434")
        .temperature(0.4)
        .timeout(Duration.ofSeconds(600))
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
      return "生成 Commit Message 失敗: " + e.getMessage() + " 可能為 Ollama 未打開導致";
    }
  }

  /**
   * 批量生成多個檔案的修改內容摘要
   *
   * @param filesDiffData 包含檔案路徑和對應 diff 資訊的列表
   * @return 所有檔案修改內容的組合摘要
   */
  public String generateBatchFilesSummary(List<FileDiffData> filesDiffData) {
    if (filesDiffData == null || filesDiffData.isEmpty()) {
      log.warn("收到空的檔案 diff 資料列表");
      return "無修改內容";
    }

    log.info("開始批量生成檔案修改摘要，檔案數量: {}", filesDiffData.size());

    List<String> fileSummaries = new ArrayList<>();

    for (FileDiffData fileData : filesDiffData) {
      try {
        if (fileData.getDiff() == null || fileData.getDiff().trim().isEmpty()) {
          log.debug("檔案 {} 沒有修改內容", fileData.getFile());
          fileSummaries.add(fileData.getFile() + ": 無修改內容");
          continue;
        }

        String summary = generateSingleFileSummary(fileData.getFile(), fileData.getDiff());
        fileSummaries.add(summary);

      } catch (Exception e) {
        log.warn("生成檔案 {} 摘要時發生錯誤: {}", fileData.getFile(), e.getMessage());
        fileSummaries.add(fileData.getFile() + ": 生成摘要失敗 - " + e.getMessage());
      }
    }

    String finalSummary = String.join("\n\n", fileSummaries);
    log.info("成功生成批量檔案修改摘要");
    return finalSummary;
  }

  /**
   * 生成單一檔案的修改內容摘要
   *
   * @param filePath 檔案路徑
   * @param diffInfo 單一檔案的 Git diff 資訊
   * @return 該檔案修改內容的簡單摘要
   */
  private String generateSingleFileSummary(String filePath, String diffInfo) {
    log.debug("開始生成檔案修改摘要，檔案: {}", filePath);

    try {
      String prompt = """
          你是一名專業的程式設計師
          分析以下 Java 檔案的 Git diff 內容，並用繁體中文簡潔地總結修改內容
          
          回應格式要求：
          - 請勿使用過多特殊符號
          - 以檔案名稱開頭
          - 簡潔說明主要做了什麼改動
          
          檔案路徑: %s
          
          Git diff 內容:
          %s
          """.formatted(filePath, diffInfo);

      String summary = stagedModel.generate(prompt);
      log.debug("成功生成檔案修改摘要，檔案: {}", filePath);
      return removeThinKTags(summary);
    } catch (Exception e) {
      log.warn("生成檔案修改摘要時發生錯誤，檔案: {}, 錯誤: {}", filePath, e.getMessage());
      throw e;
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
    langChain.generateCommitMessageByNoIntegrate(
        readDiffFile("src/main/resources/diffData/car_diff.txt"));
  }
}