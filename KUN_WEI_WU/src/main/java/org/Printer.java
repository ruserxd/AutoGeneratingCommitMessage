package org;

import java.util.List;

// 輸出格式化
public class Printer {
    static void printLine(List<String> lines, String title) {
        System.out.println("-----------------------");
        if (title != null && !title.isEmpty()) System.out.println(title + ":");
        for (String line : lines) {
            System.out.println(line);
        }
        System.out.println("-----------------------");
    }

    static void printString(String str, String title) {
        System.out.println("-----------------------");
        if (title != null && !title.isEmpty()) System.out.println(title + ":");
        System.out.println(str);
        System.out.println("-----------------------");
    }

    static String stringListToString(List<String> stringList) {
        return String.join("\n", stringList);
    }

    static void printCommitMessage(String commitMessage) {
        System.out.println("-----------------------");
        System.out.format("\33[32;4m" + commitMessage + "\33[0m%n");
        System.out.println("-----------------------");
    }
}
