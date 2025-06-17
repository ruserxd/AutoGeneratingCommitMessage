import React, { useCallback } from "react";

const StagedSummaryPanel = ({
  isOpen,
  onToggle,
  summary,
  onGenerateSummary,
  loading,
  hasStagedFiles,
}) => {
  console.log("StagedSummaryPanel rendering");

  // 使用 useCallback 避免函數重新創建
  const handleGenerateClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      onGenerateSummary();
    },
    [onGenerateSummary]
  );

  const handleHeaderClick = useCallback(() => {
    onToggle();
  }, [onToggle]);

  return (
    <div className="git-section">
      <div className="section-header" onClick={handleHeaderClick}>
        <div className="section-title-wrapper">
          <span className="section-icon">{isOpen ? "▼" : "▶"}</span>
          <span>修改摘要</span>
        </div>
      </div>

      {isOpen && (
        <div className="section-content">
          <div className="summary-display">{summary || "尚未生成修改摘要"}</div>
          <div className="summary-controls">
            <button
              className="generate-button"
              onClick={handleGenerateClick}
              disabled={loading || !hasStagedFiles}
              title="生成修改內容摘要"
            >
              {loading ? "分析中..." : "生成摘要"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const areEqual = (prevProps, nextProps) => {
  return (
    prevProps.isOpen === nextProps.isOpen &&
    prevProps.summary === nextProps.summary &&
    prevProps.loading === nextProps.loading &&
    prevProps.hasStagedFiles === nextProps.hasStagedFiles
  );
};

export default React.memo(StagedSummaryPanel, areEqual);
