#!/usr/bin/env python3
import subprocess
import sys
import os
from datetime import datetime

class GitSync:
    def __init__(self):
        self.repo_path = "/Users/yangjie/code/antigravity"
        os.chdir(self.repo_path)

    def run_command(self, command):
        """执行命令并返回结果"""
        print(f"执行命令: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        return result

    def get_status(self):
        """检查 git 状态"""
        result = self.run_command(["git", "status", "--porcelain"])
        return result.stdout.strip()

    def pull(self):
        """执行 git pull"""
        print("正在拉取远程更新...")
        result = self.run_command(["git", "pull", "origin", "main"])
        if result.returncode != 0:
            if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
                print("错误: 存在合并冲突！请手动处理。")
                print(result.stdout)
                print(result.stderr)
                return False
            else:
                print(f"拉取失败: {result.stderr}")
                return False
        print("拉取成功。")
        return True

    def sync(self):
        """执行同步流程"""
        # 1. Pull
        if not self.pull():
            return

        # 2. Check local changes
        status = self.get_status()
        if not status:
            print("没有本地修改需要提交。")
        else:
            print("检测到本地修改:")
            print(status)
            
            # 3. Add and Commit
            self.run_command(["git", "add", "."])
            commit_msg = f"chore: auto sync updates at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            commit_result = self.run_command(["git", "commit", "-m", commit_msg])
            if commit_result.returncode != 0:
                print(f"提交失败: {commit_result.stderr}")
                return

        # 4. Push
        print("正在推送到远程仓库...")
        push_result = self.run_command(["git", "push", "origin", "main"])
        if push_result.returncode != 0:
            print(f"推送失败: {push_result.stderr}")
            return
        
        print("同步完成！")

if __name__ == "__main__":
    sync_tool = GitSync()
    sync_tool.sync()
