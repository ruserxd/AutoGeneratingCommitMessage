import { useState, useEffect, useMemo } from 'react';
import reactLogo from './assets/react.svg';
import './App.css';

function App() {
  const [greeting, setGreeting] = useState('');
  const [gitStatus, setGitStatus] = useState('未獲取 Git 狀態');
  const [stagedFiles, setStagedFiles] = useState([]);
  const [unstagedFiles, setUnstagedFiles] = useState([]);
  const [selectedStagedFile, setSelectedStagedFile] = useState('');
  const [selectedUnstagedFile, setSelectedUnstagedFile] = useState('');
  const [loading, setLoading] = useState(false);
  const [commitMessage, setCommitMessage] = useState(''); // 新增 Commit Message 狀態

  const vscode = useMemo(() => acquireVsCodeApi(), []);

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
            setUnstagedFiles(lines.map(line => line.trim()));
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
    vscode.postMessage({ command: 'initStage' });
    vscode.postMessage({ command: 'getGitStatus' });
  };

  const fetchGreeting = () => {
    setGreeting('獲取中...');
    vscode.postMessage({ command: 'getGreet' });
  };

  const fetchGitStatus = () => {
    setLoading(true);
    setGitStatus('獲取 Git 狀態中...');
    vscode.postMessage({ command: 'getGitStatus' });
  };

  const addToStage = (file) => {
    setLoading(true);
    vscode.postMessage({ 
      command: 'addStage',
      file: file
    });
  };

  const removeFromStage = (file) => {
    setLoading(true);
    vscode.postMessage({
      command: 'remove',
      file: file
    });
  };

  const showDiff = (file) => {
    vscode.postMessage({
      command: 'showDiff',
      file: file
    });
  };

  const generateCommitMessage = () => { // 新增生成 Commit Message 的函數
    setLoading(true);
    setCommitMessage('正在生成 Commit Message...');
    vscode.postMessage({ command: 'generateCommit' });
  };

  return (
    <div className="app-container">
      <div className="header">
        <a href="https://react.dev" target="_blank" rel="noreferrer">
          <img src={reactLogo} className="logo react" alt="React logo" />
        </a>
        <h1>Git Commit 訊息生成器</h1>
      </div>

      {/* 測試區塊 */}
      <div className="card">
        <button onClick={fetchGreeting}>測試 API 連線</button>
        <p>回應: {greeting || '尚未獲取'}</p>
      </div>

      {/* Git 操作區塊 */}
      <div className="git-container">
        <div className="git-header">
          <h2>Git 檔案管理</h2>
          <button 
            className="refresh-button"
            onClick={fetchGitStatus} 
            disabled={loading}
          >
            {loading ? '載入中...' : '重新整理 Git 狀態'}
          </button>
        </div>

        {/* 未加入 Stage 的檔案 */}
        <div className="git-section">
          <h3>未加入 Stage 的 Java 檔案</h3>
          {unstagedFiles.length > 0 ? (
            <ul className="file-list">
              {unstagedFiles.map((file, index) => (
                <li key={index} className="file-item">
                  <span 
                    className={`file-name ${selectedUnstagedFile === file ? 'selected' : ''}`}
                    onClick={() => setSelectedUnstagedFile(file)}
                  >
                    {file}
                  </span>
                  <div className="file-actions">
                    <button 
                      className="action-button add-button"
                      onClick={() => addToStage(file)}
                      disabled={loading}
                    >
                      加入 Stage
                    </button>
                    <button 
                      className="action-button diff-button"
                      onClick={() => showDiff(file)}
                    >
                      檢視差異
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-message">沒有未加入 Stage 的 Java 檔案</p>
          )}
        </div>

        {/* 已加入 Stage 的檔案 */}
        <div className="git-section">
          <h3>已加入 Stage 的 Java 檔案</h3>
          {stagedFiles.length > 0 ? (
            <ul className="file-list">
              {stagedFiles.map((file, index) => (
                <li key={index} className="file-item">
                  <span 
                    className={`file-name ${selectedStagedFile === file ? 'selected' : ''}`}
                    onClick={() => setSelectedStagedFile(file)}
                  >
                    {file}
                  </span>
                  <div className="file-actions">
                    <button 
                      className="action-button remove-button"
                      onClick={() => removeFromStage(file)}
                      disabled={loading}
                    >
                      移出 Stage
                    </button>
                    <button 
                      className="action-button diff-button"
                      onClick={() => showDiff(file)}
                    >
                      檢視差異
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="empty-message">沒有加入 Stage 的 Java 檔案</p>
          )}
        </div>

        {/* 狀態資訊 */}
        <div className="git-section status-section">
          <h3>Git 狀態詳情</h3>
          <pre className="status-display">{gitStatus}</pre>
        </div>

        {/* 生成 Commit Message 區塊 */}
        <div className="git-section commit-section">
          <h3>生成 Commit Message</h3>
          <button 
            className="generate-button"
            onClick={generateCommitMessage}
            disabled={loading || stagedFiles.length === 0}
          >
            {loading ? '生成中...' : '生成 Commit Message'}
          </button>
          <div className="commit-message">
            <h4>生成的 Commit Message:</h4>
            <pre>{commitMessage || '尚未生成'}</pre>
          </div>
        </div>
      </div>

      <footer>
        <p>點擊按鈕來測試 Git 功能</p>
      </footer>
    </div>
  );
}

export default App;