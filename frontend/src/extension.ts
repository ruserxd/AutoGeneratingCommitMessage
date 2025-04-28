import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";


// Extension 當被啟用時
export function activate(context: vscode.ExtensionContext) {
  // 定義獲取 webview 的 HTML 內容
  function loadWebView(webviewPath: string): string {
    const readPath = path.join(context.extensionPath, webviewPath);
    return fs.readFileSync(readPath, { encoding: "utf-8" });
  }

  // 註冊 Webview 視圖提供者
  const provider = new CodeManagerViewProvider(context, loadWebView);

  // 註冊 WebView 視圖提供者
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codeManagerView", provider)
  );
}

let workspaceFolder = "";
if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
    workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
}

// WebView 視圖提供者類
class CodeManagerViewProvider implements vscode.WebviewViewProvider {
  private _context: vscode.ExtensionContext;
  private _loadWebView: (webviewPath: string) => string;

  constructor(
    context: vscode.ExtensionContext,
    loadWebView: (webviewPath: string) => string
  ) {
    this._context = context;
    this._loadWebView = loadWebView;
  }

  // 首次打開 activity bar
  async resolveWebviewView(webviewView: vscode.WebviewView) {
    // 啟用 WebView 腳本
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(this._context.extensionPath)],
    };

    // 設置 WebView 的 HTML 內容
    webviewView.webview.html = this._loadWebView("src/main/webview.html");


    // 獲取 Java 文件列表
    const javaFiles = await this.getJavaFiles();
    console.log("發現的 Java 文件:", javaFiles);

    // @ts-ignore
    const cp = require('child_process');

    //獲取修改檔的路徑，並執行git diff
    webviewView.webview.onDidReceiveMessage((message) => {
      if (message.command === 'showDiff') {
        const filePath = message.file;

        const path = vscode.window.createOutputChannel('FilePath');
        path.appendLine(filePath);
        path.show();



        cp.exec(`cd "${workspaceFolder}"`);

        //執行git diff
        cp.exec(`git diff -- "${filePath}"`, { cwd: workspaceFolder }, (err: any, stdout: string, stderr: string) => {
          if (err) {
            vscode.window.showErrorMessage(`執行 git diff 錯誤: ${stderr}`);
            return;
          }

          //將diff info以文字檔開啟
          vscode.workspace.openTextDocument({
            content: stdout || '無變更內容。',
            language: 'diff',
          }).then(doc => {
            vscode.window.showTextDocument(doc, { preview: false });
          });
        });
      }
    });
  }

  // 獲取當前 java 專案的資訊
  private async getJavaFiles() {
    try {
      let fileList = await vscode.workspace.findFiles("**/*.java}");
      const pathList = fileList.map(uri => uri.fsPath);

      // 將工作區路徑回傳給後端
      await fetch("http://localhost:8080/getlist", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ workspace: workspaceFolder })
      });
      return fileList;
    } catch (error) {
      return error;
    }
  }
}

// Extension 當被停用時
export function deactivate() {}


