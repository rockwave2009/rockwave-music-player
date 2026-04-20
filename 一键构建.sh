#!/bin/bash

# 一键构建并上传到 GitHub
# 使用方法: ./一键构建.sh YOUR_GITHUB_USERNAME

clear

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   RockWave Music Player - 一键构建 Windows 版本          ║"
echo "║                                                          ║"
echo "║   ✨ 无需 Windows 电脑                                   ║"
echo "║   ✨ 无需安装 Python                                     ║"
echo "║   ✨ 全自动云端构建                                      ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 检查参数
if [ -z "$1" ]; then
    echo "❌ 使用方法:"
    echo ""
    echo "   ./一键构建.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "   例如:"
    echo "   ./一键构建.sh zhangsan"
    echo ""
    echo "📌 如果你还没有 GitHub 账号:"
    echo "   1. 访问 https://github.com/join 注册"
    echo "   2. 然后运行此脚本"
    echo ""
    exit 1
fi

USERNAME=$1
REPO="rockwave-music-player"

echo "👤 GitHub 用户名: $USERNAME"
echo "📦 仓库名: $REPO"
echo ""

# 步骤 1: 初始化 Git
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 1/4: 初始化 Git 仓库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ ! -d ".git" ]; then
    git init
    echo "✓ Git 仓库已初始化"
else
    echo "✓ Git 仓库已存在"
fi

# 步骤 2: 添加文件
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 2/4: 添加项目文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

git add rockwave_music_play.py
git add .github/workflows/build-windows.yml
git add *.txt 2>/dev/null || true
git add *.md 2>/dev/null || true

echo "✓ 文件已添加"

# 步骤 3: 提交
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 3/4: 提交代码"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

git commit -m "Build Windows executable" 2>/dev/null || git commit -m "Initial commit" --allow-empty 2>/dev/null

echo "✓ 代码已提交"

# 步骤 4: 配置远程仓库
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "步骤 4/4: 配置 GitHub 远程仓库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REPO_URL="https://github.com/$USERNAME/$REPO.git"

if git remote get-url origin >/dev/null 2>&1; then
    git remote set-url origin "$REPO_URL"
    echo "✓ 远程仓库 URL 已更新"
else
    git remote add origin "$REPO_URL"
    echo "✓ 远程仓库已添加"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║                  ✅ 准备完成！                           ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 显示下一步操作
echo "📋 接下来你需要执行 3 个命令:"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "命令 1: 在 GitHub 创建仓库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   访问: https://github.com/new"
echo "   仓库名: $REPO"
echo "   选择: Public"
echo "   点击: Create repository"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "命令 2: 推送代码（复制粘贴执行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   git push -u origin main"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "命令 3: 触发构建（复制粘贴执行）"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   git tag v1.0.0 && git push origin v1.0.0"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "⏳ 执行命令 3 后，等待 5-10 分钟"
echo ""
echo "📥 然后在这里下载:"
echo "   https://github.com/$USERNAME/$REPO/releases"
echo ""
echo "📁 你会得到:"
echo "   • RockWaveMusicPlayer.exe (主程序)"
echo "   • README.txt (说明文件)"
echo ""
echo "🎁 这两个文件就是最终产品，直接发给 Windows 用户即可"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
