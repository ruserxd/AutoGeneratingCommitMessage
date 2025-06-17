import * as vscode from "vscode";
import { WebViewManager } from "../webview/WebViewManager";
import { MessageHandler } from "../handlers/MessageHandler";

export class CodeManagerViewProvider implements vscode.WebviewViewProvider {
  private _view?: vscode.WebviewView;
  private webviewManager: WebViewManager;
  private messageHandler: MessageHandler;

  constructor(private readonly context: vscode.ExtensionContext) {
    this.webviewManager = new WebViewManager(context);
    this.messageHandler = new MessageHandler();
  }

  public async resolveWebviewView(webviewView: vscode.WebviewView) {
    this._view = webviewView;

    // 設定 webview 選項
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.file(this.context.extensionPath)],
    };

    try {
      // 載入 webview 內容
      const html = await this.webviewManager.loadWebviewContent(webviewView);
      webviewView.webview.html = html;

      // 設置訊息監聽器
      this.setupMessageListener(webviewView);
    } catch (error) {
      console.error("載入 webview 失敗:", error);
      webviewView.webview.html = this.webviewManager.getErrorPageHtml();
    }
  }

  private setupMessageListener(webviewView: vscode.WebviewView) {
    webviewView.webview.onDidReceiveMessage(async (message) => {
      await this.messageHandler.handleMessage(message, webviewView);
    });
  }
}
