"""
使用 OpenAI Whisper 将音频转换为字幕文件
支持 SRT、VTT、JSON 和 ASS 格式
"""

import os
import json
from pathlib import Path
from typing import List, Tuple, Optional
import whisper
import pysubs2


class SubtitleSegment:
    """字幕段落"""
    def __init__(self, index: int, start: float, end: float, text: str):
        self.index = index
        self.start = start
        self.end = end
        self.text = text
    
    def format_time(self, seconds: float, format_type: str = "srt") -> str:
        """
        格式化时间
        SRT: HH:MM:SS,mmm
        VTT: HH:MM:SS.mmm
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        if format_type == "srt":
            return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
        else:  # vtt
            return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


def transcribe_audio(audio_path: str, model: str = "base", language: str = "zh") -> dict:
    """
    使用 Whisper 转录视频
    
    Args:
        audio_path (str): 视频文件路径
        model (str): Whisper 模型大小 (tiny, base, small, medium, large)
        language (str): 语言代码，如 'zh' 表示中文，'en' 表示英文，None 为自动检测
    
    Returns:
        dict: 转录结果（包含 segments 和文本）
    
    Raises:
        FileNotFoundError: 视频文件不存在
    """
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"视频文件不存在: {audio_path}")
    
    print(f"正在加载 Whisper 模型 ({model})...")
    model_obj = whisper.load_model(model)
    
    print(f"正在转录视频: {audio_path}")
    print(f"语言: {language if language else '自动检测'}")
    
    # 使用指定语言或自动检测；CPU 环境显式关闭 FP16，避免 Whisper 打印警告。
    options = {"fp16": False}
    if language:
        options["language"] = language
    result = model_obj.transcribe(audio_path, **options)
    
    return result


def create_subtitles(result: dict, subtitle_format: str = "srt") -> List[SubtitleSegment]:
    """
    从转录结果创建字幕段落
    
    Args:
        result (dict): Whisper 转录结果
        subtitle_format (str): 字幕格式 ('srt' 或 'vtt')
    
    Returns:
        List[SubtitleSegment]: 字幕段落列表
    """
    segments = []
    
    for i, segment in enumerate(result["segments"], 1):
        sub = SubtitleSegment(
            index=i,
            start=segment["start"],
            end=segment["end"],
            text=segment["text"].strip()
        )
        segments.append(sub)
    
    return segments


def save_srt(segments: List[SubtitleSegment], output_path: str) -> None:
    """
    保存为 SRT 格式字幕
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        for seg in segments:
            f.write(f"{seg.index}\n")
            f.write(f"{seg.format_time(seg.start, 'srt')} --> {seg.format_time(seg.end, 'srt')}\n")
            f.write(f"{seg.text}\n\n")
    
    print(f"✓ SRT 字幕已保存: {output_path}")


def save_vtt(segments: List[SubtitleSegment], output_path: str) -> None:
    """
    保存为 VTT 格式字幕
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("WEBVTT\n\n")
        for seg in segments:
            f.write(f"{seg.format_time(seg.start, 'vtt')} --> {seg.format_time(seg.end, 'vtt')}\n")
            f.write(f"{seg.text}\n\n")
    
    print(f"✓ VTT 字幕已保存: {output_path}")


def save_json(result: dict, output_path: str) -> None:
    """
    保存为 JSON 格式（包含所有信息）
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"✓ JSON 数据已保存: {output_path}")


def save_ass(segments: List[SubtitleSegment], output_path: str) -> None:
    """
    保存为 ASS 格式字幕（支持样式和特效）
    """
    ass = pysubs2.SSAFile()
    
    # 设置脚本信息
    ass.info["Title"] = "Generated Subtitles"
    ass.info["ScriptType"] = "v4.00+"
    ass.info["PlayResX"] = "1920"
    ass.info["PlayResY"] = "1080"
    # 创建默认样式
    default_style = pysubs2.SSAStyle(
        fontname="Arial",
        fontsize=20,
        primarycolor=pysubs2.Color(255, 255, 255),       # 白色
        secondarycolor=pysubs2.Color(255, 0, 0),         # 红色
        outlinecolor=pysubs2.Color(0, 0, 0),             # 黑色
        backcolor=pysubs2.Color(0, 0, 0),                # 黑色背景
        bold=False,
        italic=False,
        outline=2,
        shadow=0,
        alignment=2,
        marginl=0,
        marginr=0,
        marginv=0,
    )
    ass.styles["Default"] = default_style
    
    # 添加字幕
    for seg in segments:
        event = pysubs2.SSAEvent(
            start=int(seg.start * 1000),  # 转换为毫秒
            end=int(seg.end * 1000),
            text=seg.text
        )
        event.style = "Default"
        ass.events.append(event)
    
    # 保存文件
    ass.save(output_path, format_="ass")
    print(f"✓ ASS 字幕已保存: {output_path}")


def audio_to_subtitle(audio_path: str, 
                     output_path: str = None,
                     subtitle_format: str = "srt",
                     model: str = "base",
                     language: str = "zh") -> str:
    """
    将视频转换为字幕文件
    
    Args:
        audio_path (str): 视频文件路径
        output_path (str): 输出字幕文件路径，如果不指定则自动生成
        subtitle_format (str): 字幕格式 ('srt', 'vtt' 或 'json')
        model (str): Whisper 模型大小 ('tiny', 'base', 'small', 'medium', 'large')
        language (str): 语言代码 ('zh' 中文, 'en' 英文, 等)，None 为自动检测
    
    Returns:
        str: 输出字幕文件路径
    """
    
    # 转录音频
    result = transcribe_audio(audio_path, model, language)
    
    # 如果没有指定输出路径，则自动生成
    if output_path is None:
        audio_name = Path(audio_path).stem
        ext = "srt" if subtitle_format == "srt" else (
            "vtt" if subtitle_format == "vtt" else (
            "ass" if subtitle_format == "ass" else "json"))
        output_path = f"{audio_name}.{ext}"
    
    # 创建字幕
    if subtitle_format == "json":
        save_json(result, output_path)
    else:
        segments = create_subtitles(result, subtitle_format)
        
        if subtitle_format == "srt":
            save_srt(segments, output_path)
        elif subtitle_format == "vtt":
            save_vtt(segments, output_path)
        elif subtitle_format == "ass":
            save_ass(segments, output_path)
        else:
            raise ValueError(f"不支持的字幕格式: {subtitle_format}")
    
    print(f"\n✓ 字幕转换成功!")
    print(f"  原始文件: {audio_path}")
    print(f"  输出文件: {output_path}")
    
    return output_path
