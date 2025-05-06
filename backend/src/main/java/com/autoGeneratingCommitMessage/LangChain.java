package com.autoGeneratingCommitMessage;

import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.logging.Logger;

/**
 * LangChain 組件，負責與 Ollama 模型交互並生成 Commit Message
 * 包含處理前端提供的 Git 狀態和生成格式化輸出的功能
 */
@Component
public class LangChain {
    private static final Logger logger = Logger.getLogger(LangChain.class.getName());

    // LLM 模型配置
    private final OllamaChatModel model;

    public LangChain() {
        // 初始化 Commit Message 模型
        this.model = OllamaChatModel.builder()
                                    .modelName("tavernari/git-commit-message:latest")
                                    .baseUrl("http://localhost:11434")
                                    .temperature(0.7)
                                    .timeout(Duration.ofSeconds(300))
                                    .build();
    }

    /**
     * 生成 Commit Message
     * @param diffInfo 前端提供的 Git diff 資訊
     * @return 生成的 Commit Message
     */
    public String generateCommitMessage(String diffInfo) {
        if (diffInfo == null || diffInfo.trim().isEmpty()) {
            logger.warning("收到空的 diff 資訊，無法生成 Commit Message");
            return "無法生成 Commit Message: 尚無檔案變更";
        }

        String prompt_CommitMessage = buildCommitMessagePrompt(diffInfo);
        logger.info("開始生成 Commit Message...");

        try {
            String commitMessage = model.generate(prompt_CommitMessage);
            logger.info("成功生成 Commit Message");
            return commitMessage;
        } catch (Exception e) {
            logger.severe("生成 Commit Message 時發生錯誤: " + e.getMessage());
            return "生成 Commit Message 失敗: " + e.getMessage();
        }
    }

    /**
     * 構建 Commit Message 提示
     * @param diffInfo 前端提供的 Git diff 資訊
     * @return 完整的提示文本
     */
    private String buildCommitMessagePrompt(String diffInfo) {
        logger.info("DiffInfo -> " +  diffInfo);
//        return """
//                Please generate an English commit message based on the following Conventional Commits specification:
//                Please output a single-line commit message that strictly follows the Conventional Commits format.
//
//                1. Use `feat` for adding new features, `fix` for bug fixes, `docs` for documentation changes, `refactor` for code refactoring, and `chore` for changes related to build tools or auxiliary development processes.
//
//                2. The commit message format should follow this structure:
//
//                   Header: <type>(<scope>): <subject>
//                      - type: Indicates the type of commit: feat, fix, docs, style, refactor, test, chore. This field is required.
//                      - scope: Describes the area of the codebase affected by the change (e.g., database, controller, template layer, etc.). This field is optional.
//                      - subject: A short description of the change. It should be no more than 50 characters and should not end with a period.
//
//                   Body (optional):
//                      - Wrap lines at 72 characters.
//                      - Provide a detailed description of the changes and the reasoning behind them.
//                      - Explain how the changes differ from previous behavior, if applicable.
//                """ + diffInfo;
        return diffInfo;
    }
}