/* global acquireVsCodeApi */
import { useEffect, useMemo, useState } from "react";

export const useVSCodeApi = () => {
  const [greeting, setGreeting] = useState("");
  const [gitStatus, setGitStatus] = useState("未獲取 Git 狀態");
  const [stagedFiles, setStagedFiles] = useState([]);
  const [unstagedFiles, setUnstagedFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [commitMessage, setCommitMessage] = useState("");
  const [whyReason, setWhyReason] = useState("尚未分析");
  const [changesSummary, setChangesSummary] = useState("尚未分析");

  const vscode = useMemo(() => {
    if (typeof acquireVsCodeApi !== "undefined") {
      return acquireVsCodeApi();
    }
    return null;
  }, []);

  useEffect(() => {
    const messageHandler = (event) => {
      const message = event.data;
      console.log("收到訊息:", message);

      switch (message.command) {
        case "greetResult":
          if (message.error) {
            setGreeting(`錯誤: ${message.error}`);
          } else {
            setGreeting(message.message);
          }
          break;
        case "updateStatus":
          setGitStatus(message.data);
          if (message.data.includes("未加入 Stage 的 Java 檔案")) {
            const lines = message.data.split("\n");
            lines.shift();
            setUnstagedFiles(lines.map((line) => line.trim()).filter(Boolean));
          } else {
            setUnstagedFiles([]);
          }
          setLoading(false);
          break;
        case "sendData":
          try {
            let files = [];

            if (message.data) {
              if (typeof message.data === "string") {
                if (message.data.includes("\n")) {
                  files = message.data
                    .split("\n")
                    .map((line) => line.trim())
                    .filter(Boolean);
                } else {
                  // 空格分隔的格式
                  files = message.data
                    .split(/\s+/)
                    .filter((file) => file.trim());
                }
              } else if (Array.isArray(message.data)) {
                files = message.data.filter(Boolean);
              }
            }

            setStagedFiles(files);
            console.log("設置已暫存文件:", files);
          } catch (error) {
            console.error("處理 sendData 時發生錯誤:", error);
            setStagedFiles([]);
          }
          setLoading(false);
          break;
        case "updateCommit":
          setCommitMessage(message.data);
          setLoading(false);
          break;
        case "updateWhy":
          setWhyReason(message.data);
          setLoading(false);
          break;
        case "updateSummary":
          setChangesSummary(message.data);
          setLoading(false);
          break;
      }
    };

    window.addEventListener("message", messageHandler);
    initializeGitStatus();

    return () => {
      window.removeEventListener("message", messageHandler);
    };
  }, []);

  const initializeGitStatus = () => {
    setLoading(true);
    vscode && vscode.postMessage({ command: "initStage" });
    vscode && vscode.postMessage({ command: "getGitStatus" });
  };

  const fetchGreeting = () => {
    setGreeting("獲取中...");
    vscode && vscode.postMessage({ command: "getGreet" });
  };

  const fetchGitStatus = () => {
    setLoading(true);
    setGitStatus("獲取 Git 狀態中...");
    vscode && vscode.postMessage({ command: "getGitStatus" });
  };

  const addToStage = (file) => {
    return new Promise((resolve, reject) => {
      setLoading(true);

      const messageHandler = (event) => {
        const message = event.data;
        if (message.command === "stageComplete" && message.file === file) {
          window.removeEventListener("message", messageHandler);
          setLoading(false);
          resolve();
        } else if (message.command === "stageError" && message.file === file) {
          window.removeEventListener("message", messageHandler);
          setLoading(false);
          reject(new Error(message.error));
        }
      };

      window.addEventListener("message", messageHandler);

      vscode &&
        vscode.postMessage({
          command: "addStage",
          file: file,
        });

      // 超時處理
      setTimeout(() => {
        window.removeEventListener("message", messageHandler);
        setLoading(false);
        reject(new Error("Operation timeout"));
      }, 5000);
    });
  };

  const removeFromStage = (file) => {
    return new Promise((resolve, reject) => {
      setLoading(true);

      const messageHandler = (event) => {
        const message = event.data;
        if (message.command === "unstageComplete" && message.file === file) {
          window.removeEventListener("message", messageHandler);
          setLoading(false);
          resolve();
        } else if (
          message.command === "unstageError" &&
          message.file === file
        ) {
          window.removeEventListener("message", messageHandler);
          setLoading(false);
          reject(new Error(message.error));
        }
      };

      window.addEventListener("message", messageHandler);

      vscode &&
        vscode.postMessage({
          command: "remove",
          file: file,
        });

      // 超時處理
      setTimeout(() => {
        window.removeEventListener("message", messageHandler);
        setLoading(false);
        reject(new Error("Operation timeout"));
      }, 5000);
    });
  };

  const showDiff = (file) => {
    vscode && vscode.postMessage({ command: "showDiff", file });
  };

  const generateCommitMessage = (modelName) => {
    setLoading(true);
    setCommitMessage("正在生成 Commit Message...");
    vscode &&
      vscode.postMessage({
        command: "generateCommit",
        modelName, // 🚀 把模型選擇傳出去
      });
  };

  // 新增生成摘要方法
  const generateSummary = () => {
    setChangesSummary("正在分析修改內容...");
    setLoading(true);
    vscode && vscode.postMessage({ command: "generateSummary" });
  };

  return {
    greeting,
    gitStatus,
    stagedFiles,
    unstagedFiles: unstagedFiles,
    loading,
    commitMessage,
    whyReason,
    setCommitMessage,
    setWhyReason,
    fetchGreeting,
    fetchGitStatus,
    addToStage,
    removeFromStage,
    showDiff,
    generateCommitMessage,
    changesSummary,
    setChangesSummary,
    generateSummary,
  };
};
