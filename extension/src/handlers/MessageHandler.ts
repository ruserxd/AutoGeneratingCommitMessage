import * as vscode from "vscode";
import { GitOperations } from "../services/GitOperations";
import { ApiService } from "../services/ApiService";
import { getErrorMessage } from "../utils/ErrorHandler";

// 定義 WebView 訊息介面
interface WebviewMessage {
  command: string;
  file?: string;
  [key: string]: any;
}

// 定義有效的命令類型
type ValidCommand =
  | "getGitStatus"
  | "initStage"
  | "addStage"
  | "remove"
  | "generateCommit"
  | "showDiff"
  | "generateSummary"
  | "methodDiffHistory";

export class MessageHandler {
  private gitOps: GitOperations;
  private apiService: ApiService;
  private validCommands: Set<ValidCommand>;

  constructor() {
    this.gitOps = new GitOperations();
    this.apiService = new ApiService();
    this.validCommands = new Set([
      "getGitStatus",
      "initStage",
      "addStage",
      "remove",
      "generateCommit",
      "showDiff",
      "generateSummary",
      "methodDiffHistory",
    ]);
  }

  public async handleMessage(
    message: WebviewMessage,
    webviewView: vscode.WebviewView
  ): Promise<void> {
    // 驗證訊息格式
    if (!message || typeof message.command !== "string") {
      this.sendErrorMessage(webviewView, "無效的訊息格式");
      return;
    }

    // 驗證命令是否有效
    if (!this.isValidCommand(message.command)) {
      console.warn(`Unknown command: ${message.command}`);
      this.sendErrorMessage(webviewView, `未知的命令: ${message.command}`);
      return;
    }

    try {
      await this.executeCommand(message, webviewView);
    } catch (error) {
      const errorMessage = getErrorMessage(error);
      console.error(`Error handling command ${message.command}:`, error);
      this.sendErrorMessage(
        webviewView,
        `處理命令 ${message.command} 時發生錯誤: ${errorMessage}`
      );
    }
  }

  private async executeCommand(
    message: WebviewMessage,
    webviewView: vscode.WebviewView
  ): Promise<void> {
    switch (message.command as ValidCommand) {
      case "getGitStatus":
        await this.gitOps.handleGetGitStatus(webviewView);
        break;

      case "initStage":
        await this.gitOps.handleInitStage(webviewView);
        break;

      case "addStage":
        if (!message.file) {
          throw new Error("addStage 命令需要 file 參數");
        }
        await this.gitOps.handleAddStage(message.file, webviewView);
        break;

      case "remove":
        if (!message.file) {
          throw new Error("remove 命令需要 file 參數");
        }
        await this.gitOps.handleRemoveFromStage(message.file, webviewView);
        break;

      case "generateCommit":
        await this.apiService.handleGenerateCommit(
          webviewView,
          message.modelName
        );
        break;

      case "showDiff":
        if (!message.file) {
          throw new Error("showDiff 命令需要 file 參數");
        }
        await this.gitOps.handleShowDiff(message.file);
        break;

      case "generateSummary":
        await this.apiService.handleGenerateSummary(webviewView);
        break;

      case "methodDiffHistory":
        await this.apiService.handleMethodDiffHistory(webviewView);
        break;
      default:
        throw new Error(`未實作的命令: ${message.command}`);
    }
  }

  private isValidCommand(command: string): command is ValidCommand {
    return this.validCommands.has(command as ValidCommand);
  }

  private sendErrorMessage(
    webviewView: vscode.WebviewView,
    errorMessage: string
  ): void {
    webviewView.webview.postMessage({
      command: "error",
      message: errorMessage,
      timestamp: new Date().toISOString(),
    });
  }

  // 獲取支援的命令列表
  public getSupportedCommands(): ValidCommand[] {
    return Array.from(this.validCommands);
  }

  // 檢查命令是否需要檔案參數
  public commandRequiresFile(command: ValidCommand): boolean {
    return ["addStage", "remove", "showDiff"].includes(command);
  }
}
