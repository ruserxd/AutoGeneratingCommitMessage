// 獲取 VSCode API
const vscode = acquireVsCodeApi();

// 頁面載入完成時初始化
document.addEventListener("DOMContentLoaded", function () {
  refreshAll();

  // 註冊按鈕點擊事件
  document.getElementById("refreshBtn").addEventListener("click", refreshAll);
  document
    .getElementById("commitBtn")
    .addEventListener("click", generateCommit);
});

// 刷新所有區域
function refreshAll() {
  const refreshBtn = document.getElementById("refreshBtn");
  refreshBtn.innerHTML = "刷新 Git 狀態 <span class='loader'></span>";

  // 獲取 Git Status（含未加入 Stage 的檔案）
  vscode.postMessage({
    command: "getGitStatus",
  });

  // 獲取已加入 Stage 的檔案
  vscode.postMessage({
    command: "initStage",
  });

  // 2秒後恢復按鈕狀態
  setTimeout(() => {
    refreshBtn.innerHTML = "刷新 Git 狀態";
  }, 2000);
}

// 產生 Commit Message
function generateCommit() {
  const commitBtn = document.getElementById("commitBtn");
  commitBtn.innerHTML = "生成 Commit Message <span class='loader'></span>";

  document.getElementById("commit-message").textContent =
    "正在生成 Commit Message...";

  // 向插件發送消息，請求生成 Commit Message
  vscode.postMessage({
    command: "generateCommit",
  });
}

// 顯示文件差異
function showDiff(filePath) {
  vscode.postMessage({
    command: "showDiff",
    file: filePath,
  });
}

// 將檔案添加到 stage
function addToStage(filePath) {
  vscode.postMessage({
    command: "addStage",
    file: filePath,
  });
}

// 將檔案從 stage 移除
function removeFromStage(filePath) {
  vscode.postMessage({
    command: "remove",
    file: filePath,
  });
}

// 監聽來自擴展的消息
window.addEventListener("message", (event) => {
  const message = event.data;

  // 接收並處理從擴展發送過來的數據
  switch (message.command) {
    case "sendData":
      // 處理 Stage 區檔案的數據
      updateStagedFiles(message.data);
      break;
    case "updateStatus":
      // 處理 Git Status 的數據
      updateUnstagedFiles(message.data);
      break;
    case "updateCommit":
      // 處理 Commit Message 的數據
      updateCommitMessage(message.data);
      document.getElementById("commitBtn").innerHTML = "生成 Commit Message";
      break;
  }
});

// 更新未加入 Stage 的檔案列表
function updateUnstagedFiles(data) {
  const unstagedElement = document.getElementById("unstaged");

  // 為了調試，將原始數據輸出到控制台
  console.log("原始 Git Status 資料:", data);

  // 如果沒有數據或數據為空
  if (!data || data.trim() === "") {
    unstagedElement.innerHTML =
      "<div class='section-empty'>無法獲取 Git Status 資訊</div>";
    return;
  }

  try {
    // 解析 Git 狀態資訊，提取未加入 stage 的檔案
    let filesFound = false;
    let html = "";

    // 直接解析未加入 Stage 的 Java 檔案部分
    if (data.includes("未加入 Stage 的 Java 檔案")) {
      const fileSection = data.split("未加入 Stage 的 Java 檔案：")[1];
      if (fileSection) {
        const fileLines = fileSection.split("\n");

        for (let i = 0; i < fileLines.length; i++) {
          const line = fileLines[i].trim();
          if (
            line &&
            line !== "" &&
            !line.startsWith("沒有") &&
            !line.startsWith("已加入")
          ) {
            filesFound = true;
            // 移除可能的前導空格或符號
            let filePath = line;
            if (line.startsWith("  ")) filePath = line.substring(2);

            html += `<div class="file-row">
              <span>${filePath}</span>
              <span class="file-buttons">
                <button class="file-button" onclick="showDiff('${filePath}')">查看差異</button>
                <button class="file-button" onclick="addToStage('${filePath}')">加入 Stage</button>
              </span>
            </div>`;
          }
        }
      }
    }
    // 如果找不到我們特別格式化的輸出，嘗試解析標準 Git 輸出
    else {
      // 嘗試檢測標準 Git 狀態輸出中的未暫存文件
      const lines = data.split("\n");
      let isUnstagedSection = false;

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // 檢測表示未暫存變更的標題
        if (
          line.includes("尚未暫存以備提交的變更") ||
          line.includes("未暫存的變更") ||
          line.includes("Untracked files") ||
          line.includes("Changes not staged for commit") ||
          line.includes("未被追蹤的檔案")
        ) {
          isUnstagedSection = true;
          html += `<div><strong>${line}</strong></div>`;
          continue;
        }

        // 檢測暫存區或其他部分開始，結束未暫存區
        if (
          isUnstagedSection &&
          (line.includes("要提交的變更") ||
            line.includes("Changes to be committed") ||
            (line === "" &&
              i < lines.length - 1 &&
              lines[i + 1].includes("變更")))
        ) {
          isUnstagedSection = false;
          continue;
        }

        // 處理未暫存區中的文件
        if (
          isUnstagedSection &&
          line !== "" &&
          line.includes(".java") &&
          !line.includes(":") &&
          !line.startsWith("(") &&
          !line.startsWith("#")
        ) {
          filesFound = true;
          // 移除可能的前導符號或空格
          let filePath = line;
          if (line.startsWith("\t")) filePath = line.substring(1);
          if (line.startsWith("    ")) filePath = line.substring(4);
          if (line.startsWith("  ")) filePath = line.substring(2);
          if (line.startsWith(" ")) filePath = line.substring(1);

          // 檢查是否以顏色或狀態標記開始 (如 "modified:" 或 "new file:")
          if (filePath.includes("modified:")) {
            filePath = filePath.split("modified:")[1].trim();
          }
          if (filePath.includes("new file:")) {
            filePath = filePath.split("new file:")[1].trim();
          }

          html += `<div class="file-row">
            <span>${filePath}</span>
            <span class="file-buttons">
              <button class="file-button" onclick="showDiff('${filePath}')">查看差異</button>
              <button class="file-button" onclick="addToStage('${filePath}')">加入 Stage</button>
            </span>
          </div>`;
        }
      }
    }

    // 如果找到了未加入 stage 的檔案，顯示它們
    if (filesFound) {
      unstagedElement.innerHTML = html;
    } else {
      unstagedElement.innerHTML =
        "<div class='section-empty'>沒有未加入 Stage 的 Java 檔案</div>";
    }
  } catch (error) {
    console.error("處理 Git 狀態時出錯:", error);
    unstagedElement.innerHTML = `<div class='section-empty'>處理 Git 狀態時出錯: ${error.message}</div>`;
  }
}

// 更新已加入 Stage 的檔案列表
function updateStagedFiles(data) {
  const stagedElement = document.getElementById("staged");

  if (!data || data.trim() === "") {
    stagedElement.innerHTML =
      "<div class='section-empty'>沒有 Java 檔案在 Stage 中</div>";
    return;
  }

  const files = data.trim().split("\n");
  let html = "";

  files.forEach((file) => {
    if (file.trim()) {
      html += `<div class="file-row">
        <span>${file}</span>
        <span class="file-buttons">
          <button class="file-button" onclick="showDiff('${file}')">查看差異</button>
          <button class="file-button" onclick="removeFromStage('${file}')">移除</button>
        </span>
      </div>`;
    }
  });

  stagedElement.innerHTML =
    html || "<div class='section-empty'>沒有 Java 檔案在 Stage 中</div>";
}

// 更新 Commit Message
function updateCommitMessage(data) {
  const commitElement = document.getElementById("commit-message");
  commitElement.textContent = data;
}
