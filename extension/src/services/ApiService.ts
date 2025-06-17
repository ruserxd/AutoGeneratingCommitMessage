import * as vscode from "vscode";
import axios, { AxiosInstance } from "axios";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";

const execPromise = promisify(exec);
const API_BASE_URL = "http://localhost:8080";

export class ApiService {
  private httpClient: AxiosInstance;

  constructor() {
    this.httpClient = axios.create({
      baseURL: API_BASE_URL,
      timeout: 60000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  public async handleGenerateCommit(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    webviewView.webview.postMessage({
      command: "updateCommit",
      data: "正在生成 Java 檔案的 Commit Message...",
    });

    try {
      const javaFiles = await this.getStagedJavaFiles();

      if (javaFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateCommit",
          data: "沒有 Java 檔案被加入到 Stage 區，無法生成 Commit Message。",
        });
        return;
      }

      const diffInfo = await this.getJavaDiffInfo();

      const commitMessage = await this.getCommitMessage(diffInfo);

      webviewView.webview.postMessage({
        command: "updateCommit",
        data: commitMessage,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("生成 Commit Message 失敗:", error);
      webviewView.webview.postMessage({
        command: "updateCommit",
        data: `生成失敗: ${errorMessage}`,
      });
    }
  }

  public async handleGenerateSummary(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    webviewView.webview.postMessage({
      command: "updateSummary",
      data: "正在分析修改內容...",
    });

    try {
      const stagedFiles = await this.getStagedJavaFiles();

      if (stagedFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateSummary",
          data: "沒有 Java 檔案被加入到 Stage 區，無法生成摘要。",
        });
        return;
      }

      // 收集所有檔案的 diff 資訊
      const filesDiffData: { file: string; diff: string }[] = [];

      for (const file of stagedFiles) {
        try {
          webviewView.webview.postMessage({
            command: "updateSummary",
            data: `正在獲取 ${file} 的修改內容...`,
          });

          const fileDiff = await this.getFileDiffInfo(file);
          if (fileDiff.trim()) {
            filesDiffData.push({
              file: file,
              diff: fileDiff,
            });
          }
        } catch (error) {
          console.error(`獲取檔案 ${file} diff 時發生錯誤:`, error);
          filesDiffData.push({
            file: file,
            diff: `Error: ${getErrorMessage(error)}`,
          });
        }
      }

      if (filesDiffData.length === 0) {
        webviewView.webview.postMessage({
          command: "updateSummary",
          data: "所有檔案都沒有修改內容",
        });
        return;
      }

      // 一次性傳送所有檔案的 diff 資訊給後端
      webviewView.webview.postMessage({
        command: "updateSummary",
        data: "正在生成修改摘要...",
      });

      const summary = await this.getBatchFilesSummary(filesDiffData);

      webviewView.webview.postMessage({
        command: "updateSummary",
        data: summary,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("生成修改摘要失敗:", error);
      webviewView.webview.postMessage({
        command: "updateSummary",
        data: `生成失敗: ${errorMessage}`,
      });
    }
  }

  // 獲取已暫存的 Java 檔案
  private async getStagedJavaFiles(): Promise<string[]> {
    const { stdout: stagedFiles } = await execPromise(
      `git diff --cached --name-only -- "*.java"`,
      { cwd: WorkspaceManager.workspaceFolder }
    );

    return stagedFiles
      .split("\n")
      .filter((file) => file.trim() && file.endsWith(".java"));
  }

  // 獲取 Java 檔案的 diff 資訊
  private async getJavaDiffInfo(): Promise<string> {
    const { stdout: diffInfo } = await execPromise(
      `git diff --cached -- "*.java"`,
      { cwd: WorkspaceManager.workspaceFolder }
    );
    return diffInfo;
  }

  // 獲取特定檔案的 diff 資訊
  private async getFileDiffInfo(filePath: string): Promise<string> {
    const { stdout: diffInfo } = await execPromise(
      `git diff --cached -- "${filePath}"`,
      { cwd: WorkspaceManager.workspaceFolder }
    );
    return diffInfo;
  }

  // 統一的 API 請求處理
  private async makeApiRequest(endpoint: string, data: any): Promise<string> {
    try {
      const response = await this.httpClient.post(endpoint, data);
      return response.data;
    } catch (error) {
      throw new Error(`API 請求失敗: ${getErrorMessage(error)}`);
    }
  }

  // 生成 CommitMessage
  private async getCommitMessage(diffInfo: string): Promise<string> {
    if (!diffInfo.trim()) {
      return "無法生成 Commit Message：沒有 Java 檔案變更";
    }

    try {
      return await this.makeApiRequest("/getCommitMessage", { diffInfo });
    } catch (error) {
      return `連接後端服務失敗: ${getErrorMessage(error)}`;
    }
  }

  // 生成各個檔案的摘要
  private async getBatchFilesSummary(
    filesDiffData: { file: string; diff: string }[]
  ): Promise<string> {
    if (filesDiffData.length === 0) {
      return "無修改內容";
    }

    try {
      return await this.makeApiRequest("/getBatchFilesSummary", {
        filesDiffData,
      });
    } catch (error) {
      return `連接後端服務失敗: ${getErrorMessage(error)}`;
    }
  }
}
