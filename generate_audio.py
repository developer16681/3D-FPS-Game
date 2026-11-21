"""Procedural BGM Generator for Ursina FPS Arena Shooter.
Generates studio-quality cyberpunk / synthwave style music tracks using NumPy and wave:
- bgm.wav: Main battle theme (128 BPM, rolling bass, punchy drums, dark synth arpeggio)
- bgm_intense.wav: Intense combat / boss theme (140 BPM, distorted bass, furious 16th drums & lead)
- bgm_gameover.wav: Defeat stinger / drone (descending ominous minor chords)
- bgm_victory.wav: Victory fanfare (triumphant brass-like synth arpeggios & celebration beat)
"""
import math
import wave
from pathlib import Path
import numpy as np

SAMPLE_RATE = 44100

def create_enveloped_sine(freq, duration, env_type="exp", decay=5.0):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    sig = np.sin(2 * np.pi * freq * t)
    if env_type == "exp":
        env = np.exp(-decay * t)
    elif env_type == "linear":
        env = np.maximum(0, 1.0 - t / duration)
    return sig * env

def synth_kick(bpm, count, total_samples):
    out = np.zeros(total_samples, dtype=np.float32)
    beat_samples = int(SAMPLE_RATE * (60.0 / bpm))
    kick_dur = 0.35
    n_kick = int(SAMPLE_RATE * kick_dur)
    t = np.linspace(0, kick_dur, n_kick, endpoint=False)
    # Pitch envelope drops from 160Hz down to 42Hz
    freq_env = 42 + 120 * np.exp(-32 * t)
    phase = 2 * np.pi * np.cumsum(freq_env) / SAMPLE_RATE
    body = np.sin(phase) * np.exp(-9 * t)
    # Transient click
    click = (np.random.rand(n_kick) * 2 - 1) * np.exp(-120 * t) * 0.4
    kick = np.tanh((body + click) * 1.6) * 0.95
    for i in range(count):
        idx = i * beat_samples
        if idx + n_kick <= total_samples:
            out[idx:idx + n_kick] += kick
        else:
            rem = total_samples - idx
            out[idx:] += kick[:rem]
    return out

def synth_snare(bpm, count, total_samples, beats_offset=1):
    out = np.zeros(total_samples, dtype=np.float32)
    beat_samples = int(SAMPLE_RATE * (60.0 / bpm))
    snare_dur = 0.28
    n_snare = int(SAMPLE_RATE * snare_dur)
    t = np.linspace(0, snare_dur, n_snare, endpoint=False)
    # Tone component
    tone = np.sin(2 * np.pi * (185 - 60 * t) * t) * np.exp(-18 * t) * 0.6
    # Noise component
    noise = (np.random.rand(n_snare) * 2 - 1) * np.exp(-14 * t) * 0.7
    # Transient snap
    snap = (np.random.rand(n_snare) * 2 - 1) * np.exp(-90 * t) * 0.5
    snare = np.tanh(tone + noise + snap) * 0.75
    # Play on beats 2 and 4 (offset 1 beat, step 2 beats)
    for i in range(beats_offset, count, 2):
        idx = i * beat_samples
        if idx + n_snare <= total_samples:
            out[idx:idx + n_snare] += snare
        else:
            rem = total_samples - idx
            out[idx:] += snare[:rem]
    return out

def synth_hihats(bpm, total_samples, pattern="16th"):
    out = np.zeros(total_samples, dtype=np.float32)
    step_samples = int(SAMPLE_RATE * (60.0 / bpm) / 4) # 16th note
    steps = total_samples // step_samples
    hat_dur = 0.06
    n_hat = int(SAMPLE_RATE * hat_dur)
    t = np.linspace(0, hat_dur, n_hat, endpoint=False)
    # High frequency noise
    raw_noise = np.random.rand(n_hat) * 2 - 1
    # Simple high-pass diff
    hp_noise = np.diff(raw_noise, prepend=0)
    for s in range(steps):
        # Velocity groove: accents on upbeat 16ths
        accent = 0.5 if (s % 2 == 0) else 0.75
        if s % 4 == 2:
            accent = 0.85
        env = np.exp(-55 * t)
        hat = hp_noise * env * accent * 0.35
        idx = s * step_samples
        if idx + n_hat <= total_samples:
            out[idx:idx + n_hat] += hat
        else:
            rem = total_samples - idx
            out[idx:] += hat[:rem]
    return out

def synth_bassline(notes, bpm, total_samples, sidechain=True):
    out = np.zeros(total_samples, dtype=np.float32)
    step_samples = int(SAMPLE_RATE * (60.0 / bpm) / 4) # 16th note
    note_dur = (60.0 / bpm) / 4 * 0.88 # slight staccato
    n_note = int(SAMPLE_RATE * note_dur)
    t = np.linspace(0, note_dur, n_note, endpoint=False)

    for i, freq in enumerate(notes):
        if freq <= 0:
            continue
        idx = i * step_samples
        # Saw + sub octave sine
        saw = 2 * (t * freq - np.floor(0.5 + t * freq))
        saw2 = 2 * (t * (freq * 1.003) - np.floor(0.5 + t * (freq * 1.003)))
        sub = np.sin(2 * np.pi * (freq * 0.5) * t) * 0.7
        # Filter envelope
        filter_env = np.exp(-12 * t)
        tone = (saw + saw2) * (0.4 + 0.6 * filter_env) + sub
        amp_env = np.minimum(1.0, t * 150) * np.exp(-6 * t)
        note_snd = np.tanh(tone * amp_env * 1.3) * 0.6

        # Sidechain ducking on the beat (every 4 16ths)
        if sidechain and (i % 4 == 0):
            duck_len = min(n_note, int(SAMPLE_RATE * 0.12))
            duck_curve = np.linspace(0.15, 1.0, duck_len)
            note_snd[:duck_len] *= duck_curve

        if idx + n_note <= total_samples:
            out[idx:idx + n_note] += note_snd
        else:
            rem = total_samples - idx
            out[idx:] += note_snd[:rem]
    return out

def synth_arp(melody, bpm, total_samples):
    out_left = np.zeros(total_samples, dtype=np.float32)
    out_right = np.zeros(total_samples, dtype=np.float32)
    step_samples = int(SAMPLE_RATE * (60.0 / bpm) / 4)
    note_dur = (60.0 / bpm) / 4 * 1.2 # slight overlap for delay
    n_note = int(SAMPLE_RATE * note_dur)
    t = np.linspace(0, note_dur, n_note, endpoint=False)

    for i, freq in enumerate(melody):
        if freq <= 0:
            continue
        idx = i * step_samples
        # Pluck saw
        saw = 2 * (t * freq - np.floor(0.5 + t * freq))
        sq = np.sign(np.sin(2 * np.pi * freq * t)) * 0.3
        env = np.exp(-16 * t) * np.minimum(1.0, t * 200)
        snd = (saw + sq) * env * 0.35

        # Pan ping-pong
        pan = 0.5 + 0.35 * np.sin(i * 1.2)
        l_snd = snd * (1.0 - pan)
        r_snd = snd * pan

        if idx + n_note <= total_samples:
            out_left[idx:idx + n_note] += l_snd
            out_right[idx:idx + n_note] += r_snd
        else:
            rem = total_samples - idx
            out_left[idx:] += l_snd[:rem]
            out_right[idx:] += r_snd[:rem]
            # Wrap tail around to beginning for seamless looping!
            wrap = n_note - rem
            out_left[:wrap] += l_snd[rem:]
            out_right[:wrap] += r_snd[rem:]

    return out_left, out_right

def synth_pad(chords, bpm, total_samples):
    out_left = np.zeros(total_samples, dtype=np.float32)
    out_right = np.zeros(total_samples, dtype=np.float32)
    bar_samples = int(SAMPLE_RATE * (60.0 / bpm) * 4)

    for bar_idx, chord_freqs in enumerate(chords):
        idx = bar_idx * bar_samples
        dur = (60.0 / bpm) * 4.2 # slight overlap
        n_pad = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n_pad, endpoint=False)
        attack = int(SAMPLE_RATE * 0.4)
        release = int(SAMPLE_RATE * 0.5)
        env = np.ones(n_pad, dtype=np.float32)
        env[:attack] = np.linspace(0, 1, attack)
        env[-release:] = np.linspace(1, 0, release)

        sig_l = np.zeros(n_pad, dtype=np.float32)
        sig_r = np.zeros(n_pad, dtype=np.float32)
        for f in chord_freqs:
            # Warm detuned supersaw
            sig_l += np.sin(2 * np.pi * f * t) * 0.25
            sig_l += np.sin(2 * np.pi * (f * 1.004) * t) * 0.15
            sig_r += np.sin(2 * np.pi * (f * 0.996) * t) * 0.25
            sig_r += np.sin(2 * np.pi * (f * 1.008) * t) * 0.15

        chord_l = sig_l * env * 0.22
        chord_r = sig_r * env * 0.22

        if idx + n_pad <= total_samples:
            out_left[idx:idx + n_pad] += chord_l
            out_right[idx:idx + n_pad] += chord_r
        else:
            rem = total_samples - idx
            out_left[idx:] += chord_l[:rem]
            out_right[idx:] += chord_r[:rem]
            wrap = n_pad - rem
            out_left[:wrap] += chord_l[rem:]
            out_right[:wrap] += chord_r[rem:]

    return out_left, out_right

def make_seamless_loop(left, right, crossfade_samples=1000):
    """Smoothly aligns the audio boundary so the end connects to the start with zero click."""
    l = left.copy()
    r = right.copy()
    fade = np.linspace(0, 1, crossfade_samples, dtype=np.float32)
    l[-crossfade_samples:] = l[-crossfade_samples:] * (1.0 - fade) + l[0] * fade
    r[-crossfade_samples:] = r[-crossfade_samples:] * (1.0 - fade) + r[0] * fade
    return l, r

def write_stereo_wav(filepath, left, right, loop=False):
    if loop:
        left, right = make_seamless_loop(left, right)
    stereo = np.column_stack((left, right))
    # Normalize with headroom
    peak = np.max(np.abs(stereo))
    if peak > 0:
        stereo = stereo / peak * 0.90
    int_samples = (stereo * 32767).astype(np.int16)
    with wave.open(str(filepath), 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        wav_file.writeframes(int_samples.tobytes())
    print(f"Generated {filepath.name} ({len(stereo)/SAMPLE_RATE:.1f}s, {Path(filepath).stat().st_size} bytes)")

def m_to_f(midi_note):
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def build_bgm():
    """Builds standard combat BGM (128 BPM, D minor, 16 bars / 30s)."""
    bpm = 128
    bars = 16
    total_beats = bars * 4
    total_samples = int(total_beats * (60.0 / bpm) * SAMPLE_RATE)

    # Drums
    kick = synth_kick(bpm, total_beats, total_samples)
    snare = synth_snare(bpm, total_beats, total_samples)
    hats = synth_hihats(bpm, total_samples)

    # Chord progression (D minor, Bb major, F major, C major) - 4 bars each, repeated twice
    # MIDI: D=62, F=65, A=69 ; Bb=58, D=62, F=65 ; F=53, A=57, C=60 ; C=60, E=64, G=67
    chords_4bars = [
        [m_to_f(50), m_to_f(57), m_to_f(62)], # Dm
        [m_to_f(46), m_to_f(53), m_to_f(58)], # Bb
        [m_to_f(48), m_to_f(55), m_to_f(60)], # C
        [m_to_f(45), m_to_f(52), m_to_f(57)], # Am
    ] * 4 # 16 bars

    pad_l, pad_r = synth_pad(chords_4bars, bpm, total_samples)

    # Bassline notes (16th notes): D, Bb, C, A roots
    root_midis = [38, 34, 36, 33] * 4 # bars 1-16
    bass_notes = []
    for root in root_midis:
        # 16 notes per bar (rolling 16ths with octave bounce)
        bar_pattern = [root, root, root + 12, root, root, root + 12, root, root,
                       root, root, root + 12, root, root, root + 7, root + 10, root + 12]
        bass_notes.extend([m_to_f(n) for n in bar_pattern])

    bass = synth_bassline(bass_notes, bpm, total_samples, sidechain=True)

    # Arpeggio (driving melodic sequence in D minor)
    arp_notes = []
    arp_scales = [
        [62, 65, 69, 74, 69, 65, 69, 72], # Dm arp
        [58, 62, 65, 70, 65, 62, 65, 69], # Bb arp
        [60, 64, 67, 72, 67, 64, 67, 70], # C arp
        [57, 60, 64, 69, 64, 60, 64, 67], # Am arp
    ] * 4
    for chord in arp_scales:
        arp_notes.extend([m_to_f(n) for n in chord * 2]) # 16 notes per bar

    arp_l, arp_r = synth_arp(arp_notes, bpm, total_samples)

    # Mix
    drum_mix = kick * 0.9 + snare * 0.8 + hats * 0.55
    left = drum_mix + bass * 0.85 + pad_l * 0.45 + arp_l * 0.65
    right = drum_mix + bass * 0.85 + pad_r * 0.45 + arp_r * 0.65

    return left, right

def build_bgm_intense():
    """Builds intense combat / boss BGM (142 BPM, D Phrygian / Minor, fast heavy aggressive)."""
    bpm = 142
    bars = 16
    total_beats = bars * 4
    total_samples = int(total_beats * (60.0 / bpm) * SAMPLE_RATE)

    # Heavy double kick pattern
    kick = synth_kick(bpm, total_beats, total_samples)
    # Add off-beat 16th kick punch for intense metal/cyberpunk drive
    step_samples = int(SAMPLE_RATE * (60.0 / bpm) / 4)
    for s in range(bars * 16):
        if s % 16 in (6, 14): # Syncopated kicks
            k_hit = create_enveloped_sine(55, 0.25, decay=15)
            idx = s * step_samples
            if idx + len(k_hit) <= total_samples:
                kick[idx:idx + len(k_hit)] += k_hit * 0.7

    snare = synth_snare(bpm, total_beats, total_samples)
    hats = synth_hihats(bpm, total_samples)

    # Heavy distorted bassline
    root_midis = [38, 38, 39, 37] * 4 # D, D, Eb (Phrygian crunch), C#
    bass_notes = []
    for root in root_midis:
        bar_pattern = [root, root, root, root + 12, root, root, root + 12, root,
                       root, root, root + 1, root + 12, root, root + 7, root + 8, root + 12]
        bass_notes.extend([m_to_f(n) for n in bar_pattern])

    bass = synth_bassline(bass_notes, bpm, total_samples, sidechain=True) * 1.25

    # Rapid screaming arpeggios
    arp_notes = []
    for bar_idx in range(bars):
        root = [62, 62, 63, 61][bar_idx % 4]
        pattern = [root, root + 12, root + 15, root + 18, root + 17, root + 15, root + 12, root + 13,
                   root, root + 12, root + 15, root + 20, root + 18, root + 17, root + 15, root + 12]
        arp_notes.extend([m_to_f(n) for n in pattern])

    arp_l, arp_r = synth_arp(arp_notes, bpm, total_samples)

    drum_mix = kick * 1.0 + snare * 0.85 + hats * 0.65
    left = drum_mix + bass * 0.95 + arp_l * 0.8
    right = drum_mix + bass * 0.95 + arp_r * 0.8

    return left, right

def build_gameover():
    """Dark descending defeat stinger / theme (~5.5s)."""
    dur = 5.5
    total_samples = int(SAMPLE_RATE * dur)
    t = np.linspace(0, dur, total_samples, endpoint=False)

    # Sub-bass descending drop
    freq_drop = 65 * np.exp(-0.8 * t) + 25
    phase = 2 * np.pi * np.cumsum(freq_drop) / SAMPLE_RATE
    sub = np.sin(phase) * np.exp(-0.5 * t) * 0.8

    # Low melancholy chords: D minor descending to Bb minor
    chord_midis = [50, 53, 57, 62] # Dm
    drone = np.zeros(total_samples, dtype=np.float32)
    for m in chord_midis:
        f = m_to_f(m)
        drone += np.sin(2 * np.pi * f * t) * np.exp(-0.6 * t) * 0.25
        drone += np.sin(2 * np.pi * (f * 0.5) * t) * np.exp(-0.4 * t) * 0.35

    sig = np.tanh(sub + drone) * 0.85
    return sig, sig

def build_victory():
    """Triumphant victory fanfare with rising synth chords & energetic pulse (~7.0s)."""
    dur = 7.0
    total_samples = int(SAMPLE_RATE * dur)
    bpm = 132
    beats = int(dur * (bpm / 60.0))

    kick = synth_kick(bpm, beats, total_samples)
    snare = synth_snare(bpm, beats, total_samples)
    hats = synth_hihats(bpm, total_samples)

    # Ascending heroic chords (F major -> G major -> A major)
    # 4 beats of F, 4 beats of G, 8 beats of A
    fanfare_notes = [
        m_to_f(65), m_to_f(69), m_to_f(72), m_to_f(77), # F maj
        m_to_f(67), m_to_f(71), m_to_f(74), m_to_f(79), # G maj
        m_to_f(69), m_to_f(73), m_to_f(76), m_to_f(81), # A maj
    ]
    fanfare_l, fanfare_r = synth_arp(fanfare_notes * 4, bpm, total_samples)

    # Triumphant bass
    bass_notes = [m_to_f(41)] * 8 + [m_to_f(43)] * 8 + [m_to_f(45)] * 16
    bass = synth_bassline(bass_notes, bpm, total_samples, sidechain=True)

    fade_out = np.minimum(1.0, np.linspace(1.2, 0.0, total_samples))
    left = (kick * 0.8 + snare * 0.7 + hats * 0.5 + bass * 0.7 + fanfare_l * 0.8) * fade_out
    right = (kick * 0.8 + snare * 0.7 + hats * 0.5 + bass * 0.7 + fanfare_r * 0.8) * fade_out

    return left, right

def main():
    audio_dir = Path(__file__).resolve().parent / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    print("Generating bgm.wav...")
    l, r = build_bgm()
    write_stereo_wav(audio_dir / "bgm.wav", l, r, loop=True)

    print("Generating bgm_intense.wav...")
    l, r = build_bgm_intense()
    write_stereo_wav(audio_dir / "bgm_intense.wav", l, r, loop=True)

    print("Generating bgm_gameover.wav...")
    l, r = build_gameover()
    write_stereo_wav(audio_dir / "bgm_gameover.wav", l, r, loop=False)

    print("Generating bgm_victory.wav...")
    l, r = build_victory()
    write_stereo_wav(audio_dir / "bgm_victory.wav", l, r, loop=False)

    print("All audio files successfully generated!")

if __name__ == "__main__":
    main()
