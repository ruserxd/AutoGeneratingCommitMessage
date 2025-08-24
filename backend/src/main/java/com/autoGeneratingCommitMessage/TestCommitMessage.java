package com.autoGeneratingCommitMessage;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;

public class TestCommitMessage {

  // 測試用
  private static String readDiffFile(String filePath) throws IOException {
    return Files.readString(Paths.get(filePath));
  }

  public static void main(String[] args) throws IOException {
    LangChain langChain = new LangChain();
    //langChain.generateCommitMessageByNoIntegrate(
     //   readDiffFile("src/main/resources/diffData/car_diff_name.txt"));
  }
}
