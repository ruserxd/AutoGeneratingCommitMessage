package com.autoGeneratingCommitMessage;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;


@CrossOrigin(origins = "*")
@RestController
public class APIController {

    String workspace;
    String statusInfo;

    private final LangChain langchain;

    @Autowired
    public APIController(LangChain langchain) {
        this.langchain = langchain;
    }

    /*
     **執行 LangChain 並將 Commit Message 傳給前端
     */
    @RequestMapping("/langChain")
    public String langChain() {
        return langchain.generateCommitMessage(workspace);
    }


    /*
     **將 git status 傳到前端 webview
     */
    @RequestMapping("/getStatus")
    public String getStatus() {
        return langchain.generateGitStatus(statusInfo);
    }

    /*
     **從前端獲得工作區目錄
     */
    @PostMapping("/getList")
    public ResponseEntity<String> receiveJavaFiles(@RequestBody Map<String, Object> workspaceList) {
        workspace = (String) workspaceList.get("workspace");
        statusInfo = (String) workspaceList.get("gitStatus");
        System.out.println("Workspace 路徑：" + workspace);
        System.out.println(statusInfo);
        return ResponseEntity.ok("接收成功！");
    }
}