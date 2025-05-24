import { useState, useEffect, useMemo } from 'react';
import './App.css';

function App() {
  const [greeting, setGreeting] = useState('');
  const [gitStatus, setGitStatus] = useState('未獲取 Git 狀態');
  const [stagedFiles, setStagedFiles] = useState([]);
  const [unstagedFiles, setUnstagedFiles] = useState([]);
  const [selectedStagedFile, setSelectedStagedFile] = useState('');
  const [selectedUnstagedFile, setSelectedUnstagedFile] = useState('');
  const [loading, setLoading] = useState(false);
  const [commitMessage, setCommitMessage] = useState('')
  const [whyReason, setWhyReason] = useState('尚未分析');
  
  // 展開/收合狀態
  const [sourceControlOpen, setSourceControlOpen] = useState(true);
  const [stagedOpen, setStagedOpen] = useState(true);
  const [changesOpen, setChangesOpen] = useState(true);
  const [commitMessageOpen, setCommitMessageOpen] = useState(true);
  const [whyOpen, setWhyOpen] = useState(false);
  

  // 使用 useMemo 来获取 vscode API
  const vscode = useMemo(() => {
    if (typeof acquireVsCodeApi !== 'undefined') {
      return acquireVsCodeApi();
    }
    return null;
  }, []);

  useEffect(() => {
    const messageHandler = (event) => {
      const message = event.data;
      console.log('收到訊息:', message);

      switch (message.command) {
        case 'greetResult':
          if (message.error) {
            setGreeting(`錯誤: ${message.error}`);
          } else {
            setGreeting(message.message);
          }
          break;
        case 'updateStatus':
          setGitStatus(message.data);
          // 解析未加入 Stage 的 Java 檔案列表
          if (message.data.includes('未加入 Stage 的 Java 檔案')) {
            const lines = message.data.split('\n');
            lines.shift(); // 移除第一行標題
            setUnstagedFiles(lines.map(line => line.trim()).filter(Boolean));
          } else {
            setUnstagedFiles([]);
          }
          setLoading(false);
          break;
        case 'sendData':
          // 解析已加入 Stage 的 Java 檔案
          const files = message.data ? message.data.split(/\s+/).filter(file => file.trim()) : [];
          setStagedFiles(files);
          setLoading(false);
          break;
        case 'updateCommit': // 處理生成的 Commit Message
          setCommitMessage(message.data);
          setLoading(false);
          break;
        case 'updateWhy':
          setWhyReason(message.data);
          setLoading(false);
          break;
      }
    };

    window.addEventListener('message', messageHandler);

    // 初始化時獲取 Git 狀態
    initializeGitStatus();

    return () => {
      window.removeEventListener('message', messageHandler);
    };
  }, []);

  const initializeGitStatus = () => {
    setLoading(true);
    vscode && vscode.postMessage({ command: 'initStage' });
    vscode && vscode.postMessage({ command: 'getGitStatus' });
  };

  const fetchGreeting = () => {
    setGreeting('獲取中...');
    vscode && vscode.postMessage({ command: 'getGreet' });
  };

  const fetchGitStatus = () => {
    setLoading(true);
    setGitStatus('獲取 Git 狀態中...');
    vscode && vscode.postMessage({ command: 'getGitStatus' });
  };

  const addToStage = (file) => {
    setLoading(true);
    vscode && vscode.postMessage({ 
      command: 'addStage',
      file: file
    });
  };

  const removeFromStage = (file) => {
    setLoading(true);
    vscode && vscode.postMessage({
      command: 'remove',
      file: file
    });
  };

  const showDiff = (file) => {
    vscode && vscode.postMessage({
      command: 'showDiff',
      file: file
    });
  };

  const generateCommitMessage = () => { // 新增生成 Commit Message 的函數
    setLoading(true);
    setCommitMessage('正在生成 Commit Message...');
    vscode && vscode.postMessage({ command: 'generateCommit' });
  };

  const generateWhy = () => {
    setWhyReason('正在分析修改原因...');
    setLoading(true);
    vscode && vscode.postMessage({ command: 'generateWhy' });
  };

  return (
    <div className="app-container">
      {/* Source Control Header */}
      <div className="source-control-header">
        <div className="section-title" onClick={() => setSourceControlOpen(!sourceControlOpen)}>
          {sourceControlOpen ? <span className="section-icon">▼</span> : <span className="section-icon">▶</span>}
          <span>Source Control</span>
        </div>
        <div className="actions">
          <button className="icon-button" onClick={fetchGitStatus} title="重新整理">↻</button>
          <button className="icon-button" title="確認">✓</button>
          <button className="icon-button" title="更多選項">⋯</button>
        </div>
      </div>

      {sourceControlOpen && (
        <>
          {/* Commit 輸入框 */}
          <div className="commit-input">
            <textarea 
              placeholder="Message (press Ctrl+Enter to commit)"
              value={commitMessage}
              onChange={(e) => setCommitMessage(e.target.value)}
            ></textarea>
            <div className="commit-actions">
              <span>Commit</span>
              <button className="commit-button">
                <span className="check-icon">✓</span> Commit
              </button>
            </div>
          </div>

          {/* Staged Changes Section */}
          <div className="git-section">
            <div className="section-header" onClick={() => setStagedOpen(!stagedOpen)}>
              {stagedOpen ? <span className="section-icon">▼</span> : <span className="section-icon">▶</span>}
              <span>Staged Changes</span>
              <div className="section-counters">
                <span className="counter">{stagedFiles.length}</span>
                <button className="action-button unstage-all">−</button>
              </div>
            </div>

            {stagedOpen && (
              <div className="file-list">
                {stagedFiles.length > 0 ? (
                  stagedFiles.map((file, index) => (
                    <div 
                      key={index} 
                      className={`file-item ${selectedStagedFile === file ? 'selected' : ''}`}
                      onClick={() => setSelectedStagedFile(file)}
                    >
                      <span className="file-name">{file}</span>
                      <button 
                        className="action-button unstage"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeFromStage(file);
                        }}
                      >−</button>
                    </div>
                  ))
                ) : (
                  <div className="empty-message">No staged changes</div>
                )}
              </div>
            )}
          </div>

          {/* Changes (Unstaged) Section */}
          <div className="git-section">
            <div className="section-header" onClick={() => setChangesOpen(!changesOpen)}>
              {changesOpen ? <span className="section-icon">▼</span> : <span className="section-icon">▶</span>}
              <span>Changes</span>
              <div className="section-counters">
                <span className="counter">{unstagedFiles.length}</span>
                <button className="action-button stage-all">+</button>
              </div>
            </div>

            {changesOpen && (
              <div className="file-list">
                {unstagedFiles.length > 0 ? (
                  unstagedFiles.map((file, index) => (
                    <div 
                      key={index} 
                      className={`file-item ${selectedUnstagedFile === file ? 'selected' : ''}`}
                      onClick={() => setSelectedUnstagedFile(file)}
                    >
                      <span className="file-name">{file}</span>
                      <div className="file-actions">
                        <button 
                          className="action-button stage"
                          onClick={(e) => {
                            e.stopPropagation();
                            addToStage(file);
                          }}
                        >+</button>
                        <button 
                          className="action-button diff"
                          onClick={(e) => {
                            e.stopPropagation();
                            showDiff(file);
                          }}
                        >✓</button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-message">No changes</div>
                )}
              </div>
            )}
          </div>

          {/* Commit Message Generator */}
          <div className="git-section">
            <div className="section-header" onClick={() => setCommitMessageOpen(!commitMessageOpen)}>
              {commitMessageOpen ? <span className="section-icon">▼</span> : <span className="section-icon">▶</span>}
              <span>Commit Message 生成</span>
              <button 
                className="generate-button"
                onClick={generateCommitMessage}
                disabled={loading || stagedFiles.length === 0}
              >
                {loading ? '生成中...' : '生成 Commit Message'}
              </button>
            </div>

            {commitMessageOpen && (
              <div className="commit-message-display">
                {commitMessage || '尚未生成 Commit Message'}
              </div>
            )}
          </div>

          {/* Why Panel */}
          <div className="git-section">
            <div className="section-header" onClick={() => setWhyOpen(!whyOpen)}>
              {whyOpen ? <span className="section-icon">▼</span> : <span className="section-icon">▶</span>}
              <span>Why 為何要修改</span>
              <button 
                className="generate-button"
                onClick={generateWhy}
                disabled={loading || stagedFiles.length === 0}
              >
                {loading ? '分析中...' : '分析 Why'}
              </button>
            </div>

            {whyOpen && (
              <div className="section-content">
                <textarea 
                  value={whyReason}
                  onChange={(e) => setWhyReason(e.target.value)}
                ></textarea>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default App;