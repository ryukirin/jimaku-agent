import sys
from pathlib import Path
from audio_to_subtitle import audio_to_subtitle


def resolve_output_paths(output_path: str | None, subtitle_format: str) -> str | None:
    """
    将一个用户传入的输出基名和字幕格式组合成完整的字幕文件路径。
    例如 output + srt -> output.srt。
    """
    if output_path is None:
        return None

    base = Path(output_path)
    if base.suffix:
        base = base.with_suffix("")

    subtitle_output_path = str(base.with_suffix(f".{subtitle_format}"))
    return subtitle_output_path


def main():
    """
    命令行入口
    """
    if len(sys.argv) < 2:
        print("用法: python main.py <视频文件路径> [输出文件路径] [字幕格式] [模型] [语言]")
        print("\n示例:")
        print("  python main.py video.mp4")
        print("  python main.py video.mp4 output")
        print("  python main.py video.mp4 output srt")
        print("  python main.py video.mp4 output ass small")
        print("  python main.py video.mp4 output ass base en")
        print("  [模型]           可选，tiny/base/small/medium/large（默认 base）")
        print("  [语言]           可选，语言代码如 zh/en（默认 zh）")
        print("\n字幕格式说明:")
        print("  srt   - SubRip 格式，最常见，兼容性最好")
        print("  vtt   - WebVTT 格式，Web 标准")
        print("  ass   - Advanced SubStation Alpha，支持样式和特效 ⭐")
        print("  json  - JSON 格式，包含所有原始数据")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    subtitle_format = sys.argv[3].lower() if len(sys.argv) > 3 else "srt"
    model = sys.argv[4].lower() if len(sys.argv) > 4 else "base"
    language = sys.argv[5].lower() if len(sys.argv) > 5 else "zh"
    
    # 验证参数
    valid_formats = ["srt", "vtt", "json", "ass"]
    language = sys.argv[5].lower() if len(sys.argv) > 5 else "zh"
    
    # 验证参数
    valid_formats = ["srt", "vtt", "json", "ass"]
    valid_models = ["tiny", "base", "small", "medium", "large"]
    
    if subtitle_format not in valid_formats:
        print(f"错误: 无效的字幕格式。支持: {', '.join(valid_formats)}")
        sys.exit(1)
    
    if model not in valid_models:
        print(f"错误: 无效的模型。支持: {', '.join(valid_models)}")
        sys.exit(1)
    
    try:
        subtitle_output_path = resolve_output_paths(output_path, subtitle_format)
        audio_to_subtitle(video_path, subtitle_output_path, subtitle_format, model, language)
    except FileNotFoundError as e:
        print(f"✗ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ 转换失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
