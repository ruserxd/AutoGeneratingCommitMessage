import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";

const execPromise = promisify(exec);

// 定義常數
const JAVA_FILE_EXTENSION = ".java";

// 定義 Git指令
const GIT_COMMANDS = {
  UNSTAGED_FILES: `git ls-files --modified --others --exclude-standard -- "*.java"`,
  STAGED_FILES: `git diff --cached --name-only -- "*.java"`,
  ADD_FILE: (filePath: string) => `git add "${filePath}"`,
  RESET_FILE: (filePath: string) => `git reset HEAD -- "${filePath}"`,
} as const;

// 定義訊息類型
interface WebviewMessage {
  command: string;
  data?: string;
  file?: string;
  error?: string;
}

export class GitOperations {
  /**
   * 獲取 Git 狀態並更新 WebView
   */
  public async handleGetGitStatus(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    console.log("handleGetGitStatus called");

    this.sendMessage(webviewView, {
      command: "updateStatus",
      data: "正在獲取 Java 檔案的 Git 狀態資訊...",
    });

    try {
      const unstagedFiles = await this.getUnstagedJavaFiles();
      const formattedStatus = this.formatUnstagedFilesStatus(unstagedFiles);

      this.sendMessage(webviewView, {
        command: "updateStatus",
        data: formattedStatus,
      });

      await this.refreshStagedFiles(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "Git 操作失敗");
    }
  }

  /**
   * 刷新已暫存的檔案列表
   */
  public async refreshStagedFiles(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    try {
      const stagedFiles = await this.getStagedJavaFiles();

      this.sendMessage(webviewView, {
        command: "sendData",
        data: stagedFiles.join("\n"),
      });
    } catch (error) {
      this.handleError(error, webviewView, "刷新 Stage 區域失敗");
    }
  }

  /**
   * 初始化 Stage 狀態
   */
  public async handleInitStage(webviewView: vscode.WebviewView): Promise<void> {
    await this.refreshStagedFiles(webviewView);
  }

  /**
   * 添加檔案到 Stage 區
   */
  public async handleAddStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ): Promise<void> {
    if (!this.isJavaFile(filePath)) {
      const errorMsg = "只能加入 Java 檔案";
      vscode.window.showInformationMessage(`${errorMsg}：${filePath}`);
      this.sendStageErrorMessage(webviewView, filePath, errorMsg);
      return;
    }

    try {
      await this.executeGitCommand(GIT_COMMANDS.ADD_FILE(filePath));
      await this.refreshAfterStageOperation(webviewView);

      this.sendMessage(webviewView, {
        command: "stageComplete",
        file: filePath,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      this.handleError(error, webviewView, "執行 git add 錯誤");
      this.sendStageErrorMessage(webviewView, filePath, errorMessage);
    }
  }

  /**
   * 從 Stage 區移除檔案
   */
  public async handleRemoveFromStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ): Promise<void> {
    if (!this.isJavaFile(filePath)) {
      this.sendUnstageErrorMessage(webviewView, filePath, "只能移除 Java 檔案");
      return;
    }

    try {
      const sanitizedPath = this.sanitizeFilePath(filePath);
      await this.executeGitCommand(GIT_COMMANDS.RESET_FILE(sanitizedPath));
      await this.refreshAfterStageOperation(webviewView);

      this.sendMessage(webviewView, {
        command: "unstageComplete",
        file: filePath,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("Git unstage error:", error);
      this.handleError(error, webviewView, "從 Stage 區移除檔案失敗");
      this.sendUnstageErrorMessage(webviewView, filePath, errorMessage);
    }
  }

  /**
   * 顯示檔案差異
   */
  public async handleShowDiff(filePath: string): Promise<void> {
    if (!this.isJavaFile(filePath)) {
      vscode.window.showInformationMessage(
        `只能顯示 Java 檔案的差異：${filePath}`
      );
      return;
    }

    try {
      await this.openFileAndShowDiff(filePath);
    } catch (error) {
      this.handleError(error, null, "顯示檔案差異失敗");
    }
  }

  /**
   * 獲取未暫存的 Java 檔案列表
   */
  private async getUnstagedJavaFiles(): Promise<string[]> {
    const { stdout } = await this.executeGitCommand(
      GIT_COMMANDS.UNSTAGED_FILES
    );
    return this.parseFileList(stdout);
  }

  /**
   * 獲取已暫存的 Java 檔案列表
   */
  private async getStagedJavaFiles(): Promise<string[]> {
    const { stdout } = await this.executeGitCommand(GIT_COMMANDS.STAGED_FILES);
    return this.parseFileList(stdout);
  }

  /**
   * 解析檔案列表字串
   */
  private parseFileList(fileListString: string): string[] {
    return fileListString
      .split("\n")
      .map((file) => file.trim())
      .filter((file) => file && file.endsWith(JAVA_FILE_EXTENSION));
  }

  /**
   * 格式化未暫存檔案狀態訊息
   */
  private formatUnstagedFilesStatus(files: string[]): string {
    if (files.length === 0) {
      return "沒有未加入 Stage 的 Java 檔案";
    }

    return (
      "未加入 Stage 的 Java 檔案：\n" +
      files.map((file) => `  ${file}`).join("\n")
    );
  }

  /**
   * 執行 Git 命令
   */
  private async executeGitCommand(
    command: string
  ): Promise<{ stdout: string; stderr: string }> {
    return await execPromise(command, {
      cwd: WorkspaceManager.workspaceFolder,
    });
  }

  /**
   * Stage 操作後的刷新
   */
  private async refreshAfterStageOperation(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    await Promise.all([
      this.refreshStagedFiles(webviewView),
      this.handleGetGitStatus(webviewView),
    ]);
  }

  /**
   * 開啟檔案並顯示差異
   */
  private async openFileAndShowDiff(filePath: string): Promise<void> {
    const fullPath = path.join(WorkspaceManager.workspaceFolder, filePath);
    const document = await vscode.workspace.openTextDocument(fullPath);
    await vscode.window.showTextDocument(document);
    await vscode.commands.executeCommand(
      "git.openChange",
      vscode.Uri.file(fullPath)
    );
  }

  /**
   * 檢查是否為 Java 檔案
   */
  private isJavaFile(filePath: string): boolean {
    return filePath.endsWith(JAVA_FILE_EXTENSION);
  }

  /**
   * 清理檔案路徑（處理特殊字元）
   */
  private sanitizeFilePath(filePath: string): string {
    return filePath.replace(/"/g, '\\"');
  }

  /**
   * 發送訊息到 WebView
   */
  private sendMessage(
    webviewView: vscode.WebviewView,
    message: WebviewMessage
  ): void {
    webviewView.webview.postMessage(message);
  }

  /**
   * 發送 Stage 錯誤訊息
   */
  private sendStageErrorMessage(
    webviewView: vscode.WebviewView,
    filePath: string,
    error: string
  ): void {
    this.sendMessage(webviewView, {
      command: "stageError",
      file: filePath,
      error,
    });
  }

  /**
   * 發送 Unstage 錯誤訊息
   */
  private sendUnstageErrorMessage(
    webviewView: vscode.WebviewView,
    filePath: string,
    error: string
  ): void {
    this.sendMessage(webviewView, {
      command: "unstageError",
      file: filePath,
      error,
    });
  }

  /**
   * 統一的錯誤處理
   */
  private handleError(
    error: unknown,
    webviewView: vscode.WebviewView | null,
    prefix: string
  ): void {
    const errorMessage = getErrorMessage(error);
    console.error(`${prefix}:`, error);
    vscode.window.showErrorMessage(`${prefix}: ${errorMessage}`);

    if (webviewView) {
      this.sendMessage(webviewView, {
        command: "updateStatus",
        data: `Error: ${errorMessage}`,
      });
    }
  }

  /**
   * 處理方法版本歷程檢查
   */
  public async handleMethodDiffHistory(
    webviewView: vscode.WebviewView
  ): Promise<void> {
    console.log("handleMethodDiffHistory called");

    this.sendMessage(webviewView, {
      command: "updateMethodDiff",
      data: "正在獲取專案 Git Remote 資訊...",
    });

    try {
      // 獲取 git remote URL
      const remoteUrl = await this.getGitRemoteUrl();

      if (!remoteUrl) {
        this.sendMessage(webviewView, {
          command: "updateMethodDiff",
          error: "無法獲取 Git Remote URL，請確認專案已設置遠端儲存庫",
        });
        return;
      }

      this.sendMessage(webviewView, {
        command: "updateMethodDiff",
        data: `找到 Remote URL: ${remoteUrl}，正在分析方法版本歷程...`,
      });

      // 呼叫後端 API 進行分析
      const projectData = await this.callMethodDiffApi(remoteUrl);

      // 開啟瀏覽器顯示結果
      await this.openMethodDiffInBrowser(projectData);

      this.sendMessage(webviewView, {
        command: "updateMethodDiff",
        data: "方法版本歷程分析完成，已在瀏覽器中開啟結果頁面",
      });
    } catch (error) {
      this.handleError(error, webviewView, "方法版本歷程分析失敗");
    }
  }

  /**
   * 獲取 Git Remote URL
   */
  private async getGitRemoteUrl(): Promise<string | null> {
    try {
      const { stdout } = await this.executeGitCommand(
        "git remote get-url origin"
      );
      return stdout.trim();
    } catch (error) {
      console.error("獲取 Git Remote URL 失敗:", error);
      return null;
    }
  }

  /**
   * 呼叫後端 API 分析方法差異
   */
  private async callMethodDiffApi(remoteUrl: string): Promise<any> {
    const axios = require("axios");

    const response = await axios.post(
      "http://localhost:8000/api/get-method-diff-temporary",
      null,
      {
        params: {
          url: remoteUrl,
          commitId: "HEAD",
        },
        timeout: 120000, // 2分鐘超時
      }
    );

    return response.data;
  }

  /**
   * 在瀏覽器中開啟方法差異結果
   */
  private async openMethodDiffInBrowser(projectData: any): Promise<void> {
    // 建立臨時 HTML 頁面
    const htmlContent = this.generateMethodDiffHtml(projectData);

    // 建立臨時檔案
    const fs = require("fs");
    const path = require("path");
    const os = require("os");

    const tempDir = os.tmpdir();
    const tempFilePath = path.join(tempDir, `method-diff-${Date.now()}.html`);

    fs.writeFileSync(tempFilePath, htmlContent, "utf8");

    // 開啟瀏覽器
    const open = require("open");
    await open(tempFilePath);

    // 設定 5 秒後清理臨時檔案
    setTimeout(() => {
      try {
        fs.unlinkSync(tempFilePath);
      } catch (error) {
        console.log("清理臨時檔案失敗:", error);
      }
    }, 5000);
  }

  /**
   * 生成方法差異的 HTML 內容
   */
  private generateMethodDiffHtml(projectData: any): string {
    const projectName = projectData.projectName || "Unknown Project";
    const files = projectData.files || [];

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
          const commitMessage = diff.commitMessage || "";
          const commitTime = diff.commitTime
            ? new Date(diff.commitTime).toLocaleString()
            : "";
          const diffCode = diff.diffCode || "";

          diffHtml += `
          <div class="diff-item">
            <div class="commit-info">
              <div class="commit-meta">
                <span class="author">作者: ${author}</span>
                <span class="time">時間: ${commitTime}</span>
              </div>
              <div class="commit-message">${commitMessage}</div>
            </div>
            <pre class="diff-code"><code>${this.escapeHtml(
              diffCode
            )}</code></pre>
          </div>
        `;
        }

        methodsHtml += `
        <div class="method-section">
          <h3 class="method-name">${methodName}</h3>
          <div class="diff-list">
            ${diffHtml}
          </div>
        </div>
      `;
      }

      filesHtml += `
      <div class="file-section">
        <h2 class="file-name">${fileName}</h2>
        <div class="file-path">${filePath}</div>
        <div class="methods-list">
          ${methodsHtml}
        </div>
      </div>
    `;
    }

    return `
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>方法版本歷程 - ${projectName}</title>
      <style>
        body {
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          margin: 0;
          padding: 20px;
          background-color: #f5f5f5;
          line-height: 1.6;
        }
        .container {
          max-width: 1200px;
          margin: 0 auto;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          padding: 30px;
        }
        .project-title {
          color: #2c3e50;
          border-bottom: 3px solid #5680E9;
          padding-bottom: 15px;
          margin-bottom: 30px;
        }
        .file-section {
          margin-bottom: 40px;
          border: 1px solid #e1e1e1;
          border-radius: 6px;
          overflow: hidden;
        }
        .file-name {
          background: #5680E9;
          color: white;
          margin: 0;
          padding: 15px 20px;
          font-size: 1.2em;
        }
        .file-path {
          background: #f8f9fa;
          padding: 10px 20px;
          font-family: 'Courier New', monospace;
          font-size: 0.9em;
          color: #6c757d;
          border-bottom: 1px solid #e1e1e1;
        }
        .methods-list {
          padding: 20px;
        }
        .method-section {
          margin-bottom: 30px;
          border-left: 4px solid #17a2b8;
          padding-left: 20px;
        }
        .method-name {
          color: #17a2b8;
          margin: 0 0 15px 0;
          font-size: 1.1em;
        }
        .diff-item {
          background: #f8f9fa;
          border: 1px solid #e9ecef;
          border-radius: 4px;
          margin-bottom: 15px;
          overflow: hidden;
        }
        .commit-info {
          padding: 15px;
          background: white;
        }
        .commit-meta {
          display: flex;
          gap: 20px;
          margin-bottom: 8px;
          font-size: 0.9em;
        }
        .author {
          color: #28a745;
          font-weight: bold;
        }
        .time {
          color: #6c757d;
        }
        .commit-message {
          color: #495057;
          font-style: italic;
        }
        .diff-code {
          margin: 0;
          padding: 15px;
          background: #272822;
          color: #f8f8f2;
          overflow-x: auto;
          font-family: 'Courier New', monospace;
          font-size: 0.85em;
          line-height: 1.4;
        }
        .diff-code code {
          background: none;
          color: inherit;
        }
        /* Git diff 語法高亮 */
        .diff-code {
          background: #1e1e1e;
        }
        .no-files {
          text-align: center;
          color: #6c757d;
          padding: 40px;
          font-style: italic;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1 class="project-title">方法版本歷程分析 - ${projectName}</h1>
        ${
          files.length > 0
            ? filesHtml
            : '<div class="no-files">此專案沒有找到可分析的 Java 方法</div>'
        }
      </div>
    </body>
    </html>
  `;
  }

  /**
   * HTML 字符轉義
   */
  private escapeHtml(unsafe: string): string {
    return unsafe
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}
