package org;

import dev.langchain4j.model.chat.ChatLanguageModel;
import dev.langchain4j.model.ollama.OllamaChatModel;

import java.io.IOException;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

import static org.Printer.printCommitMessage;

public class Main {
    public static void main(String[] args) throws IOException {
        // 建立語言模型
        ChatLanguageModel model = OllamaChatModel.builder()
                                                 .baseUrl("http://localhost:11434")
                                                 .modelName("deepseek-r1:14b")
                                                 .temperature(0.7)
                                                 .timeout(Duration.ofSeconds(180))
                                                 .maxRetries(5)
                                                 .build();

        // 要比較的檔案
        List<String[]> Pairs = new ArrayList<>();

        Pairs.add(new String[]{"src/main/resources/Car/oldClass_Car.java", "src/main/resources/Car/newClass_Car.java"});
        Pairs.add(new String[]{"src/main/resources/Person/oldClass_Person.java", "src/main/resources/Person/newClass_Person.java"});
        Pairs.add(new String[]{"src/main/resources/Bank/newClass_Bank.java", "src/main/resources/Bank/newClass_Bank.java"});

        // 各個檔案生成後獲得的 Message
        List<String> commitMessages = new ArrayList<>();
        List<String> fileNames = new ArrayList<>();

        // 針對每個檔案生成提交訊息
        for (String[] filePair : Pairs) {
            String oldFilePath = filePair[0];
            String newFilePath = filePair[1];
            String fileName = Paths.get(newFilePath).getFileName().toString();

            fileNames.add(fileName);
            String commitMessage = CommitGenerator.generateSingleFileCommitMessage(model, oldFilePath, newFilePath);
            commitMessages.add(commitMessage);
        }

        String finalCommitMessage = CommitGenerator.mergeCommitMessages(model, commitMessages, fileNames);
        printCommitMessage(finalCommitMessage);
    }
}
