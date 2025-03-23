package com.example.commitmessagegenerator.Service;

import com.example.commitmessagegenerator.Util.FileUtil;
import com.github.difflib.DiffUtils;
import com.github.difflib.patch.AbstractDelta;
import com.github.difflib.patch.DeltaType;
import com.github.difflib.patch.Patch;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class DiffService {

    private final FileUtil fileUtil;

    public DiffService(FileUtil fileUtil) {
        this.fileUtil = fileUtil;
    }

    public String generateDiff(Path file1, Path file2) throws IOException {
        List<String> file1Lines = fileUtil.readLines(file1);
        List<String> file2Lines = fileUtil.readLines(file2);

        // generate diff
        Patch<String> patch = DiffUtils.diff(file1Lines, file2Lines);

        StringBuilder diffBuilder = new StringBuilder();
        diffBuilder.append("比較檔案:\n");
        diffBuilder.append("檔案1: ").append(file1.getFileName()).append("\n");
        diffBuilder.append("檔案2: ").append(file2.getFileName()).append("\n\n");

        if (patch.getDeltas().isEmpty()) {
            diffBuilder.append("檔案之間沒有差異\n");
            return diffBuilder.toString();
        }

        for (AbstractDelta<String> delta : patch.getDeltas()) {
            DeltaType effectiveType = delta.getType();
            if (delta.getType() == DeltaType.CHANGE) {
                List<String> sourceLines = delta.getSource().getLines();
                List<String> targetLines = delta.getTarget().getLines();
                // Check if the CHANGE is actually an INSERT before the last line
                if (sourceLines.size() == 1 && sourceLines.get(0).trim().equals("}") &&
                        targetLines.size() > 1 && targetLines.get(targetLines.size() - 1).trim().equals("}")) {
                    effectiveType = DeltaType.INSERT;
                }
            }

            diffBuilder.append("變更類型: ").append(deltaTypeToString(effectiveType)).append("\n");

            // Calculate the start and end line numbers based on the delta type
            int startLine, endLine;
            if (effectiveType == DeltaType.INSERT) {

                startLine = delta.getTarget().getPosition() + 1;
                endLine = delta.getTarget().getPosition() + delta.getTarget().size();
            } else {
                startLine = delta.getSource().getPosition() + 1;
                endLine = delta.getSource().getPosition() + delta.getSource().size();
            }

            diffBuilder.append("位置: 行 ").append(startLine)
                    .append(" 到 ").append(endLine).append("\n");

            if (!delta.getSource().getLines().isEmpty() && effectiveType != DeltaType.INSERT) {
                diffBuilder.append("檔案1 內容:\n");
                diffBuilder.append(delta.getSource().getLines().stream()
                        .map(line -> "- " + line)
                        .collect(Collectors.joining("\n")));
                diffBuilder.append("\n");
            }

            if (!delta.getTarget().getLines().isEmpty()) {
                diffBuilder.append("檔案2 內容:\n");
                // For the reclassified INSERT, exclude the last line (closing brace) from display
                List<String> targetLinesToShow = delta.getTarget().getLines();
                if (effectiveType == DeltaType.INSERT && targetLinesToShow.get(targetLinesToShow.size() - 1).trim().equals("}")) {
                    targetLinesToShow = targetLinesToShow.subList(0, targetLinesToShow.size() - 1);
                }
                diffBuilder.append(targetLinesToShow.stream()
                        .map(line -> "+ " + line)
                        .collect(Collectors.joining("\n")));
                diffBuilder.append("\n");
            }

            diffBuilder.append("\n");
        }

        return diffBuilder.toString();
    }

    private String deltaTypeToString(DeltaType type) {
        return switch (type) {
            case INSERT -> "新增";
            case DELETE -> "刪除";
            case CHANGE -> "修改";
            default -> type.toString();
        };
    }

    public String generateShortDiffSummary(Path file1, Path file2) throws IOException {
        List<String> file1Lines = fileUtil.readLines(file1);
        List<String> file2Lines = fileUtil.readLines(file2);

        Patch<String> patch = DiffUtils.diff(file1Lines, file2Lines);

        if (patch.getDeltas().isEmpty()) {
            return "檔案 " + file1.getFileName() + " 和 " + file2.getFileName() + " 之間沒有差異";
        }

        int additions = 0;
        int deletions = 0;
        int modifications = 0;

        for (AbstractDelta<String> delta : patch.getDeltas()) {
            // Reclassify certain CHANGE operations as INSERT for summary purposes
            DeltaType effectiveType = delta.getType();
            if (delta.getType() == DeltaType.CHANGE) {
                List<String> sourceLines = delta.getSource().getLines();
                List<String> targetLines = delta.getTarget().getLines();
                if (sourceLines.size() == 1 && sourceLines.get(0).trim().equals("}") &&
                        targetLines.size() > 1 && targetLines.get(targetLines.size() - 1).trim().equals("}")) {
                    effectiveType = DeltaType.INSERT;
                }
            }

            switch (effectiveType) {
                case INSERT:
                    additions += delta.getTarget().size();
                    // If reclassified as INSERT, subtract the closing brace line
                    if (effectiveType == DeltaType.INSERT && delta.getType() == DeltaType.CHANGE) {
                        additions -= 1; // Exclude the closing brace
                    }
                    break;
                case DELETE:
                    deletions += delta.getSource().size();
                    break;
                case CHANGE:
                    modifications += Math.max(delta.getSource().size(), delta.getTarget().size());
                    break;
            }
        }

        StringBuilder summary = new StringBuilder();
        summary.append("檔案差異摘要: ");

        if (additions > 0) {
            summary.append(additions).append(" 行新增 ");
        }
        if (deletions > 0) {
            summary.append(deletions).append(" 行刪除 ");
        }
        if (modifications > 0) {
            summary.append(modifications).append(" 行修改 ");
        }

        if (additions == 0 && deletions == 0 && modifications == 0) {
            summary.append("無變更");
        }

        return summary.toString().trim();
    }
}