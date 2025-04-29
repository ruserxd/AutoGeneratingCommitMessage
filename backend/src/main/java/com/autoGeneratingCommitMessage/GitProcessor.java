package com.autoGeneratingCommitMessage;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.logging.Level;
import java.util.logging.Logger;

public class GitProcessor {
    private static final Logger logger = Logger.getLogger(GitProcessor.class.getName());

    /*
     **執行 Git diff
     */
    public static String getGitDiff(File repoDir, String file) {
        StringBuilder output = new StringBuilder();
        try {
            // 執行 `git diff` 指令
            ProcessBuilder processBuilder = new ProcessBuilder("git", "diff", file);
            processBuilder.directory(repoDir);
            processBuilder.redirectErrorStream(true);
            Process process = processBuilder.start();

            // 獲取 diff 資訊
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
}
