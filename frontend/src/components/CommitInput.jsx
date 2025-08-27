// CommitInput.jsx
import { useCallback } from "react";

const CommitInput = ({
  commitMessage,
  onCommitMessageChange,
  onGenerateCommit,
  loading,
  hasStagedFiles,

  // ✅ 新增的 props
  selectedLLM,
  onLLMChange,
  llmOptions = [],
}) => {
  const handleGenerateClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      // ✅ 把選到的 LLM 帶回去
      onGenerateCommit?.(selectedLLM);
    },
    [onGenerateCommit, selectedLLM]
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

  const handleLLMChange = useCallback(
    (e) => {
      onLLMChange?.(e.target.value);
    },
    [onLLMChange]
  );

  return (
    <div className="commit-input" onClick={handleContainerClick}>
      {/* ✅ LLM 選擇器 */}
      <div
        className="llm-selector"
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 8,
          alignItems: "center",
        }}
      >
        <label
          htmlFor="llm-select"
          style={{ whiteSpace: "nowrap", fontSize: 12, opacity: 0.8 }}
        >
          生成模型
        </label>
        <select
          id="llm-select"
          value={selectedLLM}
          onChange={handleLLMChange}
          disabled={loading}
          style={{ padding: "6px 8px", borderRadius: 6 }}
          title="選擇用來生成 Commit Message 的 LLM"
        >
          {llmOptions.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

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
