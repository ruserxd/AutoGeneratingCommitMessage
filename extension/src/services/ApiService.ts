import * as vscode from "vscode";
import axios, { AxiosInstance } from "axios";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";
import * as path from "path";

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

  // ApiService.ts（節錄：class ApiService 內）
  // 允許外部丟進 model（數字編號或名稱）；不丟就沿用預設
  public async handleGenerateCommit(
    webviewView: vscode.WebviewView,
    modelName?: string
  ): Promise<void> {
    webviewView.webview.postMessage({
      command: "updateCommit",
      data: "正在生成 Java 檔案的 Commit Message.",
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
      const commitMessage = await this.getCommitMessage(diffInfo, modelName);

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

  // ✅ 新增參數 model，可為 number | string；會一起 POST 給後端
  private async getCommitMessage(
    diffInfo: string,
    modelName?: string
  ): Promise<string> {
    const body: any = { diffInfo };
    if (modelName && modelName.trim()) {
      body.modelName = modelName.trim();
    }
    return await this.makeApiRequest("/getCommitMessage", body);
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

  /**
   * 處理方法版本歷程檢查 - 直接顯示結果
   */
  public async handleMethodDiffHistory(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    webviewView.webview.postMessage({
      command: "updateMethodDiff",
      data: "正在獲取專案 Git Remote 資訊...",
    });

    try {
      // 獲取 git remote URL
      const remoteUrl = await this.getGitRemoteUrl();

      if (!remoteUrl) {
        webviewView.webview.postMessage({
          command: "updateMethodDiff",
          data: "無法獲取 Git Remote URL，請確認專案已設置遠端儲存庫",
        });
        return;
      }

      webviewView.webview.postMessage({
        command: "updateMethodDiff",
        data: `找到 Remote URL: ${remoteUrl}，正在分析方法版本歷程...`,
      });

      // 呼叫 port 8000 的 API
      const response = await this.httpClient.post(
        "http://localhost:8000/api/get-method-diff-temporary",
        null,
        {
          params: {
            url: remoteUrl,
            commitId: "HEAD",
          },
          timeout: 120000,
        }
      );

      // 直接開啟瀏覽器顯示結果
      await this.openMethodDiffInBrowser(response.data);

      webviewView.webview.postMessage({
        command: "updateMethodDiff",
        data: "方法版本歷程分析完成，已在瀏覽器中開啟結果",
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("方法版本歷程分析失敗:", error);
      webviewView.webview.postMessage({
        command: "updateMethodDiff",
        data: `分析失敗: ${errorMessage}`,
      });
    }
  }

  /**
   * 在瀏覽器中開啟方法差異結果 - 使用外部模板
   */
  private async openMethodDiffInBrowser(projectData: any): Promise<void> {
    const fs = require("fs");
    const path = require("path");
    const os = require("os");

    // 讀取 HTML 模板
    const templatePath = path.join(
      __dirname,
      "../../src/templates/method-diff.html"
    );
    let htmlTemplate = fs.readFileSync(templatePath, "utf8");

    // 生成內容
    const content = this.generateContentHtml(projectData);

    // 替換模板變數
    const htmlContent = htmlTemplate
      .replace(
        /\{\{PROJECT_NAME\}\}/g,
        this.escapeHtml(projectData.projectName || "Unknown Project")
      )
      .replace(/\{\{CONTENT\}\}/g, content);

    // 建立臨時檔案
    const tempDir = os.tmpdir();
    const tempFilePath = path.join(tempDir, `method-diff-${Date.now()}.html`);

    fs.writeFileSync(tempFilePath, htmlContent, "utf8");

    // 開啟瀏覽器
    const vscode = require("vscode");
    const uri = vscode.Uri.file(tempFilePath);
    await vscode.env.openExternal(uri);

    // 清理臨時檔案
    setTimeout(() => {
      try {
        fs.unlinkSync(tempFilePath);
        console.log("已清理臨時檔案:", tempFilePath);
      } catch (error) {
        console.log("清理臨時檔案失敗:", error);
      }
    }, 10000);
  }

  /**
   * 生成內容 HTML（只有主體部分）
   */
  private generateContentHtml(projectData: any): string {
    const files = projectData.files || [];

    if (files.length === 0) {
      return '<div class="no-files">此專案沒有找到可分析的 Java 方法</div>';
    }

    let filesHtml = "";

    for (const file of files) {
      const fileName = file.fileName || "Unknown File";
      const filePath = file.filePath || "";
      const methods = file.methods || [];

      let methodsHtml = "";

      for (const method of methods) {
        const methodName = method.methodName || "Unknown Method";
        const diffList = method.diffInfoList || [];

        let diffHtml = "";

        for (const diff of diffList) {
          const author = diff.author || "Unknown";
          const authorEmail = diff.authorEmail || "";
          const commitMessage = diff.commitMessage || "";
          const commitTime = diff.commitTime
            ? new Date(diff.commitTime).toLocaleString("zh-TW")
            : "";
          const headRevstr = diff.headRevstr || "";
          const diffCode = diff.diffCode || "";

          diffHtml += `
          <div class="diff-card">
            <div class="diff-header">
              <div class="commit-meta">
                <span class="author">${this.escapeHtml(author)}</span>
                <span class="email">(${this.escapeHtml(authorEmail)})</span>
                <span class="time">${commitTime}</span>
                <span class="commit-hash">${headRevstr.substring(0, 8)}</span>
              </div>
              <div class="commit-message">${this.escapeHtml(
                commitMessage
              )}</div>
            </div>
            ${
              diffCode
                ? `<pre class="diff-code"><code>${this.escapeHtml(
                    diffCode
                  )}</code></pre>`
                : ""
            }
          </div>
        `;
        }

        methodsHtml += `
        <div class="method-section">
          <h3 class="method-title">${this.escapeHtml(methodName)}</h3>
          <div class="diff-count">共 ${diffList.length} 次修改</div>
          <div class="diff-list">
            ${diffHtml || '<div class="no-diff">此方法沒有差異記錄</div>'}
          </div>
        </div>
      `;
      }

      filesHtml += `
      <div class="file-section">
        <h2 class="file-title">${this.escapeHtml(fileName)}</h2>
        <div class="file-path">${this.escapeHtml(filePath)}</div>
        <div class="methods-container">
          ${methodsHtml || '<div class="no-methods">此檔案沒有找到方法</div>'}
        </div>
      </div>
    `;
    }

    return filesHtml;
  }

  /**
   * HTML 字符轉義
   */
  private escapeHtml(unsafe: string): string {
    if (typeof unsafe !== "string") return "";
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  /**
   * 獲取 Git Remote URL
   */
  private async getGitRemoteUrl(): Promise<string | null> {
    try {
      const { stdout } = await execPromise("git remote get-url origin", {
        cwd: WorkspaceManager.workspaceFolder,
      });
      return stdout.trim();
    } catch (error) {
      console.error("獲取 Git Remote URL 失敗:", error);
      return null;
    }
  }
}
