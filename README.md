# M3U8 to MP4 Converter

A simple Python tool to convert M3U8 files to MP4 format.

## Prerequisites

- Python 3.6 or higher
- FFmpeg installed on your system

## Installation

1. Install FFmpeg if you haven't already:
   - Windows: Download from [FFmpeg official website](https://ffmpeg.org/download.html)
   - Make sure FFmpeg is added to your system PATH

2. Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python m3u8_to_mp4.py <m3u8_url_or_path> <output_file>
```

Example:
```bash
python m3u8_to_mp4.py video.m3u8 output.mp4
```

The tool supports both local M3U8 files and M3U8 URLs.

## Features

- Converts M3U8 files to MP4 format
- Supports both local files and URLs
- Maintains original video and audio quality
- Simple command-line interface

## Error Handling

The tool includes basic error handling for:
- File not found
- Invalid M3U8 format
- FFmpeg processing errors
- Network issues (for URLs)

## 使用方法

### 直接使用

1. 下载发布包（包含ffmpeg）
2. 解压后直接运行`gui_converter.exe`
3. 输入M3U8文件路径或URL
4. 选择输出MP4文件位置
5. 点击"开始转换"

### 开发环境

1. 安装Python依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行程序：
   ```bash
   python gui_converter.py
   ```

## ffmpeg配置

程序会按以下顺序查找ffmpeg：

1. 程序目录下的`ffmpeg`文件夹
2. 系统PATH环境变量

如果您没有安装ffmpeg，请：

1. 下载ffmpeg（[官方下载页面](https://ffmpeg.org/download.html)）
2. 将`ffmpeg.exe`和`ffprobe.exe`放在程序目录的`ffmpeg`文件夹中

## 注意事项

- 确保有足够的磁盘空间
- 对于在线URL，需要稳定的网络连接
- 某些M3U8流可能需要额外的认证信息
