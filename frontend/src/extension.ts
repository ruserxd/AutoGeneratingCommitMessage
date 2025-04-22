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
  }

  // 獲取當前 java 專案的資訊
  private async getJavaFiles() {
    try {
      let fileList = await vscode.workspace.findFiles("*{.java}");
      return fileList;
    } catch (error) {
      return error;
    }
  }
}

// Extension 當被停用時
export function deactivate() {}
