const SourceControlHeader = ({isOpen, onToggle, onRefresh}) => {
    return (
        <div className="source-control-header">
            <div className="section-title" onClick={onToggle}>
                <span className="section-icon">{isOpen ? "▼" : "▶"}</span>
                <span>Source Control</span>
            </div>
            <div className="actions">
                <button className="icon-button" onClick={onRefresh} title="重新整理">
                    ↻
                </button>
            </div>
        </div>
    );
};

export default SourceControlHeader;
