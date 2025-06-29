const FileItem = ({
                      file,
                      isSelected,
                      onSelect,
                      onStage,
                      onUnstage,
                      onShowDiff,
                      isStaged = false,
                  }) => {
    const handleFileClick = (e) => {
        // 如果點擊的是按鈕，不選擇檔案
        if (e.target.closest(".action-button")) {
            return;
        }
        onSelect(file);
    };

    const handleStage = (e) => {
        e.preventDefault();
        e.stopPropagation();
        onStage(file);
    };

    const handleUnstage = (e) => {
        e.preventDefault();
        e.stopPropagation();
        onUnstage(file);
    };

    const handleShowDiff = (e) => {
        e.preventDefault();
        e.stopPropagation();
        onShowDiff(file);
    };

    return (
        <div
            className={`file-item ${isSelected ? "selected" : ""}`}
            onClick={handleFileClick}
        >
      <span className="file-name" title={file}>
        {file}
      </span>
            {isStaged ? (
                <button
                    className="action-button unstage"
                    onClick={handleUnstage}
                    title={`Unstage ${file}`}
                >
                    −
                </button>
            ) : (
                <div className="file-actions">
                    <button
                        className="action-button stage"
                        onClick={handleStage}
                        title={`Stage ${file}`}
                    >
                        +
                    </button>
                    <button
                        className="action-button diff"
                        onClick={handleShowDiff}
                        title={`Show diff for ${file}`}
                    >
                        ✓
                    </button>
                </div>
            )}
        </div>
    );
};

export default FileItem;
