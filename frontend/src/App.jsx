import {useState} from "react";
import {useVSCodeApi} from "./hooks/useVSCodeApi";
import SourceControlHeader from "./components/SourceControlHeader";
import CommitInput from "./components/CommitInput";
import GitSection from "./components/GitSection";
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

    // 展開/收合狀態
    const [summaryOpen, setSummaryOpen] = useState(true);
    const [sourceControlOpen, setSourceControlOpen] = useState(true);
    const [stagedOpen, setStagedOpen] = useState(true);
    const [changesOpen, setChangesOpen] = useState(true);

    // 處理批量操作的函數，加上事件阻止冒泡
    const handleUnstageAll = async (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log("Unstage all files");

        // 順序執行 unstage 操作
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
        console.log("Stage all files");

        // 依序執行 stage 操作
        for (const file of unstagedFiles) {
            try {
                await addToStage(file);
                await new Promise((resolve) => setTimeout(resolve, 100));
            } catch (error) {
                console.error(`Failed to stage ${file}:`, error);
            }
        }
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
                        onGenerateCommit={generateCommitMessage}
                        loading={loading}
                        hasStagedFiles={stagedFiles.length > 0}
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
                </>
            )}
        </div>
    );
}

export default App;
