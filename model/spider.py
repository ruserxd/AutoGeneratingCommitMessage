import os
import json
import time
import requests
import re
from datetime import datetime

# ====== 修改這裡 ======
GITHUB_TOKEN = ""
MAX_COMMITS_PER_REPO = 50
MAX_SKIP_STREAK = 10
REPO_PAGES = 2       # 搜尋 repo 頁數
REPO_PER_PAGE = 5    # 每頁 repo 數量
# ======================

HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"}
BASE_SPIDER_DIR = os.path.join(os.getcwd(), "spider-data")
os.makedirs(BASE_SPIDER_DIR, exist_ok=True)
seen_sha_path = os.path.join(BASE_SPIDER_DIR, "seen_commits.json")

# 讀取已處理過的 commit SHA
def load_seen_shas():
    if os.path.exists(seen_sha_path):
        with open(seen_sha_path, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

# 儲存 seen SHA
def save_seen_shas(seen_shas):
    with open(seen_sha_path, "w", encoding="utf-8") as f:
        json.dump(list(seen_shas), f, ensure_ascii=False, indent=2)

def search_java_repos(pages=1, per_page=5):
    repos = []
    for page in range(1, pages + 1):
        url = "https://api.github.com/search/repositories"
        params = {
            "q": "language:Java",
            "sort": "stars",
            "order": "desc",
            "per_page": per_page,
            "page": page
        }
        r = requests.get(url, headers=HEADERS, params=params)
        r.raise_for_status()
        data = r.json()
        for item in data["items"]:
            repos.append((item["owner"]["login"], item["name"]))
        time.sleep(1)
    return repos

def get_commits(owner, repo, per_page=30, page=1):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits"
    params = {"per_page": per_page, "page": page}
    r = requests.get(url, headers=HEADERS, params=params)
    if r.status_code == 409:
        return []  # 空 repo
    r.raise_for_status()
    return r.json()

def get_commit_detail(owner, repo, sha):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{sha}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()

def extract_java_patch(commit_data):
    message = commit_data["commit"]["message"]

    # 1️⃣ 剔除含中文 commit message
    if re.search(r'[\u4e00-\u9fff]', message):
        return None

    files = commit_data.get("files", [])
    java_patches = []

    for f in files:
        filename = f.get("filename", "")
        patch = f.get("patch", "")
        if filename.endswith(".java") and patch:
            # 2️⃣ 檢查是否只改註解
            lines = patch.splitlines()
            added_lines = [line[1:].strip() for line in lines if line.startswith("+") and not line.startswith("+++")]
            total = len(added_lines)
            comment_like = sum(
                1 for line in added_lines
                if line.startswith("//") or line.startswith("*") or line.startswith("/*") or line.startswith("*/")
            )
            if total > 0 and comment_like / total > 0.8:
                return None  # 過濾只改註解的 commit

            # 3️⃣ 補上完整 Git diff 格式
            diff_header = f"diff --git a/{filename} b/{filename}\n"
            file_header = f"--- a/{filename}\n+++ b/{filename}\n"
            full_patch = diff_header + file_header + patch
            java_patches.append(full_patch)

    if not java_patches:
        return None

    return {
        "input": "\n\n".join(java_patches),
        "output": message.strip()
    }
def crawl_repo_commits(owner, repo, seen_shas, max_commits=50, max_skip_streak=10, max_too_long=10):
    print(f"\n📦 開始抓取：{owner}/{repo}")
    results = []
    page = 1
    skip_streak = 0
    too_long_count = 0

    while len(results) < max_commits:
        try:
            commits = get_commits(owner, repo, page=page)
            if not commits:
                break

            for commit in commits:
                if len(results) >= max_commits:
                    break
                sha = commit["sha"]
                if sha in seen_shas:
                    print(f"  🔁 Commit {sha[:7]} 已存在，跳過")
                    continue

                try:
                    detail = get_commit_detail(owner, repo, sha)
                    data = extract_java_patch(detail)
                    if data:
                        # 檢查 input 長度
                        if len(data["input"]) > 7000:
                            too_long_count += 1
                            print(f"  🚫 Commit {sha[:7]} 過長跳過（{too_long_count}/{max_too_long}）")
                            if too_long_count >= max_too_long:
                                print(f"  ❌ 超過允許的過長 commit 次數，停止此 repo")
                                return results
                            continue

                        results.append(data)
                        seen_shas.add(sha)
                        skip_streak = 0
                        print(f"  ✅ Commit {sha[:7]} saved ({len(results)}/{max_commits})")
                    else:
                        skip_streak += 1
                        print(f"  ⏭️ Commit {sha[:7]} skipped（無 .java patch）({skip_streak}/{max_skip_streak})")
                        if skip_streak >= max_skip_streak:
                            print(f"  ❌ 超過允許的無 Java commit 次數，停止此 repo")
                            return results

                    time.sleep(0.8)

                except Exception as e:
                    print(f"  ⚠️ Commit {sha[:7]} error: {e}")
            page += 1

        except Exception as e:
            print(f"  ❌ Error fetching commits: {e}")
            break

    return results


def main():
    print("🚀 開始搜尋熱門 Java 專案...")
    seen_shas = load_seen_shas()
    repo_list = search_java_repos(pages=10, per_page=5)  # 搜尋 50 個 repo（視情況調整）

    all_results = []
    TARGET_TOTAL_RESULTS = 50  # ✅ 你要抓到的總資料量

    for owner, repo in repo_list:
        if len(all_results) >= TARGET_TOTAL_RESULTS:
            break

        repo_results = crawl_repo_commits(
            owner, repo,
            seen_shas,
            max_commits=MAX_COMMITS_PER_REPO,
            max_skip_streak=5,
            max_too_long=5
        )

        if repo_results:
            all_results.extend(repo_results)
        time.sleep(1)

    # 儲存新結果
    if all_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(BASE_SPIDER_DIR, f"all_java_commits_{timestamp}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 共 {len(all_results)} 筆新資料已儲存：{output_path}")
    else:
        print("⚠️ 本次無有效資料")

    # 儲存 SHA 清單
    save_seen_shas(seen_shas)
    print(f"📌 已更新 seen_commits.json（共 {len(seen_shas)} 筆 SHA）")


if __name__ == "__main__":
    main()



