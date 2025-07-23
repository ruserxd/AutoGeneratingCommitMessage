import os
import json
import time
import requests
import re
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass
import logging


@dataclass
class CrawlerConfig:
    """爬蟲配置類"""
    max_skip_streak: int = 50
    repo_pages: int = 2  # 增加搜尋頁數
    repo_per_page: int = 5  # 增加每頁數量
    max_too_long: int = 50
    max_input_length: int = 10000
    max_retries: int = 3
    request_delay: float = 0.5
    per_page_commits: int = 100
    target_repos: List[str] = None  # 指定要抓取的存儲庫
    max_repos_per_run: int = 1  # 每次執行處理的最大專案數


@dataclass
class RepoInfo:
    """Repository 資訊類"""
    owner: str
    name: str
    full_name: str
    stars: int
    forks: int
    language: str
    created_at: str
    updated_at: str


@dataclass
class CommitData:
    """Commit 資料類"""
    input: str
    output: str


class GitHubAPIClient:
    """GitHub API 客戶端"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {"Authorization": f"token {token}"}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, params: Dict = None, max_retries: int = 3) -> requests.Response:
        """發起請求並處理重試機制"""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params)
                
                # 處理 API 限制
                if response.status_code == 403:
                    reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))
                    wait_time = reset_time - int(time.time()) + 10
                    logging.warning(f"API 限制，等待 {wait_time} 秒...")
                    time.sleep(wait_time)
                    continue
                
                # 處理空 repository
                if response.status_code == 409:
                    return response
                
                response.raise_for_status()
                return response
                
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logging.warning(f"請求失敗，重試第 {attempt + 1} 次: {e}")
                time.sleep(2 ** attempt)
        
        raise Exception("達到最大重試次數")
    
    def search_repositories(self, query: str, sort: str = "stars", 
                          order: str = "desc", pages: int = 1, per_page: int = 5) -> List[RepoInfo]:
        """搜尋 repositories"""
        repos = []
        for page in range(1, pages + 1):
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": sort,
                "order": order,
                "per_page": per_page,
                "page": page
            }
            
            response = self._make_request(url, params)
            data = response.json()
            
            for item in data["items"]:
                repo = RepoInfo(
                    owner=item["owner"]["login"],
                    name=item["name"],
                    full_name=item["full_name"],
                    stars=item["stargazers_count"],
                    forks=item["forks_count"],
                    language=item["language"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"]
                )
                repos.append(repo)
            
            time.sleep(1)  # 避免過快請求
        
        return repos
    
    def get_commits(self, owner: str, repo: str, per_page: int = 100, page: int = 1) -> List[Dict]:
        """獲取 commit 列表"""
        url = f"https://api.github.com/repos/{owner}/{repo}/commits"
        params = {"per_page": per_page, "page": page}
        
        response = self._make_request(url, params)
        
        if response.status_code == 409:
            return []  # 空 repository
        
        return response.json()
    
    def get_commit_detail(self, owner: str, repo: str, sha: str) -> Dict:
        """獲取 commit 詳細資訊"""
        url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
        response = self._make_request(url)
        return response.json()


class DataStorage:
    """資料存儲管理類"""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        
        self.training_data_dir = os.path.join(base_dir, "training-data")
        os.makedirs(self.training_data_dir, exist_ok=True)

        # 檔案路徑
        self.seen_sha_path = os.path.join(base_dir, "seen_commits.json")
        self.completed_repos_path = os.path.join(base_dir, "completed_repos.json")
        self.repo_progress_path = os.path.join(base_dir, "repo_progress.json")
    
    def load_seen_shas(self) -> Dict[str, Set[str]]:
        """載入已處理的 commit SHA"""
        if os.path.exists(self.seen_sha_path):
            with open(self.seen_sha_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 轉換為 set 提高查詢效率
                return {repo: set(shas) for repo, shas in data.items()}
        return {}
    
    def save_seen_shas(self, seen_shas: Dict[str, Set[str]]) -> None:
        """保存已處理的 commit SHA"""
        # 轉換為 list 以便 JSON 序列化
        save_data = {repo: list(shas) for repo, shas in seen_shas.items()}
        with open(self.seen_sha_path, "w", encoding="utf-8") as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    def load_completed_repos(self) -> Dict:
        """載入已完成的 repository 列表"""
        if os.path.exists(self.completed_repos_path):
            with open(self.completed_repos_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {repo: {"completed_at": "unknown", "total_commits": 0} for repo in data}
                return data
        return {}
    
    def save_completed_repos(self, completed_repos: Dict) -> None:
        """保存已完成的 repository 列表"""
        with open(self.completed_repos_path, "w", encoding="utf-8") as f:
            json.dump(completed_repos, f, ensure_ascii=False, indent=2)
    
    def load_repo_progress(self) -> Dict:
        """載入 repository 處理進度"""
        if os.path.exists(self.repo_progress_path):
            with open(self.repo_progress_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    
    def save_repo_progress(self, repo_progress: Dict) -> None:
        """保存 repository 處理進度"""
        with open(self.repo_progress_path, "w", encoding="utf-8") as f:
            json.dump(repo_progress, f, ensure_ascii=False, indent=2)
    
    def save_repo_data(self, repo_name: str, data: List[CommitData]) -> Tuple[str, str]:
        """保存 repository 資料並返回檔案路徑"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_repo_name = repo_name.replace("/", "_")
        
        # 保存主要資料
        data_path = os.path.join(self.training_data_dir, f"{safe_repo_name}_{timestamp}.json")
        serializable_data = [{"input": item.input, "output": item.output} for item in data]
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, ensure_ascii=False, indent=2)
        
        return data_path, f"{safe_repo_name}_{timestamp}.json"
    
    def append_repo_temp_data(self, repo_name: str, data: List[CommitData]) -> None:
        """追加儲存中途暫存的資料（commit message 與 patch）"""
        safe_repo_name = repo_name.replace("/", "_")
        temp_path = os.path.join(self.training_data_dir, f"{safe_repo_name}_temp.json")

        serializable_data = [{"input": item.input, "output": item.output} for item in data]

        if os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        existing.extend(serializable_data)
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)



class JavaPatchExtractor:
    """Java patch 提取器"""
    
    @staticmethod
    def extract_java_patch(commit_data: Dict, repo_info: RepoInfo) -> Optional[CommitData]:
        """提取 Java patch 資訊"""
        message = commit_data["commit"]["message"]
        
        # 過濾含中文的 commit message
        if re.search(r'[\u4e00-\u9fff]', message):
            return None
        
        files = commit_data.get("files", [])
        java_patches = []
        
        for file_data in files:
            filename = file_data.get("filename", "")
            patch = file_data.get("patch", "")
            
            if not filename.endswith(".java") or not patch:
                continue
            
            # 檢查是否主要是註解修改
            if JavaPatchExtractor._is_mostly_comments(patch):
                return None
            
            # 生成完整的 Git diff 格式
            full_patch = JavaPatchExtractor._format_patch(filename, patch)
            java_patches.append(full_patch)
        
        if not java_patches:
            return None
        
        return CommitData(
            input="\n\n".join(java_patches),
            output=message.strip()
        )
    
    @staticmethod
    def _is_mostly_comments(patch: str) -> bool:
        """檢查 patch 是否主要是註解修改"""
        lines = patch.splitlines()
        added_lines = [
            line[1:].strip() 
            for line in lines 
            if line.startswith("+") and not line.startswith("+++")
        ]
        
        if not added_lines:
            return False
        
        comment_indicators = ["//", "*", "/*", "*/"]
        comment_lines = sum(
            1 for line in added_lines
            if any(line.startswith(indicator) for indicator in comment_indicators)
        )
        
        return comment_lines / len(added_lines) > 0.8
    
    @staticmethod
    def _format_patch(filename: str, patch: str) -> str:
        """格式化 patch 為完整的 Git diff 格式"""
        diff_header = f"diff --git a/{filename} b/{filename}\n"
        file_header = f"--- a/{filename}\n+++ b/{filename}\n"
        return diff_header + file_header + patch


class JavaRepoCrawler:
    """Java Repository 爬蟲主類"""
    
    def __init__(self, config: CrawlerConfig, token: str, base_dir: str):
        self.config = config
        self.api_client = GitHubAPIClient(token)
        self.storage = DataStorage(base_dir)
        self.extractor = JavaPatchExtractor()
        
        # 設置日誌
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def crawl_complete_repo(self, repo_info: RepoInfo, seen_shas: Dict[str, Set[str]], 
                           repo_progress: Dict) -> List[CommitData]:
        """完整抓取一個 repository 的所有 Java commits"""
        full_name = repo_info.full_name
        self.logger.info(f"開始完整抓取：{full_name} (⭐{repo_info.stars})")
        
        # 初始化專案特定的 SHA 追蹤
        if full_name not in seen_shas:
            seen_shas[full_name] = set()
        repo_seen_shas = seen_shas[full_name]
        
        # 檢查進度
        progress = self._load_or_create_progress(repo_info, repo_progress)
        
        results = []
        page = progress["last_page"]
        skip_streak = 0
        too_long_count = 0
        total_processed = progress["total_processed"]
        
        try:
            while True:
                commits = self.api_client.get_commits(
                    repo_info.owner, repo_info.name, 
                    self.config.per_page_commits, page
                )
                
                if not commits:
                    self.logger.info(f"第 {page} 頁無更多 commit，專案抓取完成")
                    break
                
                self.logger.info(f"處理第 {page} 頁，共 {len(commits)} 個 commit")
                
                page_results = self._process_commits_page(
                    commits, repo_info, repo_seen_shas, 
                    skip_streak, too_long_count, total_processed
                )
                
                results.extend(page_results['commits'])
                 # ✅ 即時保存暫存檔
                if page_results['commits']:
                    self.storage.append_repo_temp_data(full_name, page_results['commits'])
                skip_streak = page_results['skip_streak']
                too_long_count = page_results['too_long_count']
                total_processed = page_results['total_processed']
                
                # 更新進度
                self._update_progress(progress, page, len(results), total_processed)
                self.storage.save_repo_progress(repo_progress)
                
                page += 1
                
                # 定期報告進度
                if page % 10 == 0:
                    self.logger.info(f"進度報告：已處理 {page} 頁，收集 {len(results)} 筆有效資料")
        
        except Exception as e:
            self.logger.error(f"抓取過程中發生錯誤: {e}")
            raise
        
        # 標記完成
        self._mark_completed(progress, len(results), page - 1)
        self.storage.save_repo_progress(repo_progress)
        
        self.logger.info(f"專案 {full_name} 抓取完成！統計：處理了 {total_processed} 個 commit，獲得 {len(results)} 筆有效 Java 資料")
        
        return results
    
    def _load_or_create_progress(self, repo_info: RepoInfo, repo_progress: Dict) -> Dict:
        """載入或創建進度記錄"""
        full_name = repo_info.full_name
        if full_name in repo_progress:
            progress = repo_progress[full_name]
            self.logger.info(f"從第 {progress.get('last_page', 1)} 頁繼續，已收集 {progress.get('collected_count', 0)} 筆")
            return progress
        else:
            progress = {
                "owner": repo_info.owner,
                "name": repo_info.name,
                "full_name": full_name,
                "stars": repo_info.stars,
                "start_time": datetime.now().isoformat(),
                "last_page": 1,
                "collected_count": 0,
                "total_processed": 0,
                "status": "processing"
            }
            repo_progress[full_name] = progress
            return progress
    
    def _process_commits_page(self, commits: List[Dict], repo_info: RepoInfo, 
                             repo_seen_shas: Set[str], skip_streak: int, 
                             too_long_count: int, total_processed: int) -> Dict:
        """處理一頁的 commits"""
        results = []
        
        for commit in commits:
            sha = commit["sha"]
            total_processed += 1
            
            if sha in repo_seen_shas:
                self.logger.debug(f"Commit {sha[:7]} 已存在，跳過")
                continue
            
            try:
                detail = self.api_client.get_commit_detail(repo_info.owner, repo_info.name, sha)
                data = self.extractor.extract_java_patch(detail, repo_info)
                
                if data:
                    if len(data.input) > self.config.max_input_length:
                        too_long_count += 1
                        self.logger.debug(f"Commit {sha[:7]} 過長跳過（{too_long_count}/{self.config.max_too_long}）")
                        if too_long_count >= self.config.max_too_long:
                            self.logger.warning("過長 commit 過多，但繼續處理...")
                        continue

                    results.append(data)
                    repo_seen_shas.add(sha)
                    # 讀取目前所有 repo 的 seen_sha，再更新目前這個 repo 的
                    all_seen_shas = self.storage.load_seen_shas()
                    all_seen_shas[repo_info.full_name] = repo_seen_shas
                    self.storage.save_seen_shas(all_seen_shas)

                    skip_streak = 0
                    self.logger.debug(f"Commit {sha[:7]} saved")

                else:
                    skip_streak += 1
                    if skip_streak % 100 == 0:
                        self.logger.info(f"已跳過 {skip_streak} 個無 Java 變更的 commit")
                    
                    if skip_streak >= self.config.max_skip_streak:
                        self.logger.warning(f"連續跳過 {self.config.max_skip_streak} 個 commit，但繼續處理...")
                        skip_streak = 0
                
                time.sleep(self.config.request_delay)
                
            except Exception as e:
                self.logger.warning(f"Commit {sha[:7]} 處理錯誤: {e}")
        
        return {
            'commits': results,
            'skip_streak': skip_streak,
            'too_long_count': too_long_count,
            'total_processed': total_processed
        }
    
    def _update_progress(self, progress: Dict, page: int, collected_count: int, total_processed: int) -> None:
        """更新進度"""
        progress["last_page"] = page
        progress["collected_count"] = collected_count
        progress["total_processed"] = total_processed
    
    def _mark_completed(self, progress: Dict, final_count: int, total_pages: int) -> None:
        """標記為完成狀態"""
        progress["status"] = "completed"
        progress["end_time"] = datetime.now().isoformat()
        progress["final_count"] = final_count
        progress["total_pages"] = total_pages
    
    def run(self) -> None:
        """執行爬蟲主流程 - 改進版"""
        self.logger.info("開始處理...")
        
        # 載入狀態
        seen_shas = self.storage.load_seen_shas()
        completed_repos = self.storage.load_completed_repos()
        repo_progress = self.storage.load_repo_progress()
        
        # 報告現有狀態
        self.logger.info(f"📊 現有狀態：已完成 {len(completed_repos)} 個專案")
        
        # 指定了特定的存儲庫
        if self.config.target_repos:
            self.logger.info(f"🎯 使用指定的存儲庫：{self.config.target_repos}")
            repo_list = self._get_specific_repos(self.config.target_repos)
        else:
            # 擴大搜尋範圍，增加多樣性
            self.logger.info(f"🔍 搜尋熱門 Java 專案...")
            repo_list = self._search_diverse_repos()
        
        # 過濾已完成的專案
        new_repos = self._filter_new_repos(repo_list, completed_repos)
        
        if not new_repos:
            self.logger.info("❌ 沒有新的 repository 需要處理")
            self._suggest_next_steps(completed_repos)
            return
        
        self.logger.info(f"✅ 找到 {len(new_repos)} 個新的 repository")
        
        # 🔥 改進：處理多個專案而不是只處理一個
        processed_count = 0
        max_repos_per_run = self.config.max_repos_per_run
        
        for i, repo_info in enumerate(new_repos[:max_repos_per_run]):
            self.logger.info(f"🚀 處理專案 {i+1}/{min(len(new_repos), max_repos_per_run)}: {repo_info.full_name}")
            
            try:
                # 抓取資料
                repo_results = self.crawl_complete_repo(repo_info, seen_shas, repo_progress)
                
                # 保存結果
                self._save_results(repo_info, repo_results, completed_repos)
                processed_count += 1
                
                # 保存中間狀態
                self.storage.save_seen_shas(seen_shas)
                self.storage.save_completed_repos(completed_repos)
                self.storage.save_repo_progress(repo_progress)
                
            except Exception as e:
                self.logger.error(f"❌ 處理專案 {repo_info.full_name} 時發生錯誤: {e}")
                continue  # 繼續處理下一個專案，而不是直接失敗
        
        # 最終保存
        self.storage.save_seen_shas(seen_shas)
        self.storage.save_completed_repos(completed_repos)
        self.storage.save_repo_progress(repo_progress)
        
        # 總結報告
        self._print_final_summary(processed_count, new_repos, completed_repos)
    
    def _search_diverse_repos(self) -> List[RepoInfo]:
        """搜尋多樣化的 repositories"""
        all_repos = []
        
        # 搜尋策略1：按星星數
        self.logger.info("🌟 搜尋按星星數排序的專案...")
        repos_by_stars = self.api_client.search_repositories(
            "language:Java", 
            sort="stars", 
            pages=self.config.repo_pages, 
            per_page=self.config.repo_per_page
        )
        all_repos.extend(repos_by_stars)
        
        # 搜尋策略2：按最近更新
        self.logger.info("🔄 搜尋最近更新的專案...")
        repos_by_updated = self.api_client.search_repositories(
            "language:Java", 
            sort="updated", 
            pages=self.config.repo_pages, 
            per_page=self.config.repo_per_page
        )
        all_repos.extend(repos_by_updated)
        
        # 搜尋策略3：按 fork 數
        self.logger.info("🍴 搜尋按 fork 數排序的專案...")
        repos_by_forks = self.api_client.search_repositories(
            "language:Java", 
            sort="forks", 
            pages=self.config.repo_pages, 
            per_page=self.config.repo_per_page
        )
        all_repos.extend(repos_by_forks)
        
        # 去重並保持順序
        unique_repos = {}
        for repo in all_repos:
            if repo.full_name not in unique_repos:
                unique_repos[repo.full_name] = repo
        
        repo_list = list(unique_repos.values())
        self.logger.info(f"🔍 搜尋到 {len(repo_list)} 個不重複的專案")
        
        return repo_list
    
    def _suggest_next_steps(self, completed_repos: Dict) -> None:
        """建議下一步操作"""
        self.logger.info("💡 建議：")
        
        if len(completed_repos) == 0:
            self.logger.info("  - 檢查網路連接和 GitHub Token")
            self.logger.info("  - 確認搜尋條件是否正確")
        elif len(completed_repos) < 5:
            self.logger.info("  - 增加 repo_pages 或 repo_per_page 來搜尋更多專案")
            self.logger.info("  - 或者使用 target_repos 指定特定專案")
        else:
            self.logger.info("  - 考慮使用不同的搜尋關鍵字")
            self.logger.info("  - 或者清理 completed_repos.json 重新開始")
            self.logger.info("  - 檢查是否需要更多訓練資料")
    
    def _print_final_summary(self, processed_count: int, new_repos: List[RepoInfo], completed_repos: Dict) -> None:
        """打印最終總結"""
        self.logger.info("=" * 60)
        self.logger.info(f"🎉 本次執行完成！")
        self.logger.info(f"📊 本次處理：{processed_count} 個專案")
        self.logger.info(f"📈 總計完成：{len(completed_repos)} 個專案")
        
        if processed_count > 0:
            self.logger.info(f"✅ 成功處理的專案：")
            for i in range(processed_count):
                if i < len(new_repos):
                    repo = new_repos[i]
                    commits = completed_repos.get(repo.full_name, {}).get('total_commits', 0)
                    self.logger.info(f"  🚀 {repo.full_name}: {commits} 筆 commit")
        
        remaining = len(new_repos) - processed_count
        if remaining > 0:
            self.logger.info(f"⏳ 剩餘待處理：{remaining} 個專案")
            self.logger.info("💡 下次執行將繼續處理剩餘專案")
    
    def _get_specific_repos(self, target_repos: List[str]) -> List[RepoInfo]:
        """獲取指定的存儲庫資訊"""
        repo_list = []
        for repo_name in target_repos:
            try:
                # 使用 GitHub API 獲取特定 repo 的資訊
                url = f"https://api.github.com/repos/{repo_name}"
                response = self.api_client._make_request(url)
                item = response.json()
                
                repo = RepoInfo(
                    owner=item["owner"]["login"],
                    name=item["name"],
                    full_name=item["full_name"],
                    stars=item["stargazers_count"],
                    forks=item["forks_count"],
                    language=item["language"],
                    created_at=item["created_at"],
                    updated_at=item["updated_at"]
                )
                repo_list.append(repo)
                
            except Exception as e:
                self.logger.error(f"無法獲取存儲庫 {repo_name}: {e}")
        
        return repo_list

    def _filter_new_repos(self, repo_list: List[RepoInfo], completed_repos: Dict) -> List[RepoInfo]:
        """過濾出新的 repositories"""
        new_repos = []
        for repo in repo_list:
            if repo.full_name not in completed_repos:
                new_repos.append(repo)
            else:
                completed_info = completed_repos[repo.full_name]
                self.logger.info(f"跳過已完整抓取的 repo: {repo.full_name}")
                self.logger.info(f"完成時間: {completed_info.get('completed_at', 'unknown')}")
                self.logger.info(f"獲得資料: {completed_info.get('total_commits', 0)} 筆")
        return new_repos
    
    def _save_results(self, repo_info: RepoInfo, repo_results: List[CommitData], completed_repos: Dict) -> None:
        """保存結果"""
        safe_repo_name = repo_info.full_name.replace("/", "_")
        temp_path = os.path.join(self.storage.training_data_dir, f"{safe_repo_name}_temp.json")

        # ✅ 若主程式沒有結果，改用暫存檔
        if not repo_results and os.path.exists(temp_path):
            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            repo_results = [CommitData(**item) for item in data]

        if repo_results:
            # 保存資料檔案
            data_path, filename = self.storage.save_repo_data(repo_info.full_name, repo_results)
            self.logger.info(f"專案資料已儲存：{data_path}")
            self.logger.info(f"共獲得 {len(repo_results)} 筆有效的 Java commit 資料")

            # ✅ 成功後清理 temp 檔
            if os.path.exists(temp_path):
                os.remove(temp_path)

            completed_repos[repo_info.full_name] = {
                "completed_at": datetime.now().isoformat(),
                "total_commits": len(repo_results),
                "stars": repo_info.stars,
                "output_file": filename
            }
        else:
            self.logger.warning("本專案無有效的 Java commit 資料")
            completed_repos[repo_info.full_name] = {
                "completed_at": datetime.now().isoformat(),
                "total_commits": 0,
                "stars": repo_info.stars,
                "note": "無有效 Java commit 資料"
            }




def main():
    """主函數"""
    env_path = os.path.join(os.path.dirname(os.getcwd()), '.env')
    load_dotenv(env_path)
    
    github_token = os.getenv('GITHUB_TOKEN', '')
    if not github_token:
        print("❌ 錯誤：請在 .env 檔案中設定 GITHUB_TOKEN")
        return
    
    # 🔍 在執行前檢查現有狀態
    base_dir = os.getcwd()
    storage = DataStorage(base_dir)
    
    completed_repos = storage.load_completed_repos()
    seen_shas = storage.load_seen_shas()
    
    print(f"📊 現有狀態：")
    print(f"  - 已完成專案：{len(completed_repos)} 個")
    print(f"  - 追蹤 SHA 的專案：{len(seen_shas)} 個")
    
    if completed_repos:
        print("📋 已完成的專案：")
        for repo_name, info in list(completed_repos.items())[:5]:  # 只顯示前5個
            commits = info.get('total_commits', 0)
            print(f"  🚀 {repo_name}: {commits} 筆 commit")
        if len(completed_repos) > 5:
            print(f"  ... 還有 {len(completed_repos) - 5} 個已完成的專案")
    
    # 配置
    config = CrawlerConfig(
        max_skip_streak=50,
        repo_pages=3,  # 增加搜尋頁數
        repo_per_page=10,  # 增加每頁數量
        max_too_long=50,
        max_repos_per_run=1,  # 每次處理專案數量
        # target_repos=["spring-projects/spring-boot", "apache/kafka"]  # 如果要指定特定專案，取消註解
    )
    
    print(f"\n⚙️  配置：")
    print(f"  - 搜尋頁數：{config.repo_pages}")
    print(f"  - 每頁專案數：{config.repo_per_page}")
    print(f"  - 每次處理專案數：{config.max_repos_per_run}")
    if config.target_repos:
        print(f"  - 指定專案：{config.target_repos}")
    else:
        print(f"  - 搜尋模式：自動搜尋熱門 Java 專案")
    
    # 創建並執行爬蟲
    crawler = JavaRepoCrawler(config, github_token, base_dir)
    crawler.run()


if __name__ == "__main__":
    main()