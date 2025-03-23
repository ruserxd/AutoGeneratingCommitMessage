package org;

import com.github.difflib.DiffUtils;
import com.github.difflib.UnifiedDiffUtils;
import com.github.difflib.patch.Patch;
import dev.langchain4j.model.chat.ChatLanguageModel;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

import static org.Printer.*;

public class CommitGenerator {
    // 明確定義提交訊息的格式規範
    static final String COMMIT_CONVENTION =
            "提交訊息必須遵循以下格式：\n" +
                    "<type>: <subject>\n\n" +
                    "<body>\n\n" +
                    "<footer>\n\n" +
                    "其中：\n" +
                    "- type 必須是以下之一：feat (新功能), fix (錯誤修復), docs (文檔), style (格式), refactor (重構), perf (性能優化), test (測試), chore (日常任務)\n" +
                    "- subject 必須是簡短的描述，不超過50個字符\n" +
                    "- body 必須詳細描述「修改了什麼」(What) 和「為什麼修改」(Why)，每行不超過72個字符\n" +
                    "- footer 可選，用於引用相關議題或重大變更說明";

    private static String removeThinkingProcess(String commitMessage) {
        // 使用正則表達式移除 <think>...</think> 部分
        return commitMessage.replaceAll("<think>[\\s\\S]*?</think>", "").trim();
    }

    // 生成單個檔案的提交訊息
    static String generateSingleFileCommitMessage(ChatLanguageModel model, String oldFilePath, String newFilePath)
            throws IOException {
        Path oldPath = Paths.get(oldFilePath);
        Path newPath = Paths.get(newFilePath);
        List<String> oldFileTxt = Files.readAllLines(oldPath);
        List<String> newFileTxt = Files.readAllLines(newPath);

        String oldFileName = oldPath.getFileName().toString();
        String newFileName = newPath.getFileName().toString();

        printLine(oldFileTxt, "舊版本程式碼 - " + oldFileName);
        printLine(newFileTxt, "新版本程式碼 - " + newFileName);

        // 生成差異
        Patch<String> patch = DiffUtils.diff(oldFileTxt, newFileTxt);

        System.out.println("差異摘要 - " + newFileName + ":");
        List<String> unifiedDiff = UnifiedDiffUtils.generateUnifiedDiff(
                oldFileName, newFileName, oldFileTxt, patch, 3);

        //刪除不必要的兩列
        if (!unifiedDiff.isEmpty())
            unifiedDiff.removeFirst();
        if (!unifiedDiff.isEmpty())
            unifiedDiff.removeFirst();

        // prompt 設定
        String prompt = "請分析以下程式碼差異，並生成符合規範的提交訊息。\n\n" +
                "檔案名稱: " + newFileName + "\n" +
                "Git Diff 資訊：\n" +
                stringListToString(unifiedDiff) + "\n\n" +
                "請分析這些變更做了什麼(What)以及為什麼要這樣修改(Why)，然後生成一個符合以下格式的精簡英文 Commit Message：\n\n" +
                COMMIT_CONVENTION + "\n\n" +
                "請確保提交訊息的每個部分都清晰可見，尤其是type、subject、body和footer的區分。";

        printString(prompt, "生成提示詞");

        // 生成提交訊息
        String response = model.generate(prompt);
        response = removeThinkingProcess(response);
        printCommitMessage(response);

        return response;
    }

    // 合併多個檔案的提交訊息
    static String mergeCommitMessages(ChatLanguageModel model, List<String> commitMessages, List<String> fileNames) {
        StringBuilder mergePrompt = new StringBuilder();
        mergePrompt.append("請合併以下多個檔案的提交訊息，生成一個統一的提交訊息。\n\n");

        for (int i = 0; i < commitMessages.size(); i++) {
            mergePrompt.append("檔案 ").append(i + 1).append(" (").append(fileNames.get(i)).append("):\n");
            mergePrompt.append(commitMessages.get(i)).append("\n\n");
        }

        mergePrompt.append("請分析這些個別的提交訊息，找出共同的修改目的和類型，然後生成一個總結性的英文精簡Commit Message，\n");
        mergePrompt.append("遵循相同的格式規範:\n\n").append(COMMIT_CONVENTION).append("\n\n");
        mergePrompt.append("如果修改類型不同，請選擇最主要或最高層級的類型（例如feat優先於style）。\n");
        mergePrompt.append("請在body中有條理地總結所有檔案的修改內容，同時保持簡潔清晰。");

        printString(mergePrompt.toString(), "合併prompt");

        return removeThinkingProcess(model.generate(mergePrompt.toString()));
    }
}