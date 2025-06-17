import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";

export interface AssetFiles {
  cssFiles: string[];
  jsFiles: string[];
  allFiles: string[];
}

export class AssetLoader {
  constructor(private readonly extensionPath: string) {}

  public loadAssets(): AssetFiles {
    const assetsPath = path.join(this.extensionPath, "out", "assets");

    if (!fs.existsSync(assetsPath)) {
      return { cssFiles: [], jsFiles: [], allFiles: [] };
    }

    const allFiles = fs.readdirSync(assetsPath);

    // 優先尋找 webview- 開頭的檔案
    let cssFiles = allFiles.filter(
      (file) => file.startsWith("webview-") && file.endsWith(".css")
    );

    let jsFiles = allFiles.filter(
      (file) => file.startsWith("webview-") && file.endsWith(".js")
    );

    // 如果沒有找到，改找其他 CSS/JS 檔案
    if (cssFiles.length === 0) {
      cssFiles = allFiles.filter((file) => file.endsWith(".css"));
    }

    if (jsFiles.length === 0) {
      jsFiles = allFiles.filter((file) => file.endsWith(".js"));
    }

    console.log("載入的資源:", { cssFiles, jsFiles });

    return { cssFiles, jsFiles, allFiles };
  }

  public generateAssetTags(
    assets: AssetFiles,
    webview: vscode.Webview
  ): { linkTags: string; scriptTags: string } {
    const assetsPath = path.join(this.extensionPath, "out", "assets");

    const linkTags = assets.cssFiles
      .map((file) => {
        const webviewUri = webview.asWebviewUri(
          vscode.Uri.file(path.join(assetsPath, file))
        );
        console.log(`載入 CSS: ${file} -> ${webviewUri}`);
        return `<link rel="stylesheet" href="${webviewUri}">`;
      })
      .join("\n");

    const scriptTags = assets.jsFiles
      .map((file) => {
        const webviewUri = webview.asWebviewUri(
          vscode.Uri.file(path.join(assetsPath, file))
        );
        console.log(`載入 JS: ${file} -> ${webviewUri}`);
        return `<script type="module" src="${webviewUri}"></script>`;
      })
      .join("\n");

    return { linkTags, scriptTags };
  }
}
