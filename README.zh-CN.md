# Lumina

面向教会的离线优先礼拜 PowerPoint 生成工具。

[English](README.md)

Lumina 帮助礼拜同工把每周重复的主日崇拜流程变成可复用的模板，并通过本地圣经、赞美诗/礼文库、媒体资源和 PPTX 导出引擎，快速生成风格一致、可直接放映的 PowerPoint 文件。目标是减少重复排版和复制粘贴，把时间留给内容核对与礼拜准备本身。

## 功能

- 从流程模板创建礼拜工程。
- 根据经文引用生成启应经文和证道经文幻灯片。
- 管理赞美诗库和礼文库，支持内置条目与用户自建条目。
- 编辑封面、经文、赞美诗、礼文、家事报告、媒体页等段落。
- 设置段落级样式：背景色/背景图、字体、字号、颜色、对齐、边距、启应标识等。
- 为工程附加媒体资源，包括图片和音频。
- 导出标准 `.pptx` 文件，并内嵌引用媒体。
- 导出可在 PowerPoint 中选择和编辑的音频对象，支持点击播放或进入页面自动播放。
- 本地保存工程与模板，容器文件可携带引用媒体跨机器迁移。

Lumina 是本地桌面应用，不依赖账号、云同步或在线协作。

## 架构

Lumina 由本地后端服务和 Electron 桌面前端组成：

```text
lumina/
  backend/    Python FastAPI 后端、领域模型、存储与 PPTX 生成
  frontend/   Electron + React + TypeScript 桌面前端
```

Electron 主进程会启动本地 Python 后端子进程，从 stdout 读取后端绑定的本地端口，并通过 IPC 告知渲染进程。后端默认只监听 `127.0.0.1`。

## 环境要求

- Python 3.11+
- 推荐 Node.js 22
- npm
- PowerPoint、Keynote、WPS 或其他兼容 PPTX 的放映软件

## 快速开始

### 1. 后端环境

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

导入本地圣经数据库：

```bash
python -m app.data.import_bible
```

该命令会生成 `backend/app/data/bible.sqlite`。这是本地生成数据，不应提交到仓库。

### 2. 前端环境

```bash
cd frontend
npm install
```

### 3. 启动桌面应用

在 `frontend/` 下运行：

```bash
npm run dev
```

该命令会同时启动 Vite 和 Electron。Electron 会自动从 `backend/` 启动 Python 后端。

## 分别启动服务

仅启动后端：

```bash
cd backend
source .venv/bin/activate
python -m app.main
```

后端启动时会打印实际端口：

```text
LUMINA_PORT=<port>
```

常用环境变量：

- `LUMINA_HOST`：后端监听主机，默认 `127.0.0.1`
- `LUMINA_PORT`：后端监听端口，默认 `0`，表示由系统选择空闲端口
- `LUMINA_DATA_DIR`：用户数据目录，默认 `~/.lumina`
- `LUMINA_BIBLE_DB`：覆盖 `bible.sqlite` 路径
- `LUMINA_LIBRARY_DB`：覆盖赞美诗/礼文库数据库路径

只启动前端 Vite：

```bash
cd frontend
npm run dev:vite
```

## 构建

前端生产构建：

```bash
cd frontend
npm run build
```

`npm run build` 会先运行 `tsc --noEmit` 做 TypeScript 检查，然后构建 Vite 渲染进程产物。

当前仓库还没有把后端打包和 Electron 安装包制作串成一个统一发布命令。开发阶段请使用 Python 虚拟环境运行后端，并通过 Electron 启动桌面壳。

## 测试

后端测试：

```bash
cd backend
pytest
```

前端校验：

```bash
cd frontend
npm run build
```

目前前端尚未配置独立测试运行器。

## 调试

### 后端

- 直接运行 `python -m app.main` 查看 FastAPI 与启动日志。
- 需要稳定 API 地址时，可设置 `LUMINA_PORT=8000`。
- 默认用户数据位于 `~/.lumina`，除非设置了 `LUMINA_DATA_DIR`。
- 未指定导出路径时，默认 PPTX 导出目录为 `~/.lumina/exports`。

示例：

```bash
cd backend
source .venv/bin/activate
LUMINA_PORT=8000 python -m app.main
```

### Electron 与渲染进程

- `npm run dev` 会输出后端子进程日志，并带有 `[backend]` 前缀。
- 开发模式下渲染进程运行在 `http://127.0.0.1:5173`。
- 使用 Electron 开发者工具查看渲染错误、网络请求和 API 响应。
- 如果后端启动失败，先确认 `backend/.venv` 已创建且依赖已安装。

### PPTX 导出

- PPTX 生成代码位于 `backend/app/pptx/`。
- 媒体文件会复制到每个工程工作目录的 `media/` 下。
- 音频导出使用 PowerPoint 嵌入媒体和 OOXML timing，使导出的音频能在 PowerPoint 中被选中和编辑。

## 数据与存储

运行时用户数据默认位于：

```text
~/.lumina/
  projects/
  templates/
  exports/
  library.db
```

工程和模板容器会携带引用媒体，便于备份和跨机器迁移。

## 文档

- [需求文档](REQUIREMENTS.md)
- [English README](README.md)

## License

见 [LICENSE](LICENSE)。
