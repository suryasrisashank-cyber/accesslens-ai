"""Tests for Text-To-Speech engine."""

import pytest
from audio.text_to_speech import TextToSpeechEngine, tts_engine


def test_tts_initialization():
    engine = TextToSpeechEngine()
    assert engine is not None
    assert engine.is_speaking is False


def test_tts_rate_and_volume():
    engine = TextToSpeechEngine()
    engine.set_rate(3)
    assert engine._rate == 3

    # Clamping test
    engine.set_rate(15)
    assert engine._rate == 10

    engine.set_volume(85)
    assert engine._volume == 85

    engine.set_volume(150)
    assert engine._volume == 100


def test_tts_stop_when_idle():
    engine = TextToSpeechEngine()
    # Calling stop on idle engine should not throw
    engine.stop()
    assert engine.is_speaking is False
