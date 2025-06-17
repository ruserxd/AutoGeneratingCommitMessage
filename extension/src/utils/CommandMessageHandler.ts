import * as vscode from "vscode";
import { GitOperations } from "../services/GitOperations";
import { ApiService } from "../services/ApiService";

export class CommandMessageHandler {
  private gitOps: GitOperations;
  private apiService: ApiService;

  constructor() {
    this.gitOps = new GitOperations();
    this.apiService = new ApiService();
  }

  public async handleMessage(message: any, webviewView: vscode.WebviewView) {
    try {
      switch (message.command) {
        case "getGitStatus":
          await this.gitOps.handleGetGitStatus(webviewView);
          break;
        case "initStage":
          await this.gitOps.handleInitStage(webviewView);
          break;
        case "addStage":
          await this.gitOps.handleAddStage(message.file, webviewView);
          break;
        case "remove":
          await this.gitOps.handleRemoveFromStage(message.file, webviewView);
          break;
        case "generateCommit":
          await this.apiService.handleGenerateCommit(webviewView);
          break;
        case "generateWhy":
          await this.apiService.handleGenerateWhy(webviewView);
          break;
        case "showDiff":
          await this.gitOps.handleShowDiff(message.file);
          break;
        case "getGreet":
          await this.apiService.handleGetGreetCommand(webviewView);
          break;
        default:
          console.warn(`Unknown command: ${message.command}`);
      }
    } catch (error) {
      console.error(`Error handling command ${message.command}:`, error);
    }
  }
}
