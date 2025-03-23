package org.example;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;



import dev.langchain4j.model.ollama.OllamaChatModel;

public class Main {
    private static final Logger logger = Logger.getLogger(Main.class.getName());

    public static void main(String[] args) {

        File repoDir = new File("C:\\Users\\user\\Desktop\\test");

        List<String> modifiedFiles = getModifiedFiles(repoDir);
        OllamaChatModel model = OllamaChatModel.builder()
                .modelName("huihui_ai/deepseek-r1-abliterated:14b")
                .baseUrl("http://localhost:11434")
                .temperature(0.7)
                .build();

        if (modifiedFiles.isEmpty()) {
            System.out.println("沒有檔案變更，無需產生 commit message。");
            return;
        }

        StringBuilder allDiffResults = new StringBuilder();
        for (String file : modifiedFiles) {
            StringBuilder diffResults = new StringBuilder();
            diffResults.append(getGitDiff(repoDir, file)).append("\n");

            String prompt1 = """
                請基於以下 Conventional Commits 規範生成一個簡單的英文 Commit Message：
                請直接輸出一行符合 Conventional Commits 規範的英文 commit message，**不要加上說明、格式範例、<think>、解釋、或前後語句**。
                1. `feat` 用於新增功能，`fix` 用於修復 bug，`docs` 用於文件變更，`refactor` 用於重構，`chore` 用於開發工具變更。
                2. Commit Message 格式範例如下：

                   feat: 簡單描述哪個檔案增加了那些功能

                """ + diffResults;
            String raw = model.generate(prompt1);
            String simpleMessage = cleanMessage(raw);
            System.out.println(simpleMessage);
            allDiffResults.append(simpleMessage).append("\n");

        }
        System.out.println("=== 整合前的所有 simple messages ===");
        System.out.println(allDiffResults);

        String prompt2 = """
                請閱讀以下多段 commit message，並依照 Conventional Commits 規範，整合為一個清楚且有組織的 commit message。若有相同類型 (如 feat, fix)，請合併為一段，並將細節列成清單。
                如有多種類型，每種類型的message都要輸出。
                都用英文輸出。
                請只輸出最終 commit message，格式如下：
                範例如下：

                   feat: 增加功能
                   - 哪個檔案增加了什麼功能
                   - 哪個檔案增加了什麼功能
                   
                   refactor: 重構功能
                   - 哪個檔案重構了什麼功能
                   - 哪個檔案重構了什麼功能

                你是一個負責生成 Git Commit Message 的 AI，請輸出符合 Conventional Commits 規範的英文 Commit Message：
                """ + allDiffResults;



        String commitMessage = model.generate(prompt2);
        System.out.println(commitMessage);
    }


    private static List<String> getModifiedFiles(File repoDir) {
        List<String> modifiedFiles = new ArrayList<>();
        try {
            ProcessBuilder processBuilder = new ProcessBuilder("git", "status", "--porcelain");
            processBuilder.directory(repoDir);
            Process process = processBuilder.start();

            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    if (line.startsWith("AM") && line.endsWith(".java")) {
                        modifiedFiles.add(line.substring(3).trim());
                    }
                }
            }

            process.waitFor();
        } catch (IOException | InterruptedException e) {
            logger.log(Level.SEVERE, e.getMessage(), e);
        }
        return modifiedFiles;
    }

    private static String getGitDiff(File repoDir, String file) {
        StringBuilder output = new StringBuilder();
        try {
            // 執行 `git diff` 指令
            ProcessBuilder processBuilder = new ProcessBuilder("git", "diff", file);
            processBuilder.directory(repoDir);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }
            }
            process.waitFor();
        } catch (IOException | InterruptedException e) {
            logger.log(Level.SEVERE, e.getMessage(), e);
        }
        return output.toString();
    }

    private static String cleanMessage(String rawOutput) {
        return rawOutput
                .replaceAll("(?s)<think>.*?</think>", "")
                .trim();
    }
}
