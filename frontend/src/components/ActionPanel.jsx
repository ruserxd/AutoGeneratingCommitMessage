import { useCallback } from "react";

const ActionPanel = ({
  isOpen,
  onToggle,
  onButtonClick,
  loading = false,
  disabled = false,
  buttonText = "執行動作",
  buttonTitle = "點擊執行動作",
}) => {
  const handleButtonClick = useCallback(
    (e) => {
      e.preventDefault();
      e.stopPropagation();
      onButtonClick();
    },
    [onButtonClick]
  );

  const handleHeaderClick = useCallback(
    (e) => {
      if (e.target.closest(".action-button")) {
        return;
      }
      onToggle();
    },
    [onToggle]
  );

  return (
    <div className="git-section">
      <div className="section-header" onClick={handleHeaderClick}>
        <div className="section-title-wrapper">
          <span className="section-icon">{isOpen ? "▼" : "▶"}</span>
          <span>方法間的變更歷程</span>
        </div>
      </div>

      {isOpen && (
        <div className="section-content">
          <div className="action-panel-content">
            <button
              className="generate-button"
              onClick={handleButtonClick}
              disabled={loading || disabled}
              title={buttonTitle}
            >
              {loading ? "執行中..." : buttonText}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionPanel;
