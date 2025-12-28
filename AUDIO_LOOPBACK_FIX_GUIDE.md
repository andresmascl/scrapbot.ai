# PulseAudio Loopback Fix Guide

This guide will help you diagnose and fix the audio loopback issue where your speakers route audio back to your microphone.

## Understanding the Problem

Your system is capturing speaker output and feeding it back to the microphone. This causes the wake word detector to hear its own TTS responses with 99.9% confidence.

---

## Step 1: Diagnose - List Your Audio Devices

### Check PulseAudio Sources (Microphones)

```bash
pactl list sources short
```

**Look for:**
- Lines ending in `.monitor` - these capture speaker output
- Your actual microphone (usually `alsa_input.*` or `usb-*`)

Example output:
```
0   alsa_output.pci-0000_00_1f.3.analog-stereo.monitor   ...  # MONITOR - captures speakers
1   alsa_input.pci-0000_00_1f.3.analog-stereo            ...  # YOUR MIC - what you want
```

### Check What Docker Container Sees

```bash
# Start the container
make run

# In another terminal, check what sources the container sees
docker exec scrapbot-ai pactl list sources short
```

### Check ALSA Devices

```bash
# List all recording devices
arecord -l

# Check mixer controls
amixer
```

---

## Step 2: Solutions

### Solution 1: Fix Default PulseAudio Source (RECOMMENDED)

Check if your default source is a monitor:

```bash
pactl info | grep "Default Source"
```

If it shows a `.monitor`, change it to your actual microphone:

```bash
# List sources to find your mic name
pactl list sources short

# Set your actual microphone as default (replace SOURCE_NAME)
pactl set-default-source alsa_input.pci-0000_00_1f.3.analog-stereo

# Make it permanent
echo "set-default-source alsa_input.pci-0000_00_1f.3.analog-stereo" >> ~/.config/pulse/default.pa
```

---

### Solution 2: Check ALSA Mixer for Loopback Controls

Some sound cards have hardware loopback controls:

```bash
# Open interactive mixer
alsamixer
```

**In alsamixer:**
1. Press `F4` - Show capture devices
2. Press `F5` - Show all controls
3. Look for these controls and MUTE them (press `M`):
   - "Loopback"
   - "Mix"
   - "Stereo Mix"
   - "What U Hear"
   - "Monitor"
4. Press `Esc` to exit

Save the settings:
```bash
sudo alsactl store
```

---

### Solution 3: Specify Exact Microphone in PyAudio

Modify the code to use a specific device instead of default.

**First, find your device index:**

```bash
# While container is running, exec into it
docker exec -it scrapbot-ai python3 -c "
import pyaudio
p = pyaudio.PyAudio()
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if info['maxInputChannels'] > 0:
        print(f'{i}: {info[\"name\"]} (inputs: {info[\"maxInputChannels\"]})')
"
```

This will show something like:
```
0: pulse (inputs: 32)
1: default (inputs: 32)
2: USB Microphone (inputs: 1)
```

**Then modify main.py to use specific device:**

Find where PyAudio stream is opened (search for `p.open(`) and add:
```python
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=native_rate,
    input=True,
    input_device_index=2,  # <-- ADD THIS - use index from list above
    frames_per_buffer=READ_CHUNK_SIZE,
)
```

---

### Solution 4: PulseAudio Volume Control GUI (Easiest for Testing)

Install and use pavucontrol (PulseAudio Volume Control):

```bash
sudo apt install pavucontrol  # or your distro's package manager
pavucontrol
```

**In pavucontrol:**
1. Go to "Recording" tab
2. While scrapbot is running, you'll see it recording
3. Click the dropdown next to it
4. Select your actual microphone (NOT "Monitor of...")
5. Go to "Input Devices" tab
6. Make sure your microphone is not muted and has good volume

---

### Solution 5: Disable Monitor Sources Entirely

If you don't need to record desktop audio:

```bash
# Edit PulseAudio config
nano ~/.config/pulse/default.pa

# Add this line at the end:
unload-module module-remap-source

# Restart PulseAudio
pulseaudio -k
pulseaudio --start
```

---

## Step 3: Verify the Fix

### Test 1: Record and Check

```bash
# Record 5 seconds while playing audio through speakers
arecord -d 5 -f cd test.wav

# Play it back - you should NOT hear the speaker audio
aplay test.wav

# Clean up
rm test.wav
```

### Test 2: Check with scrapbot

```bash
make run
```

Say the wake word once. You should:
- ✅ See wake word detection for your voice
- ✅ See TTS response play
- ✅ See the 8-second delay
- ❌ NOT see wake word detection after the delay (unless you say it again)

---

## Still Having Issues?

### Check for Hardware Loopback

Some USB audio interfaces have hardware monitoring that routes speakers to mic:

1. Check if your device has a "Direct Monitor" switch - turn it OFF
2. Check manufacturer software/drivers
3. Try a different microphone to isolate the issue

### Advanced: Check PulseAudio Module Configuration

```bash
# See all loaded modules
pactl list modules short

# Look for suspicious modules:
# - module-loopback
# - module-echo-cancel (if misconfigured)

# Unload problematic modules (replace MODULE_ID with actual ID)
pactl unload-module MODULE_ID
```

### Last Resort: Restart PulseAudio

```bash
pulseaudio -k
pulseaudio --start
```

---

## Summary of Quick Fixes to Try First

```bash
# 1. Install pavucontrol if you don't have it
sudo apt install pavucontrol

# 2. Run it
pavucontrol

# 3. Start scrapbot in another terminal
make run

# 4. In pavucontrol, go to "Recording" tab, select your actual microphone for scrapbot

# 5. Test by saying the wake word once
```

This should fix the majority of loopback issues!
