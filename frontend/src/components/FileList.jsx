import FileItem from "./FileItem";

const FileList = ({
  files,
  selectedFile,
  onFileSelect,
  onStage,
  onUnstage,
  onShowDiff,
  isStaged = false,
  emptyMessage = "No files",
}) => {
  if (files.length === 0) {
    return <div className="empty-message">{emptyMessage}</div>;
  }

  return (
    <div className="file-list">
      {files.map((file, index) => (
        <FileItem
          key={index}
          file={file}
          isSelected={selectedFile === file}
          onSelect={onFileSelect}
          onStage={onStage}
          onUnstage={onUnstage}
          onShowDiff={onShowDiff}
          isStaged={isStaged}
        />
      ))}
    </div>
  );
};

export default FileList;
