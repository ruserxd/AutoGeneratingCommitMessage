package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.stereotype.Component;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;
import java.util.stream.Collectors;


@Component
public class LangChain {
    private static final Logger logger = Logger.getLogger(LangChain.class.getName());
    //LLM
    public static OllamaChatModel model = OllamaChatModel.builder()
                                                         .modelName("tavernari/git-commit-message:latest")
                                                         .baseUrl("http://localhost:11434")
                                                         .temperature(0.9)
                                                         .timeout(Duration.ofSeconds(300))
                                                         .build();

    // TODO: 各別做統整再生成 Commit Message
    /*
     * 生成 Commit Message
     * */
    public String generateCommitMessage(String workSpace) {

        File repoDir = new File(workSpace);

        List<String> modifiedFiles = getModifiedFiles(repoDir);

        if (modifiedFiles.isEmpty()) {
            System.out.println("沒有檔案變更，無需產生 commit message。");
            return "沒有檔案變更，無需產生 commit message。";
        }

        // TODO: 抓 Git Diff 從 extension.ts 獲取
        StringBuilder diffResults = new StringBuilder();
        for (String file : modifiedFiles) {
            diffResults.append(GitProcessor.getGitDiff(repoDir, file)).append("\n");
        }
        String prompt_CommitMessage = """
                Please generate an English commit message based on the following Conventional Commits specification:
                Please output a single-line commit message that strictly follows the Conventional Commits format.
                
                1. Use `feat` for adding new features, `fix` for bug fixes, `docs` for documentation changes, `refactor` for code refactoring, and `chore` for changes related to build tools or auxiliary development processes.
                
                2. The commit message format should follow this structure:
                
                   Header: <type>(<scope>): <subject>
                      - type: Indicates the type of commit: feat, fix, docs, style, refactor, test, chore. This field is required.
                      - scope: Describes the area of the codebase affected by the change (e.g., database, controller, template layer, etc.). This field is optional.
                      - subject: A short description of the change. It should be no more than 50 characters and should not end with a period.
                
                   Body (optional):
                      - Wrap lines at 72 characters.
                      - Provide a detailed description of the changes and the reasoning behind them.
                      - Explain how the changes differ from previous behavior, if applicable.
                """ + diffResults;

        System.out.print(diffResults);
        String commitMessage = model.generate(prompt_CommitMessage);
        System.out.println(cleanMessage(commitMessage));
        return cleanMessage(commitMessage);
    }

    /*
     ** 簡化 git status
     */
    public String generateGitStatus(String statusInfo) {
        List<String> modified = new ArrayList<>();
        List<String> added = new ArrayList<>();
        List<String> deleted = new ArrayList<>();
        List<String> renamed = new ArrayList<>();

        String[] lines = statusInfo.split("\n");

        for (String line : lines) {
            line = line.trim();
            if (line.startsWith("Changes to be committed:")) {
                continue;
            } else if (line.startsWith("Changes not staged for commit:")) {
                continue;
            }

            // 忽略無關的提示文字
            if (line.isEmpty() || line.startsWith("(use") || line.startsWith("On branch") || line.startsWith("Your branch is")) {
                continue;
            }

            // 只處理 Java 檔案
            if (line.endsWith(".java")) {
                if (line.contains("renamed:")) {
                    String path = line.replace("renamed:", "").trim();
                    renamed.add(path);
                } else if (line.contains("modified:")) {
                    modified.add(line.replace("modified:", "").trim());
                } else if (line.contains("deleted:")) {
                    deleted.add(line.replace("deleted:", "").trim());
                } else if (line.contains("new file:")) {
                    added.add(line.replace("new file:", "").trim());
                }
            }
        }

        return formatSection("內容修改過的檔案", modified)
                + "\n\n" + formatSection("新增的檔案", added)
                + "\n\n" + formatSection("刪除的檔案", deleted)
                + "\n\n" + formatSection("變更過路徑的檔案", renamed);
    }

    /*
     ** 小工具：格式化區塊輸出
     */
    private String formatSection(String title, List<String> files) {
        return title + "(" + files.size() + " files):\n"
                + files.stream()
                       .map(f -> " " + f)
                       .collect(Collectors.joining("\n"));
    }

    // TODO: git diff --staged
    /*
     ** 獲取有哪些修改檔，進行git diff，並將整合後的diff info回傳給langchain Function
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
                        String path = line.substring(2).trim();

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
     ** 將模型的推理過程清除
     */
    private static String cleanMessage(String rawOutput) {
        return rawOutput
                .replaceAll("(?s)<think>.*?</think>", "")
                .trim();
    }
}
