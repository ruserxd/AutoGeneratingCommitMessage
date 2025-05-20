import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import axios from "axios";
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
  console.log("路徑:", context.extensionPath);
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
    console.log("Updated workspace folder to:", workspaceFolder);
  }
}

// Extension 當被停用時
export function deactivate() {}

// WebView 視圖提供者類
class CodeManagerViewProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;
  private _cachedDiffInfo: string = ""; // 暫存最近一次的 diff 資訊

  constructor(private readonly context: vscode.ExtensionContext) {}

  // 首次打開 activity bar
  public async resolveWebviewView(webviewView: vscode.WebviewView) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.file(path.join(this.context.extensionPath)),
        // vscode.Uri.file(path.join(this.context.extensionPath, 'out')),
        // vscode.Uri.file(path.join(this.context.extensionPath, 'out', 'assets'))
      ],
    };

    // 讀取 index.html
    const htmlPath = vscode.Uri.joinPath(
      this.context.extensionUri,
      "out",
      "index.html"
    );
    let html = fs.readFileSync(htmlPath.fsPath, "utf8");

    // 動態產生 <link> 和 <script> 標籤
    const assetsPath = path.join(this.context.extensionPath, "out", "assets");
    const assetFiles = fs.existsSync(assetsPath)
      ? fs.readdirSync(assetsPath)
      : [];

    // 產生 CSS <link>
    const linkTags = assetFiles
      .filter((file) => file.endsWith(".css"))
      .map((file) => {
        const diskUri = vscode.Uri.file(path.join(assetsPath, file));
        const webviewUri = webviewView.webview.asWebviewUri(diskUri);
        console.log("CSS file:", file);
        console.log("Disk URI for CSS:", diskUri.fsPath);
        console.log("Webview URI for CSS:", webviewUri.toString());
        return `<link rel="stylesheet" href="${webviewUri}">`;
      })
      .join("\n");

    const scriptTags = assetFiles
      .filter((file) => file.endsWith(".js"))
      .map((file) => {
        const diskUri = vscode.Uri.file(path.join(assetsPath, file));
        const webviewUri = webviewView.webview.asWebviewUri(diskUri);
        console.log("JS file:", file);
        console.log("Disk URI for JS:", diskUri.fsPath);
        console.log("Webview URI for JS:", webviewUri.toString());
        return `<script type="module" src="${webviewUri}"></script>`;
      })
      .join("\n");

    const imageTags = assetFiles
      .filter((file) => file.endsWith(".svg"))
      .map((file) => {
        const diskUri = vscode.Uri.file(path.join(assetsPath, file));
        const webviewUri = webviewView.webview.asWebviewUri(diskUri);
        console.log("Image file:", file);
        console.log("Disk URI for Image:", diskUri.fsPath);
        console.log("Webview URI for Image:", webviewUri.toString());
        return `<script>window.REACT_LOGO = "${webviewUri}";</script>`;
      })
      .join("\n");

    // 注入到 HTML 中
    html = html.replace(
      "</head>",
      `
      ${linkTags}
      </head>`
    );
    html = html.replace(
      "</body>",
      `${scriptTags}
</body>`
    );
    //<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' vscode-webview-resource:; style-src 'self' vscode-webview-resource:; img-src 'self' vscode-webview-resource: data:;">
    // 設定 HTML
    webviewView.webview.html = html;

    // 更新工作區路徑
    updateWorkspaceFolder();

    // 設置消息處理程序
    this.setupMessageListener(webviewView);
  }

  // 設置監聽器
  private setupMessageListener(webviewView: vscode.WebviewView) {
    webviewView.webview.onDidReceiveMessage(async (message) => {
      switch (message.command) {
        case "getGitStatus":
          await this.handleGetGitStatus(webviewView);
          break;
        case "initStage":
          await this.handleInitStage(webviewView);
          break;
        case "addStage":
          await this.handleAddStage(message.file, webviewView);
          break;
        case "remove":
          await this.handleRemoveFromStage(message.file, webviewView);
          break;
        case "generateCommit":
          await this.handleGenerateCommit(webviewView);
          break;
        case "showDiff":
          await this.handleShowDiff(message.file);
          break;
        case "getGreet":
          await this.handleGetGreetCommand(webviewView);
          break;
      }
    });
  }
  // 處理獲取 Git 狀態（僅限 Java 檔案）
  private async handleGetGitStatus(webviewView: vscode.WebviewView) {
    console.log("handleGetGitStatus called");
    console.log("Current workspace folder:", workspaceFolder);
    webviewView.webview.postMessage({
      command: "updateStatus",
      data: "正在獲取 Java 檔案的 Git 狀態資訊...",
    });

    try {
      const { stdout: unstagedFiles } = await execPromise(
        `git ls-files --modified --others --exclude-standard -- "*.java"`,
        { cwd: workspaceFolder }
      );
      console.log("Unstaged files result:", unstagedFiles);
      let formattedStatus = unstagedFiles.trim()
        ? "未加入 Stage 的 Java 檔案：\n" +
          unstagedFiles
            .split("\n")
            .filter((file) => file.trim())
            .map((file) => `  ${file}`)
            .join("\n")
        : "沒有未加入 Stage 的 Java 檔案";
      console.log("Formatted status:", formattedStatus);
      webviewView.webview.postMessage({
        command: "updateStatus",
        data: formattedStatus,
      });

      await this.refreshStagedFiles(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "Git 操作失敗");
    }
  }

  // 刷新 Stage 區域（僅限 Java 檔案）
  private async refreshStagedFiles(webviewView: vscode.WebviewView) {
    console.log("refreshStagedFiles called");
    try {
      const { stdout } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: workspaceFolder }
      );

      console.log("Staged files result:", stdout);

      webviewView.webview.postMessage({
        command: "sendData",
        data: stdout,
      });
    } catch (error) {
      this.handleError(error, webviewView, "刷新 Stage 區域失敗");
    }
  }

  // 初始化 Stage 區
  private async handleInitStage(webviewView: vscode.WebviewView) {
    await this.refreshStagedFiles(webviewView);
  }

  // 將檔案加入 Stage 區
  private async handleAddStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    if (!filePath.endsWith(".java")) {
      vscode.window.showInformationMessage(`只能加入 Java 檔案：${filePath}`);
      return;
    }

    try {
      await execPromise(`git add "${filePath}"`, { cwd: workspaceFolder });
      await this.refreshStagedFiles(webviewView);
      await this.handleGetGitStatus(webviewView);
    } catch (error) {
      this.handleError(error, webviewView, "執行 git add 錯誤");
    }
  }

  // 從 Stage 區移除檔案
  private async handleRemoveFromStage(
    filePath: string,
    webviewView: vscode.WebviewView
  ) {
    if (!filePath.endsWith(".java")) return;

    try {
      console.log(`Attempting to unstage file: "${filePath}"`);

      // 確保文件路徑格式正確，避免引號問題
      const sanitizedPath = filePath.replace(/"/g, '\\"');

      // 使用更可靠的命令格式
      const result = await execPromise(`git reset HEAD -- "${sanitizedPath}"`, {
        cwd: workspaceFolder,
      });

      console.log("Git unstage result:", result);

      // 刷新狀態
      await this.refreshStagedFiles(webviewView);
      await this.handleGetGitStatus(webviewView);
    } catch (error) {
      console.error("Git unstage error:", error);
      this.handleError(error, webviewView, "從 Stage 區移除檔案失敗");
    }
  }

  // 顯示檔案差異
  private async handleShowDiff(filePath: string) {
    if (!filePath.endsWith(".java")) {
      vscode.window.showInformationMessage(
        `只能顯示 Java 檔案的差異：${filePath}`
      );
      return;
    }

    try {
      const fullPath = path.join(workspaceFolder, filePath);
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

  private async handleGetGreetCommand(webviewView: vscode.WebviewView) {
    try {
      const response = await axios.get("http://localhost:8000/api/greet");
      webviewView.webview.postMessage({
        command: "greetResult",
        message: response.data,
      });
    } catch (error) {
      console.error("Failed to fetch greeting:", error);
      webviewView.webview.postMessage({
        command: "greetResult",
        error: `Failed to fetch greeting: ${(error as any).message}`,
      });
    }
  }

  // 生成 Commit Message
  private async handleGenerateCommit(webviewView: vscode.WebviewView) {
    webviewView.webview.postMessage({
      command: "updateCommit",
      data: "正在生成 Java 檔案的 Commit Message...",
    });

    try {
      const { stdout: stagedFiles } = await execPromise(
        `git diff --cached --name-only -- "*.java"`,
        { cwd: workspaceFolder }
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
        {
          cwd: workspaceFolder,
        }
      );
      this._cachedDiffInfo = diffInfo;

      const commitMessage = await this.getCommitMessage(diffInfo);
      webviewView.webview.postMessage({
        command: "updateCommit",
        data: commitMessage,
      });
    } catch (error) {
      this.handleError(error, webviewView, "生成 Commit Message 失敗");
    }
  }

  // 從後端獲取 Commit Message
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

  // 統一錯誤處理
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
// 獲取錯誤訊息
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === "string") return error;
  if (error && typeof error === "object" && "toString" in error)
    return error.toString();
  return "未知錯誤";
}
