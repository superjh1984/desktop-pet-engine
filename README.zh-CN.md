<div align="center">
  <img src="docs/media/hero.png" alt="macOS 桌面宠物引擎" width="100%">

  <h1>macOS 桌面宠物引擎</h1>

  <p>用你自己的角色和动作素材，做一只真正住在 macOS 桌面上的原生宠物。</p>

  <p><a href="README.md">English</a> · <strong>简体中文</strong></p>

  <p>
    <img src="https://img.shields.io/badge/macOS-12%2B-0A84FF?style=flat-square" alt="macOS 12+">
    <img src="https://img.shields.io/badge/Swift-5.9-F05138?style=flat-square" alt="Swift 5.9">
    <img src="https://img.shields.io/badge/AppKit-Native-45CFCF?style=flat-square" alt="原生 AppKit">
    <img src="https://img.shields.io/badge/arch-x86__64%20%7C%20arm64-6B7CFF?style=flat-square" alt="Universal 2">
    <img src="https://img.shields.io/badge/license-Apache--2.0-F5A623?style=flat-square" alt="Apache-2.0">
  </p>
</div>

## 先看它动起来

<div align="center">
  <img src="docs/media/demo.gif" alt="桌面宠物动作演示" width="100%">
</div>

<p align="center">
  <a href="docs/media/demo.mp4">打开 8 秒高清 MP4 演示</a>
</p>

> 首页角色画面来自一个单独保存的非官方角色 Demo，只用于展示引擎效果。角色原始帧、源视频、提示词、安装包和私人项目均未公开；这些首页宣传媒体不属于 Apache-2.0 开源授权，也不代表任何人物、球队、品牌或其他权利方授权、合作或背书。详见 [媒体边界说明](docs/media/README.md)。

## 它不是一张会动的贴纸

这是一个轻量的原生 AppKit 桌宠引擎。宠物拥有透明无边框窗口、像素级命中、拖拽、鼠标方向待机、悬停反应、右键动作菜单和自主动作状态机；窗口透明区域会尽量把鼠标事件交还给桌面。

| 能力 | 已实现 |
| --- | --- |
| 原生桌面体验 | AppKit 透明置顶窗口，不依赖 Electron |
| 精确交互 | 按当前动画帧 Alpha 做像素命中与点击穿透 |
| 行为系统 | 待机、手动动作、随机动作、自主动作与中断恢复 |
| 素材流水线 | 检测 Alpha、黑/绿幕抠像、统一画布、生成 PNG 帧包 |
| 可复现发布 | 一键构建并校验 x86_64 + arm64 Universal 2 App |
| Agent 工作流 | 内置可安装的 Codex 桌宠制作 Skill |

## 鼠标互动

在宠物周围移动鼠标，它会感知指针的位置和移动方向并作出回应。在这段演示中，角色会追踪、伸手捕捉并抓住鼠标指针，而不是简单地循环播放固定动画。

<div align="center">
  <img src="docs/media/mouse-interaction.gif" alt="桌面宠物追踪并抓住鼠标指针" width="80%">
</div>

引擎同时使用逐像素 Alpha 命中检测：拖拽和右键动作菜单只作用于可见角色区域，宠物窗口的透明区域则会尽可能把鼠标事件交还给桌面。

<div align="center">
  <img src="docs/media/desktop-preview.png" alt="原生 macOS 桌面宠物预览" width="100%">
</div>

## 两条命令跑起来

要求：macOS 12 或更高版本、Xcode Command Line Tools。

```bash
git clone https://github.com/superjh1984/desktop-pet-engine.git
cd desktop-pet-engine
./scripts/check_demo.sh
./scripts/run_demo.sh
```

构建产物位于 `dist/桌宠引擎.app`。本地构建采用临时签名；公开发布二进制文件前，请使用自己的 Developer ID 并完成 Apple 公证。

## 换成你自己的角色

1. 复制 `assets_config.example.json` 为 `assets_config.json`。
2. 填入你有权使用的透明视频，或纯黑/纯绿背景视频。
3. 安装 FFmpeg，然后生成帧包并自检：

```bash
./scripts/preprocess_assets.py
./scripts/check_demo.sh
```

预处理脚本会检查编码与 Alpha，必要时抠除纯色背景，将人物等比放入统一的 360×360 透明画布，并写入 `manifest.json`。应用启动后自动读取素材，不需要把动作硬编码进播放器。

<div align="center">
  <img src="docs/media/action-grid.png" alt="桌面宠物动作示例" width="100%">
</div>

仓库内置的 Blob 示例宠物由 `scripts/generate_demo_assets.py` 程序生成，可以随时重新创建：

```bash
python3 -m pip install pillow
./scripts/generate_demo_assets.py
```

## 项目结构

```text
Sources/DesktopPetEngine/  AppKit 桌宠代码与开源 Blob 帧包
scripts/                   素材生成、预处理、构建、媒体与自检脚本
packaging/                 macOS App 包信息
docs/media/                首页截图、GIF、MP4 与媒体边界说明
assets_config.example.json 本地素材配置模板
skill/                     可安装的 Codex 桌宠制作 Skill
```

## 安装 Codex Skill

仓库包含 `build-macos-desktop-pet` Skill。它可以从干净模板创建项目、处理动作素材、构建双架构 App，并在公开发布前扫描本机路径、签名链接、凭据及指定的受限名称。

```bash
cp -R skill/build-macos-desktop-pet ~/.codex/skills/
```

安装后可以直接说：

```text
使用 $build-macos-desktop-pet，把我拥有版权的透明动作视频做成 macOS 桌宠。
```

## 素材与权利边界

- 只提交你创作或已取得明确再分发授权的视觉、音频和角色素材。
- AI 生成不会自动消除真人姓名、肖像、声音、球队标志、球衣、商标或受保护角色可能涉及的权利。
- 每个新增素材包都应记录来源、作者、授权范围和许可证。
- 首页角色宣传媒体仅用于展示引擎，不表示其角色素材已经开源，也不应被提取为素材包继续传播。

## 开源许可

引擎代码、脚本、Skill，以及由 `generate_demo_assets.py` 生成的 Blob 示例素材采用 Apache License 2.0。

`docs/media/hero.png`、`desktop-preview.png`、`action-grid.png`、`demo.gif`、`demo.mp4` 与 `mouse-interaction.gif` 是单独标识的角色展示媒体，明确排除在 Apache-2.0 授权范围之外。用户自行导入的素材同样保持其原有权利状态。

参见 [LICENSE](LICENSE)、[NOTICE](NOTICE)、[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [贡献指南](CONTRIBUTING.md)。
