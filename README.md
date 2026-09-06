# 文件格式转换器 v2.0.0

一个现代化的文件格式转换工具，基于 **Kotlin + JetBrains Compose Multiplatform（Desktop）** 开发，支持多种文件格式的转换。

## 功能特点

- 现代化的 Material Design 3 界面（基于 Compose Desktop）
- 无边框窗口，自定义标题栏（拖动、最小化、最大化、关闭）
- 高 DPI 自适应（支持 125% / 150% 等 Windows 缩放，文字清晰不模糊）
- 支持多种文件格式转换：
  - 视频格式：MP4, AVI, MOV, FLV, MKV, WMV, WEBM, M4V, 3GP
  - 音频格式：MP3, WAV, AAC, FLAC, M4A, OGG, WMA
  - 图片格式：JPG, PNG, BMP, GIF, WEBP, TIFF, ICO
  - 文档格式：PDF, DOCX, TXT（PDF↔DOCX 高保真转换，基于 LibreOffice）
  - 压缩包格式：ZIP, RAR（通过 7-Zip）
- 支持拖拽文件到主窗口直接新建转换任务
- 系统主题适配（跟随 Windows 浅色 / 深色模式，读取系统强调色）
- 开机自启动选项
- FFmpeg 自动检测与安装（可在程序内一键安装）
- 更多信息按钮（显示软件版本、开源许可证、字体信息）

## 运行要求

- 操作系统：Windows 10+
- JDK 17+（开发时需要，打包后免安装）
- LibreOffice（用于 PDF ↔ DOCX 高保真转换，可选）
- 7-Zip（用于压缩包转换，可选）
- FFmpeg（用于音视频转换，可在程序内自动安装）

## 从源代码运行

1. 确保已安装 [JDK 17](https://adoptium.net/) 和 [Gradle](https://gradle.org/)
2. 克隆本项目
3. 运行：
   ```bash
   ./gradlew run
   ```
   或在 Windows 上：
   ```powershell
   .\run.ps1
   ```

## 打包发布

```powershell
# 生成便携版（免安装）
.\portable-package.ps1

# 生成安装程序（需安装 Inno Setup）
.\installer-package.ps1
```

## 使用说明

1. 启动程序后，点击"新建任务"或直接拖放文件到程序窗口
2. 选择要转换的文件
3. 从可用的目标格式列表中选择需要转换的格式
4. 选择保存位置（默认为源文件位置）
5. 点击"开始转换"按钮
6. 在任务列表中查看转换进度

### FFmpeg 说明

本软件使用 FFmpeg 进行音视频转换，您无需手动安装 FFmpeg：

1. 打开软件时会自动检测系统是否已安装 FFmpeg
2. 如果未检测到 FFmpeg，软件会提示安装并在用户确认后自动完成
3. 安装过程包括：
   - 优先从官方源下载 FFmpeg，网络问题时使用内置备用包
   - 解压并配置 FFmpeg
   - 自动添加到用户环境变量
4. FFmpeg 安装完成后可立即使用，无需重启

## 技术栈

- **Kotlin 2.0**
- **JetBrains Compose Multiplatform 1.7（Desktop）**
- **Material Design 3**
- **JNA**（Windows 注册表、DPI 感知、开机自启）
- **Coroutines**（异步任务调度）
- **FFmpeg**（音视频转换）
- **LibreOffice headless**（文档高保真转换）

## 架构

```
com.gsgc.converter
├─ data        # 静态数据与配置（FormatMapping, ConfigManager）
├─ core        # 核心逻辑（FormatConverter, FFmpegLocator/Installer, LibreOfficeLocator）
├─ domain      # 业务模型（ConvertTask, TaskState, FFmpegService）
├─ ui          # UI 组件（MainWindow, TaskListScreen, SettingScreen, AppViewModel）
└─ util        # 工具类（ThemeHelper, AutostartManager）
```

## 开源声明

本软件是完全开源的文件格式转换工具，基于自由软件精神构建。

### 开源协议

本项目采用 **GNU 通用公共许可证第 3 版（GPLv3）**：

1. 自由使用：您可以自由地使用、修改和分发本软件
2. 开放源代码：如果您分发本软件的修改版本，必须同时提供源代码
3. 相同方式共享：任何基于本软件的衍生作品必须使用相同的许可证（GPLv3）
4. 专利授权：本许可证明确授予专利权利
5. 无担保声明：本软件按"原样"提供，不提供任何形式的保证

详见 [LICENSE](LICENSE) 文件或访问 [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)。

### 字体声明

本软件使用 **思源黑体（Source Han Sans SC）** 作为界面字体，由 Adobe 和 Google 联合开发，遵循 **SIL Open Font License 1.1** 协议。

- 字体来源：[Adobe Source Han Sans](https://github.com/adobe-fonts/source-han-sans)
- 字体协议：[SIL Open Font License 1.1](https://scripts.sil.org/OFL)

### 第三方依赖

- [Kotlin](https://kotlinlang.org/) — Apache 2.0
- [JetBrains Compose Multiplatform](https://github.com/JetBrains/compose-multiplatform) — Apache 2.0
- [JNA](https://github.com/java-native-access/jna) — LGPL 2.1 / Apache 2.0
- [FFmpeg](https://ffmpeg.org/) — LGPL 2.1+ / GPL 2+
- [LibreOffice](https://www.libreoffice.org/) — MPL 2.0 / LGPL 3+

## 免责声明

1. 本软件是一个自由的文件格式转换工具，按"现状"免费提供，不提供任何形式的保证
2. 建议在转换重要文件前进行备份
3. 某些格式转换可能会损失部分格式信息
4. 本软件使用了多个开源第三方库，这些库的使用遵循其各自的开源协议

## 联系方式

- 开发者邮箱：2713615817@qq.com
- GitHub 仓库：https://github.com/tidain/format-conversion
