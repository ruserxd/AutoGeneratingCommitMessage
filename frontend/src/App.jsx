// App.jsx
import { useState } from "react";
import { useVSCodeApi } from "./hooks/useVSCodeApi";
import SourceControlHeader from "./components/SourceControlHeader";
import CommitInput from "./components/CommitInput";
import GitSection from "./components/GitSection";
import ActionPanel from "./components/ActionPanel";
import StagedSummaryPanel from "./components/StagedSummaryPanel";
import "./App.css";

function App() {
  const {
    stagedFiles,
    unstagedFiles,
    loading,
    commitMessage,
    setCommitMessage,
    fetchGitStatus,
    addToStage,
    removeFromStage,
    showDiff,
    generateCommitMessage,
    changesSummary,
    setChangesSummary,
    generateSummary,
  } = useVSCodeApi();

  const [selectedStagedFile, setSelectedStagedFile] = useState("");
  const [selectedUnstagedFile, setSelectedUnstagedFile] = useState("");

  const [selectedLLM, setSelectedLLM] = useState(
    "tavernari/git-commit-message:latest"
  );
  const llmOptions = [
    {
      value: "tavernari/git-commit-message:latest",
      label: "tavernari/git-commit-message:latest",
    },
    { value: "llama3.1:latest", label: "llama3.1:latest" },
    { value: "gemini-2.0-flash", label: "gemini-2.0-flash" },
    { value: "code-T5", label: "code-T5" },
  ];

  // 展開/收合狀態
  const [summaryOpen, setSummaryOpen] = useState(true);
  const [sourceControlOpen, setSourceControlOpen] = useState(true);
  const [stagedOpen, setStagedOpen] = useState(true);
  const [changesOpen, setChangesOpen] = useState(true);
  const [actionPanelOpen, setActionPanelOpen] = useState(true);

  const handleUnstageAll = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    for (const file of stagedFiles) {
      try {
        await removeFromStage(file);
        await new Promise((resolve) => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Failed to unstage ${file}:`, error);
      }
    }
  };

  const handleStageAll = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    for (const file of unstagedFiles) {
      try {
        await addToStage(file);
        await new Promise((resolve) => setTimeout(resolve, 100));
      } catch (error) {
        console.error(`Failed to stage ${file}:`, error);
      }
    }
  };

  const handleGenerateCommit = (model) => {
    const useModel = model ?? selectedLLM;
    try {
      generateCommitMessage(useModel);
    } catch {
      // 若 generateCommitMessage 不吃參數也沒關係
      generateCommitMessage();
    }
  };

  const handleActionPanelButton = () => {
    console.log("動作面板按鈕被點擊 (未完成)");
  };

  return (
    <div className="app-container">
      <SourceControlHeader
        isOpen={sourceControlOpen}
        onToggle={() => setSourceControlOpen(!sourceControlOpen)}
        onRefresh={fetchGitStatus}
      />

      {sourceControlOpen && (
        <>
          <CommitInput
            commitMessage={commitMessage}
            onCommitMessageChange={setCommitMessage}
            onGenerateCommit={handleGenerateCommit}
            loading={loading}
            hasStagedFiles={stagedFiles.length > 0}
            selectedLLM={selectedLLM}
            onLLMChange={setSelectedLLM}
            llmOptions={llmOptions}
          />

          <StagedSummaryPanel
            isOpen={summaryOpen}
            onToggle={() => setSummaryOpen(!summaryOpen)}
            summary={changesSummary}
            onSummaryChange={setChangesSummary}
            onGenerateSummary={generateSummary}
            loading={loading}
            hasStagedFiles={stagedFiles.length > 0}
          />

          <GitSection
            title="Staged Changes"
            isOpen={stagedOpen}
            onToggle={() => setStagedOpen(!stagedOpen)}
            files={stagedFiles}
            selectedFile={selectedStagedFile}
            onFileSelect={setSelectedStagedFile}
            onUnstage={removeFromStage}
            isStaged={true}
            emptyMessage="No staged changes"
            actionButton={
              <button
                className="action-button unstage-all"
                onClick={handleUnstageAll}
                title="Unstage all changes"
                disabled={loading || stagedFiles.length === 0}
              >
                −
              </button>
            }
          />

          <GitSection
            title="Changes"
            isOpen={changesOpen}
            onToggle={() => setChangesOpen(!changesOpen)}
            files={unstagedFiles}
            selectedFile={selectedUnstagedFile}
            onFileSelect={setSelectedUnstagedFile}
            onStage={addToStage}
            onShowDiff={showDiff}
            isStaged={false}
            emptyMessage="No changes"
            actionButton={
              <button
                className="action-button stage-all"
                onClick={handleStageAll}
                title="Stage all changes"
                disabled={loading || unstagedFiles.length === 0}
              >
                +
              </button>
            }
          />

          <ActionPanel
            isOpen={actionPanelOpen}
            onToggle={() => setActionPanelOpen(!actionPanelOpen)}
            onButtonClick={handleActionPanelButton}
            loading={loading}
            disabled={false}
            buttonText="檢查方法間的版本歷程"
            buttonTitle="點擊執行檢查方法間的版本歷程"
          />
        </>
      )}
    </div>
  );
}

export default App;
