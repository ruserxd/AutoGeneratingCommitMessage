import * as vscode from "vscode";
import * as path from "path";
import { exec } from "child_process";
import { promisify } from "util";
import { WorkspaceManager } from "../utils/WorkspaceManager";
import { getErrorMessage } from "../utils/ErrorHandler";

const execPromise = promisify(exec);

export class GitOperations {
  public async handleGetGitStatus(webviewView: vscode.WebviewView) {
    console.log("handleGetGitStatus called");
    webviewView.webview.postMessage({
      command: "updateStatus",
      data: "正在獲取 Java 檔案的 Git 狀態資訊...",
    });

    try {
      const { stdout: unstagedFiles } = await execPromise(
        `git ls-files --modified --others --exclude-standard -- "*.java"`,
        { cwd: WorkspaceManager.workspaceFolder }
      );

      const formattedStatus = unstagedFiles.trim()
        ? "未加入 Stage 的 Java 檔案：\n" +
          unstagedFiles
            .split("\n")
            .filter((file) => file.trim())
            .map((file) => `  ${file}`)
            .join("\n")
        : "沒有未加入 Stage 的 Java 檔案";

      webviewView.webview.postMessage({
        command: "updateStatus",
        data: formattedStatus,
      });

      await this.refreshStagedFiles(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "Git 操作失敗");
    }
  }

  public async refreshStagedFiles(webviewView: vscode.WebviewView) {
    try {
      const { stdout } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: WorkspaceManager.workspaceFolder }
      );

      webviewView.webview.postMessage({
        command: "sendData",
        data: stdout,
      });
    } catch (error) {
      this.handleError(error, webviewView, "刷新 Stage 區域失敗");
    }
  }

  public async handleInitStage(webviewView: vscode.WebviewView) {
    await this.refreshStagedFiles(webviewView);
  }

  public async handleAddStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    if (!filePath.endsWith(".java")) {
      vscode.window.showInformationMessage(`只能加入 Java 檔案：${filePath}`);
      webviewView.webview.postMessage({
        command: "stageError",
        file: filePath,
        error: "只能加入 Java 檔案",
      });
      return;
    }

    try {
      await execPromise(`git add "${filePath}"`, {
        cwd: WorkspaceManager.workspaceFolder,
      });

      await this.refreshStagedFiles(webviewView);
      await this.handleGetGitStatus(webviewView);

      webviewView.webview.postMessage({
        command: "stageComplete",
        file: filePath,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      this.handleError(error, webviewView, "執行 git add 錯誤");
      webviewView.webview.postMessage({
        command: "stageError",
        file: filePath,
        error: errorMessage,
      });
    }
  }

  public async handleRemoveFromStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    if (!filePath.endsWith(".java")) {
      webviewView.webview.postMessage({
        command: "unstageError",
        file: filePath,
        error: "只能移除 Java 檔案",
      });
      return;
    }

    try {
      const sanitizedPath = filePath.replace(/"/g, '\\"');
      await execPromise(`git reset HEAD -- "${sanitizedPath}"`, {
        cwd: WorkspaceManager.workspaceFolder,
      });

      await this.refreshStagedFiles(webviewView);
      await this.handleGetGitStatus(webviewView);

      webviewView.webview.postMessage({
        command: "unstageComplete",
        file: filePath,
      });
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error("Git unstage error:", error);
      this.handleError(error, webviewView, "從 Stage 區移除檔案失敗");
      webviewView.webview.postMessage({
        command: "unstageError",
        file: filePath,
        error: errorMessage,
      });
    }
  }

  public async handleShowDiff(filePath: string) {
    if (!filePath.endsWith(".java")) {
      vscode.window.showInformationMessage(
        `只能顯示 Java 檔案的差異：${filePath}`
      );
      return;
    }

    try {
      const fullPath = path.join(WorkspaceManager.workspaceFolder, filePath);
      const document = await vscode.workspace.openTextDocument(fullPath);
      await vscode.window.showTextDocument(document);
      await vscode.commands.executeCommand(
        "git.openChange",
        vscode.Uri.file(fullPath)
      );
    } catch (error) {
      this.handleError(error, null, "顯示檔案差異失敗");
    }
  }

  private handleError(
    error: unknown,
    webviewView: vscode.WebviewView | null,
    prefix: string
  ) {
    const errorMessage = getErrorMessage(error);
    console.error(`${prefix}:`, error);
    vscode.window.showErrorMessage(`${prefix}: ${errorMessage}`);
    if (webviewView) {
      webviewView.webview.postMessage({
        command: "updateStatus",
        data: `Error: ${errorMessage}`,
      });
    }
  }
}
