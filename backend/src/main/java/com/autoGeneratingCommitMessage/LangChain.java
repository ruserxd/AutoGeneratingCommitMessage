package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;
import java.util.stream.Collectors;


@Component
public class LangChain {
    private static final Logger logger = Logger.getLogger(LangChain.class.getName());
    //LLM
    public static OllamaChatModel model = OllamaChatModel.builder()
                                                         .modelName("tavernari/git-commit-message:latest")
                                                         .baseUrl("http://localhost:11434")
                                                         .temperature(0.7)
                                                         .timeout(Duration.ofSeconds(300))
                                                         .build();

    public String generateCommitMessage(String diffInfo) {
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
                """ + diffInfo;

        logger.info("DiffInfo " + diffInfo);
        String commitMessage = model.generate(prompt_CommitMessage);
        logger.info("產生 Commit Message" + commitMessage);
        return commitMessage;
    }

    /*
     ** 將前端獲得的 git status 簡化
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

        String formatGitStatus = formatSection("內容修改過的檔案", modified)
                + "\n\n" + formatSection("新增的檔案", added)
                + "\n\n" + formatSection("刪除的檔案", deleted)
                + "\n\n" + formatSection("變更過路徑的檔案", renamed);
        logger.info("獲得簡化的 git status" + formatGitStatus);

        return formatGitStatus;
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
}