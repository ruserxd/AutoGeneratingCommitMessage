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
}
