import FileList from "./FileList";

const GitSection = ({
  title,
  isOpen,
  onToggle,
  files,
  selectedFile,
  onFileSelect,
  onStage,
  onUnstage,
  onShowDiff,
  isStaged = false,
  emptyMessage,
  actionButton,
}) => {
  // 處理標題點擊，確保不會與按鈕衝突
  const handleHeaderClick = (e) => {
    // 如果點擊的是按鈕或按鈕的子元素，不執行切換
    if (e.target.closest(".action-button")) {
      return;
    }
    onToggle();
  };

  return (
    <div className="git-section">
      <div className="section-header" onClick={handleHeaderClick}>
        <div className="section-title-wrapper">
          <span className="section-icon">{isOpen ? "▼" : "▶"}</span>
          <span>{title}</span>
        </div>
        <div className="section-counters">
          <span className="counter">{files.length}</span>
          {actionButton}
        </div>
      </div>

      {isOpen && (
        <FileList
          files={files}
          selectedFile={selectedFile}
          onFileSelect={onFileSelect}
          onStage={onStage}
          onUnstage={onUnstage}
          onShowDiff={onShowDiff}
          isStaged={isStaged}
          emptyMessage={emptyMessage}
        />
      )}
    </div>
  );
};

export default GitSection;
