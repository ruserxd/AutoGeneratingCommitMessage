import * as vscode from "vscode";

export class WorkspaceManager {
  private static _workspaceFolder: string = "";

  public static get workspaceFolder(): string {
    return this._workspaceFolder;
  }

  public static initialize() {
    this.updateWorkspaceFolder();
  }

  public static updateWorkspaceFolder() {
    if (
      vscode.workspace.workspaceFolders &&
      vscode.workspace.workspaceFolders.length > 0
    ) {
      this._workspaceFolder = vscode.workspace.workspaceFolders[0].uri.fsPath;
      console.log("Updated workspace folder to:", this._workspaceFolder);
    }
  }
}
