package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

@Component
public class LangChain {
    private static final Logger logger = Logger.getLogger(LangChain.class.getName());
    //LLM
    public static OllamaChatModel model = OllamaChatModel.builder()
                                                         .modelName("deepseek-r1:8b")
                                                         .baseUrl("http://localhost:11434")
                                                         .temperature(0.5)
                                                         .build();

    public String generateCommitMessage(String workSpace) {

        File repoDir = new File(workSpace);

        List<String> modifiedFiles = getModifiedFiles(repoDir);


        if (modifiedFiles.isEmpty()) {
            System.out.println("沒有檔案變更，無需產生 commit message。");
            return "沒有檔案變更，無需產生 commit message。";
        }

        StringBuilder diffResults = new StringBuilder();
        for (String file : modifiedFiles) {
            diffResults.append(GitProcessor.getGitDiff(repoDir, file)).append("\n");
        }
        String prompt_CommitMessage = """
                請基於以下 Conventional Commits 規範生成一個英文 Commit Message：
                請直接輸出一行符合 Conventional Commits 規範的英文 commit message
                1. `feat` 用於新增功能，`fix` 用於修復 bug，`docs` 用於文件變更，`refactor` 用於重構，`chore` 用於開發工具變更。
                2. Commit Message 格式範例如下：
                
                   Header: <type>(<scope>): <subject>
                      - type: 代表 commit 的類別：feat, fix, docs, style, refactor, test, chore，必要欄位。
                      - scope 代表 commit 影響的範圍，例如資料庫、控制層、模板層等等，視專案不同而不同，為可選欄位。
                      - subject 代表此 commit 的簡短描述，不要超過 50 個字元，結尾不要加句號，為必要欄位。
                
                   Body: 72-character wrapped. This should answer:
                       * Body 部份是對本次 Commit 的詳細描述，可以分成多行，每一行不要超過 72 個字元。
                        * 說明程式碼變動的項目與原因，還有與先前行為的對比。
                
                """ + diffResults;

        String commitMessage = model.generate(prompt_CommitMessage);
        System.out.println(cleanMessage(commitMessage));
        return cleanMessage(commitMessage);
    }

    /*
     ** 將獲得的 git status 利用 LLM 做修正
     */
    public String generateGitStatus(String workSpace) {
        String statusOutput = "";
        try {
            statusOutput = GitProcessor.getGitStatus(workSpace);
        } catch (IllegalArgumentException e) {
            return e.getMessage();
        }

        String prompt_status = """
                根據下列 `git status` 的原始輸出，請將java檔案依照變動類型進行分類，並用清楚的人類可讀格式輸出，並加入檔案數量，如果有數目為0的類型也要輸出，使用英文。
                  請分類成四個區塊：
                    1. 內容修改過的檔案(modified)
                    2. 新增的檔案 (new file)
                    3. 刪除的檔案(delete)
                    4. 變更過路徑的檔案(renamed)
                
                    格式範例如下：
                
                    內容修改過的檔案(2 files):
                     src/App.java
                     src/utils/Helper.java
                
                    新增的檔案(1 files):
                     src/newmodule/NewService.java
                
                    刪除的檔案(1 files):
                     src/oldmodule/OldService.java
                
                    變更過路徑的檔案(1 files):
                     src/Animal/Buff.java -> src/Function/Buff.java
                
                     以下是 git status 的結果，請根據規則進行整理，不需要補充或解釋，只要乾淨列出結果，不要有其他文字輸出，請按照上述的順序輸出類型，每個類型之間用一行空白行隔開，請處理JAVA檔案就好，資料夾也不用理會。
                """ + statusOutput;
        String raw = model.generate(prompt_status);
        return cleanMessage(raw);
    }

    /*
     **獲取有哪些修改檔，進行git diff，並將整合後的diff info回傳給langchain Function
     */
    private static List<String> getModifiedFiles(File repoDir) {
        List<String> modifiedFiles = new ArrayList<>();
        try {
            ProcessBuilder processBuilder = new ProcessBuilder("git", "status", "--porcelain");
            processBuilder.directory(repoDir);
            Process process = processBuilder.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    line = line.trim();

                    // 處理修改 (M) 和 移動 (RM) 的情況
                    if (line.matches("^(M|RM|AM).*\\.java")) {
                        // 抓路徑部分：從第4個字元開始
                        String path = line.substring(3).trim();

                        if (path.contains("->")) {
                            // 處理移動（RM），只取箭頭右邊的新路徑
                            String[] parts = path.split("->");
                            if (parts.length == 2) {
                                String newPath = parts[1].trim();
                                modifiedFiles.add(newPath);
                            }
                        } else {
                            modifiedFiles.add(path);
                        }
                    }
                }
            }
            process.waitFor();
        } catch (IOException | InterruptedException e) {
            logger.log(Level.SEVERE, e.getMessage(), e);
        }
        return modifiedFiles;
    }

    /*
     **將模型的推理過程清除
     */
    private static String cleanMessage(String rawOutput) {
        return rawOutput
                .replaceAll("(?s)<think>.*?</think>", "")
                .trim();
    }
}
