package com.example.commitmessagegenerator;

import com.example.commitmessagegenerator.Service.CommitMessageService;
import com.example.commitmessagegenerator.Service.DiffService;
import com.example.commitmessagegenerator.Util.FileUtil;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@SpringBootApplication
public class CommitMessageGeneratorApplication {
    private static volatile boolean running = true;

    private static final Map<Path, Long> lastProcessedTimestamps = new ConcurrentHashMap<>();
    private static final long DEBOUNCE_TIME_MS = 20000;

    public static void main(String[] args) {
        SpringApplication.run(CommitMessageGeneratorApplication.class, args);
    }

    @Bean
    public CommandLineRunner demo(CommitMessageService commitMessageService,
                                  DiffService diffService,
                                  FileUtil fileUtil) {
        return (args) -> {
            // director to track
            Path directoryToTrack = getDirectoryToTrackFromUser();
            if (directoryToTrack == null) {
                System.out.println("無效的目錄，程式結束。");
                return;
            }

            // scan .java files and copy them to temp location
            List<Path> filesToTrack = scanJavaFiles(directoryToTrack);
            if (filesToTrack.isEmpty()) {
                System.out.println("目錄中沒有 .java 檔案可監控，程式結束。");
                return;
            }

            Map<Path, Path> originalToTempMap = new HashMap<>();
            for (Path file : filesToTrack) {
                Path tempOriginalFile = Files.createTempFile(file.getFileName().toString() + "_original_", ".java");
                Files.copy(file, tempOriginalFile, StandardCopyOption.REPLACE_EXISTING);
                originalToTempMap.put(file, tempOriginalFile);
                System.out.println("已儲存原始檔案 " + file.getFileName() + " 至臨時位置: " + tempOriginalFile);
            }

            // watch service
            WatchService watchService = FileSystems.getDefault().newWatchService();
            directoryToTrack.register(watchService,
                    StandardWatchEventKinds.ENTRY_CREATE,
                    StandardWatchEventKinds.ENTRY_DELETE,
                    StandardWatchEventKinds.ENTRY_MODIFY);
            System.out.println("已註冊監控目錄: " + directoryToTrack);

            System.out.println("\n開始監控以下檔案的變更:");
            for (Path file : originalToTempMap.keySet()) {
                System.out.println("- " + file);
            }
            System.out.println("請修改這些檔案，系統將自動檢測並生成個別 commit 訊息。");
            System.out.println("輸入 'done' 生成最終合併訊息，輸入 'exit' 退出程式。");

            // commit messages and input listener
            List<String> individualCommitMessages = new ArrayList<>();
            Thread inputThread = startInputListener(commitMessageService, individualCommitMessages);

            while (running) {
                WatchKey key;
                try {

                    key = watchService.poll(1, TimeUnit.SECONDS);
                    if (key == null) {

                        continue;
                    }
                } catch (InterruptedException e) {
                    if (!running) {
                        break;
                    }
                    System.out.println("監控被中斷: " + e.getMessage());
                    break;
                } catch (ClosedWatchServiceException e) {
                    System.out.println("WatchService 已關閉，退出監控");
                    break;
                }

                for (WatchEvent<?> event : key.pollEvents()) {
                    WatchEvent.Kind<?> kind = event.kind();
                    if (kind == StandardWatchEventKinds.OVERFLOW) {
                        System.out.println("事件溢出，可能遺漏部分變更。");
                        continue;
                    }

                    Path changedFileName = (Path) event.context();
                    Path changedFilePath = directoryToTrack.resolve(changedFileName);

                    if (originalToTempMap.containsKey(changedFilePath)) {
                        long currentTime = System.currentTimeMillis();
                        Long lastProcessed = lastProcessedTimestamps.getOrDefault(changedFilePath, 0L);


                        if ((currentTime - lastProcessed) < DEBOUNCE_TIME_MS) {
                            System.out.println("忽略重複事件: " + changedFilePath + "（距離上次處理不足 " + DEBOUNCE_TIME_MS + "ms）");
                            continue;
                        }

                        System.out.println("\n檢測到變更: " + kind + " 在檔案 " + changedFilePath);

                        Path originalFile = originalToTempMap.get(changedFilePath);
                        String diffSummary = diffService.generateShortDiffSummary(originalFile, changedFilePath);
                        System.out.println("差異摘要: " + diffSummary);

                        if (!diffSummary.contains("沒有差異")) {
                            String diff = diffService.generateDiff(originalFile, changedFilePath);
                            System.out.println("詳細差異內容:\n" + diff);

                            String commitMessage = commitMessageService.generateCommitMessage(originalFile, changedFilePath);
                            System.out.println("生成的 Commit 訊息 (檔案 " + changedFilePath.getFileName() + "):");
                            System.out.println(commitMessage);
                            synchronized (individualCommitMessages) {
                                individualCommitMessages.add(commitMessage);
                            }


                            lastProcessedTimestamps.put(changedFilePath, currentTime);
                        }
                    }
                }

                boolean valid = key.reset();
                if (!valid) {
                    System.out.println("WatchKey 無效，停止監控");
                    break;
                }
            }

            // cleanup
            cleanup(originalToTempMap, watchService);
            System.out.println("程式已退出。");
        };
    }

    // get directory to track from user function
    private Path getDirectoryToTrackFromUser() {
        Scanner scanner = new Scanner(System.in);
        System.out.println("請輸入要監控的目錄路徑（例如: src/main/java/com/example/commitmessagegenerator/Service）：");

        String input = scanner.nextLine().trim();
        if (input.isEmpty()) {
            System.out.println("輸入為空，請提供有效目錄路徑。");
            return null;
        }

        try {
            Path dirPath = Paths.get(input).toAbsolutePath().normalize();
            if (Files.exists(dirPath) && Files.isDirectory(dirPath)) {
                System.out.println("已選擇目錄: " + dirPath);
                return dirPath;
            } else {
                System.out.println("路徑不存在或不是目錄: " + input);
                return null;
            }
        } catch (InvalidPathException e) {
            System.out.println("路徑格式錯誤: " + input + "，請檢查輸入。");
            return null;
        }
    }

    // scan java files function
    private List<Path> scanJavaFiles(Path directory) {
        try {
            return Files.walk(directory, 1)
                    .filter(Files::isRegularFile)
                    .filter(path -> path.toString().endsWith(".java"))
                    .collect(Collectors.toList());
        } catch (IOException e) {
            System.err.println("掃描目錄時發生錯誤: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    // listen for user input function
    private Thread startInputListener(CommitMessageService commitMessageService, List<String> commitMessages) {
        Thread thread = new Thread(() -> {
            Scanner scanner = new Scanner(System.in);
            while (running) {
                String input = scanner.nextLine().trim();
                if ("done".equalsIgnoreCase(input)) {
                    synchronized (commitMessages) {
                        if (!commitMessages.isEmpty()) {
                            String finalCommitMessage = commitMessageService.combineCommitMessages(commitMessages);
                            System.out.println("\n最終合併的 Commit 訊息:");
                            System.out.println(finalCommitMessage);
                            commitMessages.clear();
                            System.out.println("已生成最終訊息，請繼續修改檔案或輸入 'exit' 退出。");
                        } else {
                            System.out.println("目前沒有 commit 訊息可合併，請先修改檔案。");
                        }
                    }
                } else if ("exit".equalsIgnoreCase(input)) {
                    System.out.println("正在退出程式...");
                    running = false;
                    break;
                }
            }
        });
        thread.setDaemon(true);
        thread.start();
        return thread;
    }

    // cleanup function
    private void cleanup(Map<Path, Path> originalToTempMap, WatchService watchService) throws IOException {
        try {
            for (Path tempFile : originalToTempMap.values()) {
                Files.deleteIfExists(tempFile);
                System.out.println("已清理臨時檔案: " + tempFile);
            }
            watchService.close();
            System.out.println("WatchService 已關閉。");
        } catch (IOException e) {
            System.err.println("清理資源時發生錯誤: " + e.getMessage());
        }
    }
}