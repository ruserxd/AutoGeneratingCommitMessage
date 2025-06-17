import * as vscode from "vscode";
import { CodeManagerViewProvider } from "./providers/CodeManagerViewProvider";
import { WorkspaceManager } from "./utils/WorkspaceManager";

// Extension 當被啟用時
export function activate(context: vscode.ExtensionContext) {
  console.log("Extension 啟動，路徑:", context.extensionPath);

  // 初始化工作區管理器
  WorkspaceManager.initialize();

  // 註冊 WebView 提供者
  const provider = new CodeManagerViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("codeManagerView", provider)
  );

  // 監聽工作區變化
  context.subscriptions.push(
    vscode.workspace.onDidChangeWorkspaceFolders(() => {
      WorkspaceManager.updateWorkspaceFolder();
    })
  );
}

// Extension 當被停用時
export function deactivate() {
  console.log("Extension 停用");
}
