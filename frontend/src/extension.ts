// @ts-ignore
import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { exec } from "child_process";
import { promisify } from "util";

// 將 exec 轉為 Promise 版本以便使用 async/await
const execPromise = promisify(exec);

// 工作區路徑
let workspaceFolder = "";

// 後端 API 基礎 URL
const API_BASE_URL = "http://localhost:8080";

// Extension 當被啟用時
export function activate(context: vscode.ExtensionContext) {
  // 更新工作區路徑
  updateWorkspaceFolder();

  // 註冊 Webview 視圖提供者
  const provider = new CodeManagerViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codeManagerView", provider)
  );

  // 監聽工作區變化
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      updateWorkspaceFolder();
    })
  );
}

// 更新工作區路徑的函數
function updateWorkspaceFolder() {
  if (
    vscode.workspace.workspaceFolders &&
    vscode.workspace.workspaceFolders.length > 0
  ) {
    workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
  }
}

// WebView 視圖提供者類
class CodeManagerViewProvider implements vscode.WebviewViewProvider {
  private _context: vscode.ExtensionContext;
  private _cachedDiffInfo: string = ""; // 暫存最近一次的 diff 資訊

  constructor(context: vscode.ExtensionContext) {
    this._context = context;
  }

  // 首次打開 activity bar
  async resolveWebviewView(webviewView: vscode.WebviewView) {
    // 設置 WebView 配置
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(this._context.extensionPath)],
    };

    // 設置 WebView 的 HTML 內容
    webviewView.webview.html = this.getWebviewContent(webviewView.webview);

    // 更新工作區路徑
    updateWorkspaceFolder();

    // 獲取 Java 文件列表
    try {
      const javaFiles = await vscode.workspace.findFiles("**/*.java");
      console.log("發現的 Java 文件:", javaFiles);
      console.log("cd 至" + `${workspaceFolder}`);
    } catch (error) {
      console.error("獲取 Java 檔案時出錯:", error);
    }

    // 處理 WebView 發來的消息
    webviewView.webview.onDidReceiveMessage((message) => {
      switch (message.command) {
        case "getGitStatus":
          this.handleGetGitStatus(webviewView);
          break;
        case "initStage":
          this.handleInitStage(webviewView);
          break;
        case "addStage":
          this.handleAddStage(message.file, webviewView);
          break;
        case "remove":
          this.handleRemoveFromStage(message.file, webviewView);
          break;
        case "generateCommit":
          this.handleGenerateCommit(webviewView);
          break;
        case "showDiff":
          this.handleShowDiff(message.file);
          break;
      }
    });
  }

  // 獲取 Webview 內容，引用外部 CSS 和 JS 文件
  private getWebviewContent(webview: vscode.Webview): string {
    // 獲取資源所在的目錄
    const webviewDir = vscode.Uri.joinPath(
      this._context.extensionUri,
      "src",
      "main"
    );

    // 獲取資源文件的路徑
    const htmlPath = vscode.Uri.joinPath(webviewDir, "index.html");
    const cssPath = vscode.Uri.joinPath(webviewDir, "style.css");
    const jsPath = vscode.Uri.joinPath(webviewDir, "script.js");

    // 將路徑轉換為 webview 可以使用的 URI
    const cssUri = webview.asWebviewUri(cssPath);
    const jsUri = webview.asWebviewUri(jsPath);

    try {
      // 讀取 HTML 模板文件
      const htmlContent = fs.readFileSync(htmlPath.fsPath, "utf8");
      console.log(`成功讀取 HTML 模板: ${htmlPath.fsPath}`);
      console.log(`CSS URI: ${cssUri.toString()}`);
      console.log(`JS URI: ${jsUri.toString()}`);

      // 替換 HTML 模板中的佔位符
      return htmlContent
        .replace("${cssUri}", cssUri.toString())
        .replace("${jsUri}", jsUri.toString());
    } catch (error) {
      console.error(`讀取 HTML 模板失敗: ${error}`);
      // 提供一個簡單的回退 HTML 以防文件讀取失敗
      return `
      <!DOCTYPE html>
      <html lang="zh-TW">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Git CommitMessage 生成工具</title>
          <style>
            body { font-family: system-ui; margin: 10px; }
            .error { color: red; }
          </style>
        </head>
        <body>
          <h1>載入失敗</h1>
          <div class="error">無法載入 WebView 資源，請檢查文件路徑設置。</div>
          <pre>${error}</pre>
        </body>
      </html>
    `;
    }
  }

  // 處理獲取 Git 狀態(只顯示 Java 檔案)
  private async handleGetGitStatus(webviewView: vscode.WebviewView) {
    // 顯示讀取中的狀態
    webviewView.webview.postMessage({
      command: "updateStatus",
      data: "正在獲取 Java 檔案的 Git 狀態資訊...",
    });

    try {
      // 獲取未暫存的 Java 檔案
      const { stdout: unstagedFiles } = await execPromise(
        `git ls-files --modified --others --exclude-standard -- "*.java"`,
        { cwd: workspaceFolder }
      );

      console.log("未暫存的 Java 檔案：", unstagedFiles);

      // 創建格式化的輸出
      let formattedStatus = "";

      if (unstagedFiles.trim() === "") {
        formattedStatus = "沒有未加入 Stage 的 Java 檔案";
      } else {
        formattedStatus = "未加入 Stage 的 Java 檔案：\n";
        unstagedFiles.split("\n").forEach((file) => {
          if (file.trim() !== "") {
            formattedStatus += `  ${file}\n`;
          }
        });
      }

      console.log("格式化後的 Git 狀態：", formattedStatus);

      // 更新 UI
      webviewView.webview.postMessage({
        command: "updateStatus",
        data: formattedStatus,
      });

      // 獲取 staged 文件列表並更新 UI（僅 Java 檔案）
      await this.refreshStagedFiles(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "Git 操作失敗");
    }
  }

  // 刷新 stage 區域的文件，只顯示 Java 檔案
  private async refreshStagedFiles(webviewView: vscode.WebviewView) {
    try {
      // 獲取所有已暫存的 Java 檔案
      const { stdout } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: workspaceFolder }
      );

      console.log("已暫存的 Java 檔案：", stdout);

      webviewView.webview.postMessage({
        command: "sendData",
        data: stdout,
      });
    } catch (error) {
      throw error;
    }
  }

  // 初始化 stage 區
  private async handleInitStage(webviewView: vscode.WebviewView) {
    try {
      await this.refreshStagedFiles(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "初始化 stage 區失敗");
    }
  }

  // 將檔案加入 stage 區
  private async handleAddStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    try {
      // 確認是 Java 檔案才加入
      if (!filePath.endsWith(".java")) {
        vscode.window.showInformationMessage(
          `只能加入 Java 檔案到 stage 區：${filePath}`
        );
        return;
      }

      console.log(`執行 git add "${filePath}"`);
      await execPromise(`git add "${filePath}"`, { cwd: workspaceFolder });

      // 刷新 stage 區域
      await this.refreshStagedFiles(webviewView);

      // 重新獲取 Git 狀態
      await this.handleGetGitStatus(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "執行 git add 錯誤");
    }
  }

  // 將檔案從 stage 區移除
  private async handleRemoveFromStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    try {
      // 確認是 Java 檔案才處理
      if (!filePath.endsWith(".java")) {
        return;
      }

      await execPromise(`git restore --staged -- "${filePath}"`, {
        cwd: workspaceFolder,
      });

      console.log("從 stage 區移除:", filePath);

      // 刷新 stage 區域
      await this.refreshStagedFiles(webviewView);

      // 重新獲取 Git 狀態
      await this.handleGetGitStatus(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "從 stage 區移除檔案失敗");
    }
  }

  // 顯示檔案差異
  private async handleShowDiff(filePath: string) {
    try {
      // 確認是 Java 檔案才顯示差異
      if (!filePath.endsWith(".java")) {
        vscode.window.showInformationMessage(
          `只能顯示 Java 檔案的差異：${filePath}`
        );
        return;
      }

      // 獲取檔案的完整路徑
      const fullPath = path.join(workspaceFolder, filePath);

      // 開啟檔案
      const document = await vscode.workspace.openTextDocument(fullPath);
      await vscode.window.showTextDocument(document);

      // 執行 Git 差異命令
      await vscode.commands.executeCommand(
        "git.openChange",
        vscode.Uri.file(fullPath)
      );
    } catch (error) {
      vscode.window.showErrorMessage(
        `無法顯示檔案差異: ${getErrorMessage(error)}`
      );
    }
  }

  // 生成 commit，只考慮 Java 檔案
  private async handleGenerateCommit(webviewView: vscode.WebviewView) {
    try {
      webviewView.webview.postMessage({
        command: "updateCommit",
        data: "正在生成 Java 檔案的 Commit Message...",
      });

      // 獲取 staged 的 diff 資訊，只針對 Java 檔案
      const { stdout: stagedFiles } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        {
          cwd: workspaceFolder,
        }
      );

      // 檢查是否有 Java 檔案
      const javaFiles = stagedFiles
        .split("\n")
        .filter((file) => file.trim() !== "" && file.endsWith(".java"));

      // 如果沒有 Java 檔案被 stage
      if (javaFiles.length === 0) {
        webviewView.webview.postMessage({
          command: "updateCommit",
          data: "沒有 Java 檔案被加入到 stage 區，無法生成 Commit Message。",
        });
        return;
      }

      // 只獲取 Java 檔案的 diff
      const { stdout: diffInfo } = await execPromise(
        `git diff --cached -- "*.java"`,
        {
          cwd: workspaceFolder,
        }
      );

      // 保存 diff 資訊到暫存
      this._cachedDiffInfo = diffInfo;

      // 直接向後端請求生成 Commit Message
      const commitMessage = await this.getCommitMessage(diffInfo);

      // 更新 UI
      webviewView.webview.postMessage({
        command: "updateCommit",
        data: commitMessage,
      });
    } catch (error) {
      this.handleError(error, webviewView, "生成 commit 失敗");
    }
  }

  // 從後端獲取 Commit Message
  private async getCommitMessage(diffInfo: string): Promise<string> {
    if (!diffInfo || diffInfo.trim() === "") {
      return "無法生成 Commit Message：沒有 Java 檔案變更";
    }

    try {
      const response = await fetch(`${API_BASE_URL}/getCommitMessage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          diffInfo: diffInfo,
        }),
      });

      if (response.ok) {
        const commitMessage = await response.text();
        console.log("成功獲取 Commit Message");
        return commitMessage;
      } else {
        console.error(
          `獲取 Commit Message 請求失敗: ${response.status} ${response.statusText}`
        );
        return "獲取 Commit Message 失敗，請檢查後端服務是否正常運行";
      }
    } catch (error) {
      console.error("連接後端服務失敗:", error);
      return "連接後端服務失敗: " + getErrorMessage(error);
    }
  }

  // 統一錯誤處理
  private handleError(
    error: unknown,
    webviewView: vscode.WebviewView | null,
    prefix: string
  ) {
    const errorMessage = getErrorMessage(error);

    console.error(`${prefix}:`, error);
    vscode.window.showErrorMessage(`${prefix}: ${errorMessage}`);

    // 如果提供了 webview，更新 UI 顯示錯誤
    if (webviewView) {
      webviewView.webview.postMessage({
        command: "updateStatus",
        data: `Error: ${errorMessage}`,
      });
    }
  }
}

// 獲取錯誤訊息
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  } else if (typeof error === "string") {
    return error;
  } else if (error && typeof error === "object" && "toString" in error) {
    return error.toString();
  }
  return "未知錯誤";
}

// Extension 當被停用時
export function deactivate() {}
