import ffmpeg
import requests
import os
import sys
import subprocess
import shutil
import tempfile
from urllib.parse import urljoin
import platform

def get_ffmpeg_path():
    """获取ffmpeg可执行文件的路径"""
    temp_dir = None
    try:
        # 获取临时目录
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            temp_dir = os.path.join(tempfile.gettempdir(), 'ffmpeg_temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 从资源目录解压ffmpeg文件
            base_path = sys._MEIPASS
            ffmpeg_resource = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
            ffprobe_resource = os.path.join(base_path, 'ffmpeg', 'ffprobe.exe')
            
            ffmpeg_exe = os.path.join(temp_dir, 'ffmpeg.exe')
            ffprobe_exe = os.path.join(temp_dir, 'ffprobe.exe')
            
            # 仅在文件不存在时复制
            if not os.path.exists(ffmpeg_exe):
                shutil.copy2(ffmpeg_resource, ffmpeg_exe)
            if not os.path.exists(ffprobe_exe):
                shutil.copy2(ffprobe_resource, ffprobe_exe)
        else:
            # 开发环境，使用当前目录
            base_path = os.path.dirname(os.path.abspath(__file__))
            ffmpeg_dir = os.path.join(base_path, 'ffmpeg')
            if not os.path.exists(ffmpeg_dir):
                os.makedirs(ffmpeg_dir, exist_ok=True)
            
            ffmpeg_exe = os.path.join(ffmpeg_dir, 'ffmpeg.exe')
            ffprobe_exe = os.path.join(ffmpeg_dir, 'ffprobe.exe')
            
            # 如果ffmpeg不存在，尝试从系统PATH中复制
            if not os.path.exists(ffmpeg_exe) or not os.path.exists(ffprobe_exe):
                system_ffmpeg = shutil.which('ffmpeg')
                system_ffprobe = shutil.which('ffprobe')
                
                if system_ffmpeg and system_ffprobe:
                    shutil.copy2(system_ffmpeg, ffmpeg_exe)
                    shutil.copy2(system_ffprobe, ffprobe_exe)
                else:
                    raise FileNotFoundError(
                        "未找到ffmpeg！请确保ffmpeg已安装并添加到系统PATH中，"
                        "或将ffmpeg.exe和ffprobe.exe放在程序目录的ffmpeg文件夹中"
                    )
        
        return ffmpeg_exe, ffprobe_exe
    except Exception as e:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        raise e

def probe_video(input_path):
    """使用ffprobe获取视频信息"""
    _, ffprobe_path = get_ffmpeg_path()
    
    try:
        # 添加Windows特定的常量
        if platform.system() == 'Windows':
            CREATE_NO_WINDOW = 0x08000000
        else:
            CREATE_NO_WINDOW = 0
            
        cmd = [
            ffprobe_path,
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            input_path
        ]
        
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              encoding='utf-8', 
                              errors='replace',
                              creationflags=CREATE_NO_WINDOW)  # 添加此标志以隐藏控制台窗口
        if result.returncode != 0:
            raise Exception(f"ffprobe失败: {result.stderr}")
            
        import json
        probe_data = json.loads(result.stdout)
        
        # 查找视频流
        video_stream = next(
            (stream for stream in probe_data.get('streams', [])
             if stream['codec_type'] == 'video'),
            None
        )
        
        if not video_stream:
            raise ValueError("无法获取视频信息")
            
        return probe_data, video_stream
    except Exception as e:
        raise Exception(f"获取视频信息失败: {str(e)}")

def parse_time(time_str):
    """解析时间字符串，返回秒数"""
    try:
        if ':' in time_str:
            parts = time_str.split(':')
            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s
        return float(time_str)
    except:
        return 0

def download_m3u8_to_mp4(m3u8_url, output_file, progress_callback=None):
    try:
        if m3u8_url.startswith(('http://', 'https://')):
            input_stream = m3u8_url
        else:
            if not os.path.exists(m3u8_url):
                raise FileNotFoundError(f"M3U8文件未找到: {m3u8_url}")
            input_stream = m3u8_url

        print(f"正在转换 {m3u8_url} 到 {output_file}")
        
        # 获取ffmpeg路径
        ffmpeg_path, _ = get_ffmpeg_path()
        
        # 获取视频信息
        probe_data, video_info = probe_video(input_stream)
        
        # 获取总时长
        duration = float(probe_data.get('format', {}).get('duration', 0))
        if duration == 0:
            print("警告：无法获取准确的视频时长，进度显示可能不准确")
        
        # 构建ffmpeg命令
        cmd = [
            ffmpeg_path,
            '-i', input_stream,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-y',
            output_file
        ]
        
        # 添加Windows特定的常量
        if platform.system() == 'Windows':
            CREATE_NO_WINDOW = 0x08000000
        else:
            CREATE_NO_WINDOW = 0
        
        # 使用subprocess运行ffmpeg
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            encoding='utf-8',
            errors='replace',
            creationflags=CREATE_NO_WINDOW  # 添加此标志以隐藏控制台窗口
        )
        
        last_progress = 0
        print("开始转换...")
        
        # 读取输出
        while True:
            try:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                    
                if line:
                    # 尝试解析进度
                    if 'time=' in line:
                        try:
                            time_str = line.split('time=')[1].split()[0]
                            current_time = 0
                            
                            # 支持多种时间格式
                            if ':' in time_str:
                                h, m, s = map(float, time_str.split(':'))
                                current_time = h * 3600 + m * 60 + s
                            else:
                                current_time = float(time_str)
                            
                            if duration > 0:
                                progress = min(99.9, (current_time / duration) * 100)
                                if progress > last_progress:
                                    last_progress = progress
                                    if progress_callback:
                                        progress_callback(progress)
                                    else:
                                        # 使用动画进度条
                                        bar_width = 50
                                        filled = int(progress * bar_width / 100)
                                        bar = '=' * filled + '-' * (bar_width - filled)
                                        print(f'\r[{bar}] {progress:.1f}%', end='', flush=True)
                        except Exception as e:
                            continue
            except UnicodeDecodeError:
                continue
        
        # 等待进程完成
        process.wait()
        
        if process.returncode == 0:
            if progress_callback:
                progress_callback(100)
            else:
                bar_width = 50
                bar = '=' * bar_width
                print(f'\r[{bar}] 100.0%')
                print("\n转换完成！")
            print(f"输出文件: {output_file}")
        else:
            try:
                error = process.stderr.read()
                print(f"\n转换失败！错误信息:\n{error}")
            except:
                print("\n转换失败！无法读取错误信息")
            raise Exception("FFmpeg处理失败")
            
    except Exception as e:
        print(f"发生错误: {str(e)}")
        raise

def main():
    if len(sys.argv) != 3:
        print("Usage: python m3u8_to_mp4.py <m3u8_url_or_path> <output_file>")
        print("Example: python m3u8_to_mp4.py video.m3u8 output.mp4")
        sys.exit(1)
    
    m3u8_url = sys.argv[1]
    output_file = sys.argv[2]
    
    download_m3u8_to_mp4(m3u8_url, output_file)

if __name__ == "__main__":
    main()
