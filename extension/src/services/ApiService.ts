import * as vscode from "vscode";
import axios, { AxiosInstance } from "axios";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";

const execPromise = promisify(exec);
const API_BASE_URL = "http://localhost:8080";

export class ApiService {
  private _cachedDiffInfo: string = "";
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
      this._cachedDiffInfo = diffInfo;

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
      const javaFiles = await this.getStagedJavaFiles();

      if (javaFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateSummary",
          data: "沒有 Java 檔案被加入到 Stage 區，無法生成摘要。",
        });
        return;
      }

      const diffInfo = await this.getJavaDiffInfo();
      const summary = await this.getChangesSummary(diffInfo);

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

  // 生成變更摘要
  private async getChangesSummary(diffInfo: string): Promise<string> {
    if (!diffInfo.trim()) {
      return "無修改內容";
    }

    try {
      return await this.makeApiRequest("/getStagedSummary", { diffInfo });
    } catch (error) {
      return `連接後端服務失敗: ${getErrorMessage(error)}`;
    }
  }

  // 獲取快取的 diff 資訊
  public getCachedDiffInfo(): string {
    return this._cachedDiffInfo;
  }

  // 清除快取的 diff 資訊
  public clearCachedDiffInfo(): void {
    this._cachedDiffInfo = "";
  }
}
