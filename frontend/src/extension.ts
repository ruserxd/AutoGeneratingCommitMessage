// @ts-ignore
const cp = require("child_process");
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
//工作區路徑
let workspaceFolder = "";
if (
  vscode.workspace.workspaceFolders &&
  vscode.workspace.workspaceFolders.length > 0
) {
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
    if (
      vscode.workspace.workspaceFolders &&
      vscode.workspace.workspaceFolders.length > 0
    ) {
      workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    // 獲取 Java 文件列表
    const javaFiles = await this.getJavaFiles();
    console.log("發現的 Java 文件:", javaFiles);
    // 輸出 cd 至哪個區塊
    console.log("cd 至" + `${workspaceFolder}`);

    // 獲取修改檔的路徑，並執行 git diff
    webviewView.webview.onDidReceiveMessage((message) => {
      // 獲取當前 Java 專案的資訊，並生成文字檔
      if (message.command === "showDiff") {
        const filePath = message.file;

        const path = vscode.window.createOutputChannel("FilePath");
        path.appendLine(filePath);
        path.show();

        cp.exec(`cd "${workspaceFolder}"`);

        // 執行git diff
        cp.exec(`git diff -- "${filePath}"`, { cwd: workspaceFolder }, (err: Error | null, stdout: string, stderr: string) => {
          if (err) {
            vscode.window.showErrorMessage(`執行 git diff 錯誤: ${stderr}`);
            return;
          }
      
          if (stdout.trim()) {
            // 有未 stage 的差異，直接顯示
            vscode.workspace
              .openTextDocument({ content: stdout, language: "diff" })
              .then((doc) => {
                vscode.window.showTextDocument(doc, { preview: false });
              });
          } else {
            // 沒有未 stage 的差異，再去抓 staged 的差異
            cp.exec(`git diff --staged -- "${filePath}"`, { cwd: workspaceFolder }, (cachedErr: Error | null, cachedStdout: string, cachedStderr: string) => {
              if (cachedErr) {
                vscode.window.showErrorMessage(`執行 git diff --cached 錯誤: ${cachedStderr}`);
                return;
              }
      
              vscode.workspace
                .openTextDocument({ content: cachedStdout || "無變更內容。", language: "diff" })
                .then((doc) => {
                  vscode.window.showTextDocument(doc, { preview: false });
                });
            });
          }
        });
      }

      //初始化stage
      if (message.command === 'initStage') {
        // 當 webview 向插件要資料，插件這裡就回傳資料
        cp.exec(`git diff --cached --name-only`, { cwd: workspaceFolder }, (cachedErr: Error | null, cachedStdout: string, cachedStderr: string) => {
          if (cachedErr) {
            vscode.window.showErrorMessage(`執行 git diff --cached --name-only 錯誤: ${cachedStderr}`);
            return;
          }
          webviewView.webview.postMessage({ 
            command: 'sendData', 
            data: cachedStdout 
          });
  
        });
        
      }

      
      // 將檔案加入 stage 區
      if(message.command === "addStage") {
        const filePath = message.file;
        cp.exec(
          `git add "${filePath}"`,
          { cwd: workspaceFolder },
          (err: any, stdout: string, stderr: string) => {
            if (err) {
              vscode.window.showErrorMessage(`執行 git add 錯誤: ${stderr}`);
              return;
            }
          }
        );
      }

      // 將檔案從 stage 區移除
      if(message.command === "remove") {
        const filePath = message.file;
        cp.exec(
          `git restore --staged -- "${filePath}"`,
          { cwd: workspaceFolder },
          (err: any, stdout: string, stderr: string) => {
            if (err) {
              vscode.window.showErrorMessage(`執行 git add 錯誤: ${stderr}`);
              return;
            }
          }
        );

        console.log("remove", filePath);
      }

      //將生成commit的請求傳送給後端，並將當前git diff 的結果傳送給後端
      if(message.command === "generateCommit") {
        cp.exec(
          `git diff --staged`,
          { cwd: workspaceFolder },
          (err: any, stdout: string, stderr: string) => {
            if (err) {
              vscode.window.showErrorMessage(`執行 git diff 錯誤: ${stderr}`);
              return;
            }
            (async () => {
              await fetch("http://localhost:8080/getAllDiff", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  workspace: workspaceFolder,
                  diffInfo: stdout 
                }),
              });
            })();
          }
        );
      }
    });
  }

  // 獲取當前 java 專案的資訊
  private async getJavaFiles() {
    try {
      let fileList = await vscode.workspace.findFiles("**/*.java}");

      if (workspaceFolder) {
        cp.exec(
          `git status `,
          { cwd: workspaceFolder },
          (err: any, stdout: string, stderr: string) => {
            if (err) {
              vscode.window.showErrorMessage(`執行 git status 錯誤: ${stderr}`);
              return;
            }
            console.log(`Git Status 結果：\n${stdout}`);

            (async () => {
              await fetch("http://localhost:8080/getList", {
                method: "POST",
                headers: {
                  "Content-Type": "application/json",
                },
                body: JSON.stringify({
                  workspace: workspaceFolder,
                  gitStatus: stdout  
                }),
              });
            })();
          }
        );
      }

      return fileList;
    } catch (error) {
      return error;
    }
  }

  // TODO: Git API Extension
  private getGitStagedChange() {
    const gitAPI = vscode.extensions.getExtension("vscode.git")?.activate();
  }
}

// Extension 當被停用時
export function deactivate() {}
