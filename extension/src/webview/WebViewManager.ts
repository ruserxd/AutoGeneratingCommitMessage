import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { AssetLoader } from "../utils/AssetLoader";

export class WebViewManager {
  private assetLoader: AssetLoader;

  constructor(private readonly context: vscode.ExtensionContext) {
    this.assetLoader = new AssetLoader(context.extensionPath);
  }

  public async loadWebviewContent(
    webviewView: vscode.WebviewView
  ): Promise<string> {
    // 檢查必要檔案
    const htmlPath = path.join(this.context.extensionPath, "out", "index.html");
    const assetsPath = path.join(this.context.extensionPath, "out", "assets");

    if (!fs.existsSync(htmlPath)) {
      throw new Error(`HTML 檔案不存在: ${htmlPath}`);
    }

    if (!fs.existsSync(assetsPath)) {
      throw new Error(`Assets 目錄不存在: ${assetsPath}`);
    }

    // 讀取 HTML
    let html = fs.readFileSync(htmlPath, "utf8");

    // 載入並注入資源
    const assets = this.assetLoader.loadAssets();
    const { linkTags, scriptTags } = this.assetLoader.generateAssetTags(
      assets,
      webviewView.webview
    );

    // 注入資源到 HTML
    html = this.injectAssetsToHtml(html, linkTags, scriptTags, webviewView);

    return html;
  }

  private injectAssetsToHtml(
    html: string,
    linkTags: string,
    scriptTags: string,
    webviewView: vscode.WebviewView
  ): string {
    // CSP 設定
    const csp = `
      <meta http-equiv="Content-Security-Policy" content="
        default-src 'none';
        style-src ${webviewView.webview.cspSource} 'unsafe-inline';
        script-src ${webviewView.webview.cspSource} 'unsafe-eval';
        img-src ${webviewView.webview.cspSource} data: https:;
        font-src ${webviewView.webview.cspSource};
        connect-src ${webviewView.webview.cspSource} http://localhost:8080 http://localhost:8000;
      ">
    `;

    // 注入 CSP
    if (html.includes("<head>")) {
      html = html.replace("<head>", `<head>${csp}`);
    } else {
      html = `<head>${csp}</head>${html}`;
    }

    // 注入 CSS
    if (linkTags && html.includes("</head>")) {
      html = html.replace("</head>", `${linkTags}\n</head>`);
    }

    // 注入 JS
    if (scriptTags && html.includes("</body>")) {
      html = html.replace("</body>", `${scriptTags}\n</body>`);
    }

    return html;
  }

  public getErrorPageHtml(): string {
    try {
      const errorPagePath = path.join(
        this.context.extensionPath,
        "src",
        "errorPage.html"
      );
      return fs.readFileSync(errorPagePath, "utf8");
    } catch (error) {
      return `
        <!DOCTYPE html>
        <html>
          <head><title>Error</title></head>
          <body style="background:#1e1e1e;color:#cccccc;font-family:sans-serif;padding:20px;">
            <h2 style="color:#f44747;">❌ 載入失敗</h2>
            <p>請重新建置應用：<code>npm run build:all</code></p>
          </body>
        </html>
      `;
    }
  }
}
