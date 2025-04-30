package com.autoGeneratingCommitMessage;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import retrofit2.http.POST;

import java.util.Map;
import java.util.logging.Logger;


// TODO: 優先處理這部份，這邊要修改 API Controller，只負責做 API 的事情不存資料
// TODO: workspace 與 statusInfo 的資訊近乎相同
@CrossOrigin(origins = "*")
@RestController
public class APIController {
    private static final Logger logger = Logger.getLogger(APIController.class.getName());

    String workspace;
    String statusInfo;
    String diffInfo;

    private final LangChain langchain;

    @Autowired
    public APIController(LangChain langchain) {
        this.langchain = langchain;
    }

    /*
     **執行 LangChain 並將 Commit Message 傳給前端
     */
    @RequestMapping("/getCommitMessage")
    public String getCommitMessage() {
        return langchain.generateCommitMessage(workspace);
    }

    /*
     **將 git status 傳到前端 webview
     */
    @RequestMapping("/getStatus")
    public String getStatus() {
        String status = langchain.generateGitStatus(statusInfo);
        logger.info("/getStatus 獲得 " + status);
        return status;
    }

    /*
     **從前端獲得工作區目錄
     */
    @PostMapping("/getList")
    public ResponseEntity<String> receiveJavaFiles(@RequestBody Map<String, Object> workspaceList) {
        workspace = (String) workspaceList.get("workspace");
        statusInfo = (String) workspaceList.get("gitStatus");
        logger.info(workspace);
        logger.info(statusInfo);
        System.out.println("Workspace 路徑：" + workspace);
        System.out.println(statusInfo);
        return ResponseEntity.ok("接收成功！");
    }

    /*
     **從前端獲得stage中所有檔案的diff info
     */
    @PostMapping("/getAllDiff")
    public ResponseEntity<String> getAllDiff(@RequestBody Map<String, Object> workspaceList) {
        diffInfo = (String) workspaceList.get("diffInfo");
        System.out.println(diffInfo);
        return ResponseEntity.ok("接收成功！");
    }

}