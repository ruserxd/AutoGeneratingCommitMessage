import * as vscode from "vscode";
import axios from "axios";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";

const execPromise = promisify(exec);
const API_BASE_URL = "http://localhost:8080";

export class ApiService {
  private _cachedDiffInfo: string = "";

  public async handleGetGreetCommand(webviewView: vscode.WebviewView) {
    try {
      const response = await axios.get("http://localhost:8000/api/greet");
      webviewView.webview.postMessage({
        command: "greetResult",
        message: response.data,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("Failed to fetch greeting:", error);
      webviewView.webview.postMessage({
        command: "greetResult",
        error: `Failed to fetch greeting: ${errorMessage}`,
      });
    }
  }

  public async handleGenerateCommit(webviewView: vscode.WebviewView) {
    webviewView.webview.postMessage({
      command: "updateCommit",
      data: "正在生成 Java 檔案的 Commit Message...",
    });

    try {
      const { stdout: stagedFiles } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: WorkspaceManager.workspaceFolder }
      );

      const javaFiles = stagedFiles
        .split("\n")
        .filter((file) => file.trim() && file.endsWith(".java"));

      if (javaFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateCommit",
          data: "沒有 Java 檔案被加入到 Stage 區，無法生成 Commit Message。",
        });
        return;
      }

      const { stdout: diffInfo } = await execPromise(
        `git diff --cached -- "*.java"`,
        { cwd: WorkspaceManager.workspaceFolder }
      );

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

  public async handleGenerateWhy(webviewView: vscode.WebviewView) {
    webviewView.webview.postMessage({
      command: "updateWhy",
      data: "正在分析修改的原因...",
    });

    try {
      const { stdout: stagedFiles } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: WorkspaceManager.workspaceFolder }
      );

      const javaFiles = stagedFiles
        .split("\n")
        .filter((file) => file.trim().endsWith(".java"));

      if (javaFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateWhy",
          data: "沒有 Java 檔案被加入到 Stage 區，無法生成 Why 說明。",
        });
        return;
      }

      let combinedDiffInfo = "";
      for (const file of javaFiles) {
        let oldContent = "";
        try {
          const { stdout } = await execPromise(`git show HEAD:${file}`, {
            cwd: WorkspaceManager.workspaceFolder,
          });
          oldContent = stdout;
        } catch (e) {
          oldContent = "";
        }

        const { stdout: diffContent } = await execPromise(
          `git diff --cached "${file}"`,
          { cwd: WorkspaceManager.workspaceFolder }
        );

        combinedDiffInfo += `===== 檔案：${file} =====\n[原始內容]\n${oldContent}\n[差異內容]\n${diffContent}\n\n`;
      }

      const whyMessage = await this.getWhyReason(combinedDiffInfo);
      webviewView.webview.postMessage({
        command: "updateWhy",
        data: whyMessage,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("生成 Why 說明失敗:", error);
      webviewView.webview.postMessage({
        command: "updateWhy",
        data: `生成失敗: ${errorMessage}`,
      });
    }
  }

  private async getCommitMessage(diffInfo: string): Promise<string> {
    if (!diffInfo.trim()) return "無法生成 Commit Message：沒有 Java 檔案變更";

    try {
      const response = await fetch(`${API_BASE_URL}/getCommitMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diffInfo }),
      });

      if (response.ok) return await response.text();
      throw new Error(`請求失敗: ${response.status} ${response.statusText}`);
    } catch (error) {
      return `連接後端服務失敗: ${getErrorMessage(error)}`;
    }
  }

  private async getWhyReason(diffInfo: string): Promise<string> {
    if (!diffInfo.trim()) return "無法生成修改原因：沒有檔案變更內容";

    try {
      const response = await fetch(`${API_BASE_URL}/getWhyReason`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ diffInfo }),
      });

      if (response.ok) return await response.text();
      throw new Error(`請求失敗: ${response.status} ${response.statusText}`);
    } catch (error) {
      return `連接後端服務失敗: ${getErrorMessage(error)}`;
    }
  }
}
