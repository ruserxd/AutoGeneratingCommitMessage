package com.example.typescript;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;


@CrossOrigin(origins = "*") // 或限定你的前端網址
@RestController
public class LangChainController {

    String workspace;

    @Autowired
    private langchain langchain;

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
