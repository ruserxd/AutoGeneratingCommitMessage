import { useCallback } from "react";

const CommitInput = ({
  commitMessage,
  onCommitMessageChange,
  onGenerateCommit,
  loading,
  hasStagedFiles,
}) => {
  const handleGenerateClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      onGenerateCommit();
    },
    [onGenerateCommit]
  );

  const handleTextareaChange = useCallback(
    (e) => {
      onCommitMessageChange(e.target.value);
    },
    [onCommitMessageChange]
  );

  const handleContainerClick = useCallback((e) => {
    e.stopPropagation();
  }, []);

  return (
    <div className="commit-input" onClick={handleContainerClick}>
      <textarea
        placeholder="Message (press Ctrl+Enter to commit)"
        value={commitMessage}
        onChange={handleTextareaChange}
      />
      <div className="commit-actions">
        <button
          className="generate-button"
          onClick={handleGenerateClick}
          disabled={loading || !hasStagedFiles}
          title="生成 Commit Message"
        >
          {loading ? "生成中..." : "生成 Commit Message"}
        </button>
      </div>
    </div>
  );
};

export default CommitInput;
