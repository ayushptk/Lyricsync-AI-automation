"""
Lyric Post-Processor
======================

Applies conservative post-processing to Whisper transcription output
before subtitle generation.

Design principles (from the project spec):
  - NEVER add words that were not in the transcript.
  - NEVER remove words unless they are confirmed hallucinations.
  - NEVER change meaning.
  - NEVER replace slang, artist names, or song-specific words.
  - Only fix obvious recognition errors (e.g. "tonite" -> "tonight").
  - Preserve repeated lyrics, ad-libs, and intentional vocalizations.

The processing pipeline:
  1. Filter segments with very high no_speech_prob (confirmed non-speech)
  2. Flag words with very low probability (< 0.35) as uncertain
  3. Apply conservative spelling correction (only obvious typos)
  4. Detect hallucination patterns (sudden repetition, nonsense sequences)
  5. Validate: if too many words changed, revert to original

The output is the same JSON format as the Whisper output, so it is a
drop-in replacement in the worker pipeline.
"""

import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

# Words with probability below this are marked uncertain (not removed)
WORD_LOW_CONFIDENCE_THRESHOLD = 0.35

# Segments with no_speech_prob above this are dropped entirely
SEGMENT_NO_SPEECH_THRESHOLD = 0.85

# If correction changes more than this fraction of words, reject the correction
MAX_ALLOWED_CORRECTION_RATIO = 0.30

# Maximum ratio of identical consecutive words before treating as hallucination
HALLUCINATION_REPEAT_RATIO = 0.5

# Minimum segment text length to consider for hallucination detection
MIN_HALLUCINATION_CHECK_WORDS = 6


# ---------------------------------------------------------------------------
# Conservative spelling correction dictionary
# ---------------------------------------------------------------------------
# Only correct OBVIOUS recognition errors — not creative spellings, slang,
# or intentional lyrics.  This list is intentionally small to avoid
# over-correcting artistic choices.
#
# Rules for adding to this list:
#   - Must be a clear ASR error, not a lyric choice
#   - Must be unambiguous (only one possible correct word)
#   - Must not change meaning or alter artistic intent
#   - Common slang (gonna, wanna, ain't) is NOT in this list

_SPELLING_CORRECTIONS: Dict[str, str] = {
    # Common ASR errors in music
    "tonite": "tonight",
    "nite": "night",
    "luv": "love",
    "wuz": "was",
    "cuz": "cause",
    # DO NOT ADD: gonna, wanna, gotta, ain't, kinda, sorta
    # These are intentional lyric forms, not transcription errors
}

# Regex for "words" — only match actual word characters
_WORD_RE = re.compile(r"\b\w+\b")


# ---------------------------------------------------------------------------
# Hallucination detection
# ---------------------------------------------------------------------------

def _detect_repetition_hallucination(words: List[Dict]) -> bool:
    """
    Detects Whisper's characteristic hallucination pattern: rapid word repetition.

    Whisper sometimes gets "stuck" and repeats the same word many times when
    it is uncertain.  This is distinct from actual repeated lyrics in a chorus.
    
    We flag it as a hallucination ONLY when:
      - The segment has >= MIN_HALLUCINATION_CHECK_WORDS words
      - More than HALLUCINATION_REPEAT_RATIO of words are identical
      - The repeated words have near-identical short durations (< 200ms each)
        — real lyrics have natural timing variation

    Returns True if the segment looks like a repetition hallucination.
    """
    if not words or len(words) < MIN_HALLUCINATION_CHECK_WORDS:
        return False

    word_texts = [w.get("word", "").strip().lower() for w in words if w.get("word", "").strip()]
    if not word_texts:
        return False

    # Count most common word
    from collections import Counter
    counts = Counter(word_texts)
    most_common_word, most_common_count = counts.most_common(1)[0]

    # Skip common words like "the", "a", "I" — they naturally repeat
    stopwords = {"the", "a", "an", "i", "and", "or", "to", "of", "in", "it",
                 "is", "on", "at", "by", "be", "as", "do", "go", "my", "we"}
    if most_common_word in stopwords:
        return False

    repeat_ratio = most_common_count / len(word_texts)
    if repeat_ratio < HALLUCINATION_REPEAT_RATIO:
        return False

    # Check if repeated words have suspiciously uniform short durations
    repeated_word_durations = [
        w.get("end", 0) - w.get("start", 0)
        for w in words
        if w.get("word", "").strip().lower() == most_common_word
    ]
    avg_duration = sum(repeated_word_durations) / len(repeated_word_durations) if repeated_word_durations else 0

    if avg_duration < 0.2:  # Less than 200ms per occurrence
        logger.warning(
            f"[lyric_processor] Hallucination detected: '{most_common_word}' "
            f"repeated {most_common_count}/{len(word_texts)} times, "
            f"avg_duration={avg_duration:.3f}s"
        )
        return True

    return False


# ---------------------------------------------------------------------------
# Conservative spelling correction
# ---------------------------------------------------------------------------

def _correct_word(word_text: str, probability: float) -> Tuple[str, bool]:
    """
    Apply conservative spelling correction to a single word.

    Returns (corrected_word, was_changed).

    Rules:
      - Only correct from the explicit _SPELLING_CORRECTIONS dictionary.
      - Only correct if word probability > 0.5 (if we are uncertain about
        what was said, we should not correct it — uncertainty is preserved).
      - Preserve case: if original was capitalized, capitalize the correction.
      - Never correct words with apostrophes (contractions / slang).
      - Never correct ALL-CAPS words (likely emphasis).
    """
    if not word_text or not word_text.strip():
        return word_text, False

    # Don't correct uncertain words — preserve uncertainty
    if probability < 0.5:
        return word_text, False

    stripped = word_text.strip()

    # Don't touch words with apostrophes (contractions, possessives)
    if "'" in stripped or "'" in stripped:
        return word_text, False

    # Don't touch ALL-CAPS (deliberate emphasis)
    if stripped.upper() == stripped and len(stripped) > 1:
        return word_text, False

    lookup_key = stripped.lower()
    correction = _SPELLING_CORRECTIONS.get(lookup_key)

    if correction is None:
        return word_text, False

    # Preserve original case
    if stripped[0].isupper():
        correction = correction.capitalize()

    # Preserve surrounding punctuation/spaces
    result = word_text.replace(stripped, correction)
    return result, True


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------

def process_transcription(
    transcription_data: Dict[str, Any],
    max_correction_ratio: float = MAX_ALLOWED_CORRECTION_RATIO,
) -> Dict[str, Any]:
    """
    Apply conservative post-processing to a Whisper transcription JSON.

    Args:
        transcription_data: The parsed JSON from Faster-Whisper (as dict).
        max_correction_ratio: If more than this fraction of words are changed,
                              the correction is rejected and original is kept.

    Returns:
        Processed transcription dict in the same format as input.
        Adds a "processing_report" key with statistics.
    """
    import copy
    processed = copy.deepcopy(transcription_data)
    segments = processed.get("segments", [])

    total_words = 0
    corrected_words = 0
    dropped_segments = 0
    flagged_words = 0
    hallucination_segments = 0

    filtered_segments = []

    for segment in segments:
        seg_no_speech = segment.get("no_speech_prob", 0.0) or 0.0
        seg_avg_logprob = segment.get("avg_logprob", 0.0) or 0.0

        # ── 1. Drop confirmed non-speech segments ─────────────────────────
        if seg_no_speech > SEGMENT_NO_SPEECH_THRESHOLD:
            logger.info(
                f"[lyric_processor] Dropping segment [{segment.get('start', 0):.1f}s] "
                f"— no_speech_prob={seg_no_speech:.2f} > {SEGMENT_NO_SPEECH_THRESHOLD}"
            )
            dropped_segments += 1
            continue

        words = segment.get("words", [])

        # ── 2. Detect repetition hallucinations ───────────────────────────
        if _detect_repetition_hallucination(words):
            logger.warning(
                f"[lyric_processor] Dropping hallucination segment "
                f"[{segment.get('start', 0):.1f}s-{segment.get('end', 0):.1f}s]: "
                f"'{segment.get('text', '')[:50]}'"
            )
            hallucination_segments += 1
            continue

        # ── 3. Process words ──────────────────────────────────────────────
        processed_words = []
        segment_corrections = 0

        for word in words:
            total_words += 1
            word_text = word.get("word", "")
            probability = word.get("probability", 1.0)

            # Flag low-confidence words (do NOT remove them — uncertainty is preserved)
            if probability < WORD_LOW_CONFIDENCE_THRESHOLD:
                word["uncertain"] = True
                flagged_words += 1
                logger.debug(
                    f"[lyric_processor] Low-confidence word: '{word_text}' "
                    f"prob={probability:.2f}"
                )
                processed_words.append(word)
                continue

            # Apply conservative spelling correction
            corrected_text, was_corrected = _correct_word(word_text, probability)
            if was_corrected:
                logger.info(
                    f"[lyric_processor] Spelling correction: '{word_text}' → '{corrected_text}' "
                    f"(prob={probability:.2f})"
                )
                word["word"] = corrected_text
                word["original_word"] = word_text  # Keep original for debugging
                corrected_words += 1
                segment_corrections += 1

            processed_words.append(word)

        # ── 4. Rebuild segment text from processed words ──────────────────
        if processed_words:
            segment["words"] = processed_words
            segment["text"] = "".join(w.get("word", "") for w in processed_words).strip()
            filtered_segments.append(segment)
        elif segment.get("text", "").strip():
            # Keep segments without word-level data but with text
            filtered_segments.append(segment)

    # ── 5. Validate: reject if too many words were changed ─────────────────
    correction_ratio = corrected_words / total_words if total_words > 0 else 0.0
    if correction_ratio > max_correction_ratio:
        logger.warning(
            f"[lyric_processor] ⚠ Correction ratio {correction_ratio:.1%} exceeds "
            f"threshold {max_correction_ratio:.1%}. Reverting to original transcription."
        )
        # Revert — return original data with report only
        transcription_data["processing_report"] = {
            "reverted": True,
            "reason": f"Correction ratio {correction_ratio:.1%} exceeded {max_correction_ratio:.1%}",
            "total_words": total_words,
            "corrected_words": corrected_words,
            "dropped_segments": dropped_segments,
            "hallucination_segments": hallucination_segments,
            "flagged_words": flagged_words,
        }
        return transcription_data

    # ── 6. Return processed data ───────────────────────────────────────────
    processed["segments"] = filtered_segments
    processed["processing_report"] = {
        "reverted": False,
        "total_words": total_words,
        "corrected_words": corrected_words,
        "correction_ratio": round(correction_ratio, 4),
        "dropped_segments": dropped_segments,
        "hallucination_segments": hallucination_segments,
        "flagged_words": flagged_words,
        "flagged_ratio": round(flagged_words / total_words, 4) if total_words > 0 else 0,
    }

    logger.info(
        f"[lyric_processor] Processing complete: "
        f"total_words={total_words} corrected={corrected_words} "
        f"dropped_segments={dropped_segments} hallucinations={hallucination_segments} "
        f"flagged_uncertain={flagged_words}"
    )
    return processed


def process_transcription_file(
    json_path: str,
    output_path: Optional[str] = None,
) -> str:
    """
    Loads a Whisper transcription JSON, processes it, and saves the result.

    Args:
        json_path: Path to the Whisper transcription JSON file.
        output_path: Where to save the processed JSON. Defaults to
                     <name>_processed.json next to the input.

    Returns:
        Path to the processed JSON file.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Transcription file not found: {json_path}")

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    processed = process_transcription(data)

    if output_path is None:
        base, ext = os.path.splitext(json_path)
        output_path = f"{base}_processed{ext}"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed, f, indent=2, ensure_ascii=False)

    report = processed.get("processing_report", {})
    logger.info(
        f"[lyric_processor] Saved processed transcription to {output_path} "
        f"| report={report}"
    )
    return output_path
