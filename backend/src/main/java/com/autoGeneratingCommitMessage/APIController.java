package com.autoGeneratingCommitMessage;

import java.util.Map;
import lombok.extern.slf4j.Slf4j;
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

    // 使用 LangChain 生成 Commit Message
    String commitMessage = langchain.generateCommitMessageByNoIntegrate(diffInfo);

    return ResponseEntity.ok(commitMessage);
  }


  @PostMapping("/getWhyReason")
  public ResponseEntity<String> getWhyReason(@RequestBody Map<String, String> request) {
    String data = request.get("diffInfo");
    if (!request.containsKey("diffInfo")) {
      return ResponseEntity.badRequest().body("請求缺少 diffInfo 參數");
    }


    String whyMessage = langchain.generateCommitMessageByNoIntegrate(data);

    return ResponseEntity.ok(whyMessage);
  }
}