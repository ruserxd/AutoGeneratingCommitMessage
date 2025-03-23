package com.example.commitmessagegenerator.Service;

import com.example.commitmessagegenerator.Util.FileUtil;
import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.ollama.OllamaChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Path;
import java.time.Duration;
import java.util.List;

@Service
public class CommitMessageService {

    private final DiffService diffService;
    private final FileUtil fileUtil;

    @Value("${ollama.base-url:http://localhost:11434}")
    private String ollamaBaseUrl;

    @Value("${ollama.model:llama3}")
    private String ollamaModel;

    public CommitMessageService(DiffService diffService, FileUtil fileUtil) {
        this.diffService = diffService;
        this.fileUtil = fileUtil;
    }

    public String generateCommitMessage(Path file1, Path file2) throws IOException {
        String diff = diffService.generateDiff(file1, file2);
        return generateCommitMessageFromDiff(diff);
    }

    private String generateCommitMessageFromDiff(String diff) {
        ChatLanguageModel model = OllamaChatModel.builder()
                .baseUrl(ollamaBaseUrl)
                .modelName(ollamaModel)
                .temperature(0.7)
                .timeout(Duration.ofSeconds(60))
                .build();

        String promptText = buildPrompt(diff);
        String response = model.chat(promptText);
        return response;
    }

    private String buildPrompt(String diff) {
        return """
            請根據以下程式碼差異生成一個有意義的 Git commit 訊息。
            遵循 AngularJS Git Commit Message 規範：
            
            * feat: 新增/修改功能 (feature)
            * fix: 修補 bug (bug fix)
            * docs: 文件 (documentation)
            * style: 格式 (不影響程式碼運行的變動 white-space, formatting, missing semi colons, etc)
            * refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)
            * perf: 改善效能 (A code change that improves performance)
            * test: 增加測試 (when adding missing tests)
            * chore: 建構程序或輔助工具的變動 (maintain)
            * revert: 撤銷回覆先前的 commit 例如：revert: type(scope): subject (回覆版本：xxxx)
            
            訊息應該以上述類型之一開頭，後面接冒號和簡短描述。
            請保持簡潔但具描述性。不要超過 100 個字元。
            
            以下是程式碼差異：
            
            %s
            
            只返回 commit 訊息，不要包含其他內容。
            """.formatted(diff);
    }

    public String combineCommitMessages(List<String> commitMessages) {
        ChatLanguageModel model = OllamaChatModel.builder()
                .baseUrl(ollamaBaseUrl)
                .modelName(ollamaModel)
                .temperature(0.7)
                .timeout(Duration.ofSeconds(60))
                .build();

        String promptText = buildCombinePrompt(commitMessages);
        String response = model.chat(promptText);
        return response;
    }

    private String buildCombinePrompt(List<String> commitMessages) {
        StringBuilder messages = new StringBuilder();
        for (int i = 0; i < commitMessages.size(); i++) {
            messages.append("Commit 訊息 ").append(i + 1).append(": ").append(commitMessages.get(i)).append("\n");
        }

        return """
            請根據以下多個 Commit 訊息，合併成"一個"最終的 Git commit 訊息。
            遵循 AngularJS Git Commit Message 規範：
            
            * feat: 新增/修改功能 (feature)
            * fix: 修補 bug (bug fix)
            * docs: 文件 (documentation)
            * style: 格式 (不影響程式碼運行的變動 white-space, formatting, missing semi colons, etc)
            * refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)
            * perf: 改善效能 (A code change that improves performance)
            * test: 增加測試 (when adding missing tests)
            * chore: 建構程序或輔助工具的變動 (maintain)
            * revert: 撤銷回覆先前的 commit 例如：revert: type(scope): subject (回覆版本：xxxx)
            
            訊息應該以上述類型之一開頭，後面接冒號和簡短描述。
            請保持簡潔但具描述性。不要超過 100 個字元。
            
            以下是各個 Commit 訊息：
            
            %s
            
            只返回最終合併的 commit 訊息，不要包含其他內容。
            """.formatted(messages.toString());
    }
}