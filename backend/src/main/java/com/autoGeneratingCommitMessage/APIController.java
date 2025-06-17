package com.autoGeneratingCommitMessage;

import com.autoGeneratingCommitMessage.model.FileDiffData;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

/**
 * API 控制器，負責處理與前端的 HTTP 請求和回應 完全無狀態設計，不在後端保存任何資料
 */
@Slf4j
@CrossOrigin(origins = "*")
@RestController
public class APIController {

  private final LangChain langchain;

  public APIController(LangChain langchain) {
    this.langchain = langchain;
  }

  /**
   * 根據提供的 diff 資訊生成 Commit Message
   *
   * @param request 包含 diffInfo 的請求資料
   * @return 生成的 Commit Message
   */
  @PostMapping("/getCommitMessage")
  public ResponseEntity<String> generateCommitMessage(@RequestBody Map<String, String> request) {
    if (!request.containsKey("diffInfo")) {
      return ResponseEntity.badRequest().body("請求缺少 diffInfo 參數");
    }

    String diffInfo = request.get("diffInfo");

    if (diffInfo == null || diffInfo.isEmpty()) {
      return ResponseEntity.badRequest().body("提供的 diff 資訊為空");
    }

    log.info("接收到 diff 資訊，開始生成 Commit Message");

    String commitMessage = langchain.generateCommitMessageByNoIntegrate(diffInfo);

    return ResponseEntity.ok(commitMessage);
  }

  @PostMapping("/getBatchFilesSummary")
  public ResponseEntity<String> generateBatchFilesSummary(
      @RequestBody Map<String, Object> request) {

    if (!request.containsKey("filesDiffData")) {
      return ResponseEntity.badRequest().body("請求缺少 filesDiffData 參數");
    }

    try {
      @SuppressWarnings("unchecked")
      List<Map<String, String>> rawFilesDiffData = (List<Map<String, String>>) request.get(
          "filesDiffData");

      if (rawFilesDiffData == null || rawFilesDiffData.isEmpty()) {
        return ResponseEntity.badRequest().body("提供的檔案 diff 資料為空");
      }

      List<FileDiffData> filesDiffData = rawFilesDiffData.stream()
          .map(data -> new FileDiffData(
              data.get("file"),
              data.get("diff")
          ))
          .collect(Collectors.toList());

      log.info("接收到批量檔案 diff 資訊，檔案數量: {}, 開始生成修改摘要", filesDiffData.size());

      String batchSummary = langchain.generateBatchFilesSummary(filesDiffData);

      return ResponseEntity.ok(batchSummary);

    } catch (ClassCastException e) {
      log.error("解析 filesDiffData 參數時發生錯誤", e);
      return ResponseEntity.badRequest().body("filesDiffData 參數格式錯誤");
    } catch (Exception e) {
      log.error("生成批量檔案摘要時發生錯誤", e);
      return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
          .body("生成摘要失敗: " + e.getMessage());
    }
  }
}