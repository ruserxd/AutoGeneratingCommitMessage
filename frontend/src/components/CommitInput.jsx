const CommitInput = ({
  commitMessage,
  onCommitMessageChange,
  onGenerateCommit,
  loading,
  hasStagedFiles,
}) => {
  return (
    <div className="commit-input">
      <textarea
        placeholder="Message (press Ctrl+Enter to commit)"
        value={commitMessage}
        onChange={(e) => onCommitMessageChange(e.target.value)}
      />
      <div className="commit-actions">
        <button
          className="generate-button"
          onClick={onGenerateCommit}
          disabled={loading || !hasStagedFiles}
        >
          {loading ? "生成中..." : "生成 Commit Message"}
        </button>
        <button className="commit-button" title="Commit">
          生成
        </button>
      </div>
    </div>
  );
};

export default CommitInput;
