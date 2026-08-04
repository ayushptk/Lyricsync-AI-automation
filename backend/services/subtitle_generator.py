import os
import json
import math
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    def __init__(self, whisperx_json_path: str):
        self.json_path = whisperx_json_path
        with open(self.json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
            
        self.segments = self.data.get("segments", [])
        self._interpolate_missing_word_timings()

    def _interpolate_missing_word_timings(self):
        """
        WhisperX drops 'start' and 'end' keys for words with low confidence.
        This function interpolates those missing timings so karaoke formatting doesn't break.
        """
        for segment in self.segments:
            words = segment.get("words", [])
            if not words:
                continue
                
            seg_start = segment.get("start", 0.0)
            seg_end = segment.get("end", 0.0)
            
            # Simple fallback: if words are missing timings, distribute evenly
            for i, word in enumerate(words):
                if "start" not in word or "end" not in word:
                    # Find nearest previous valid time
                    prev_time = seg_start
                    for j in range(i - 1, -1, -1):
                        if "end" in words[j]:
                            prev_time = words[j]["end"]
                            break
                            
                    # Find nearest next valid time
                    next_time = seg_end
                    for j in range(i + 1, len(words)):
                        if "start" in words[j]:
                            next_time = words[j]["start"]
                            break
                            
                    # Find how many contiguous missing words there are
                    missing_count = 1
                    for j in range(i + 1, len(words)):
                        if "start" not in words[j]:
                            missing_count += 1
                        else:
                            break
                            
                    # Interpolate
                    duration_per_word = (next_time - prev_time) / (missing_count + 1)
                    
                    word["start"] = prev_time + duration_per_word
                    word["end"] = word["start"] + duration_per_word

    @staticmethod
    def _format_time_srt(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _format_time_lrc(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        hundredths = int((seconds - int(seconds)) * 100)
        return f"[{minutes:02d}:{secs:02d}.{hundredths:02d}]"

    def generate_srt(self, output_path: str = None) -> str:
        if output_path is None:
            output_path = self.json_path.replace("_transcription.json", ".srt")
            
        srt_content = ""
        for i, segment in enumerate(self.segments, 1):
            start_time = self._format_time_srt(segment.get("start", 0.0))
            end_time = self._format_time_srt(segment.get("end", 0.0))
            text = segment.get("text", "").strip()
            
            srt_content += f"{i}\n{start_time} --> {end_time}\n{text}\n\n"
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        return output_path

    def generate_lrc(self, output_path: str = None) -> str:
        if output_path is None:
            output_path = self.json_path.replace("_transcription.json", ".lrc")
            
        lrc_content = "[ti:Generated Lyrics]\n[ar:YTSaaS]\n\n"
        for segment in self.segments:
            start_time = self._format_time_lrc(segment.get("start", 0.0))
            text = segment.get("text", "").strip()
            lrc_content += f"{start_time}{text}\n"
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(lrc_content)
        return output_path

    def generate_ass(self, output_path: str = None, aspect_ratio: str = "16:9") -> str:
        if output_path is None:
            output_path = self.json_path.replace("_transcription.json", ".ass")
            
        if aspect_ratio == "9:16":
            play_res_x, play_res_y = 1080, 1920
            font_size = 86
            margin_v = 400
            margin_h = 40
            outline = 4
        else:
            play_res_x, play_res_y = 1920, 1080
            font_size = 64
            margin_v = 80
            margin_h = 80
            outline = 2
            
        ass_header = f"""[Script Info]
Title: Karaoke Generated
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: {play_res_x}
PlayResY: {play_res_y}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Georgia,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,{outline},0,5,{margin_h},{margin_h},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        ass_content = ass_header
        
        def _format_time_ass(seconds: float) -> str:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}:{minutes:02d}:{secs:05.2f}"
            
        for segment in self.segments:
            start_time = _format_time_ass(segment.get("start", 0.0))
            end_time = _format_time_ass(segment.get("end", 0.0))
            
            # Karaoke tags: {\k<duration_in_centiseconds>}
            karaoke_text = ""
            for word in segment.get("words", []):
                w_start = word.get("start", 0.0)
                w_end = word.get("end", 0.0)
                # Centiseconds
                duration_cs = max(0, int(round((w_end - w_start) * 100)))
                w_text = word.get("word", "")
                karaoke_text += f"{{\\k{duration_cs}}}{w_text} "
                
            karaoke_text = karaoke_text.strip()
            # Dialogue: 0,0:00:00.00,0:00:00.00,Default,,0,0,0,,Text
            ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{karaoke_text}\n"
            
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        return output_path
