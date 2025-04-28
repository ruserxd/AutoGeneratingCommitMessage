package com.autoGeneratingCommitMessage;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;


@CrossOrigin(origins = "*") // 或限定你的前端網址
@RestController
public class APIController {

    String workspace;

    @Autowired
    private Langchain langchain;

    /*
     **執行langchain並將comiit massege傳給前端
     */
    @RequestMapping("/langchain")
    public String langChain() {
        return langchain.langchain4j(workspace);
    }


    /*
     **將git status傳到前端webview
     */
    @RequestMapping("/getstatus")
    public String getstatus() {
        return langchain.getGitStatus(workspace);
    }

    /*
     **從前端獲得工作區目錄
     */
    @PostMapping("/getlist")
    public ResponseEntity<String> receiveJavaFiles(@RequestBody Map<String, Object> payload) {
        workspace = (String) payload.get("workspace");
        System.out.println("Workspace 路徑：" + workspace);
        return ResponseEntity.ok("接收成功！");
    }


}
