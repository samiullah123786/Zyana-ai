# Render Setup for Voice Transcription

This guide configures Render to support faster-whisper voice transcription.

## Render Dashboard Configuration

### 1. Update Build Command

In your Render service settings:

**Build Command:**
```bash
bash render-build.sh
```

This script will:
- Install ffmpeg (required for audio processing)
- Install all Python dependencies from requirements.txt

### 2. Keep Start Command As Is

**Start Command** (no change needed):
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. Environment Variables

No new environment variables needed. Voice transcription uses existing config.

## What Happens on First Deploy

1. **Build Phase (~2-3 minutes):**
   - Installs ffmpeg
   - Downloads faster-whisper package
   - Installs other Python dependencies

2. **First Voice Message (~30 seconds):**
   - Downloads Whisper "base" model (74MB)
   - Model is cached for future requests
   - Subsequent transcriptions take 3-5 seconds

## Disk Usage

- Whisper model: 74MB
- ffmpeg: ~50MB
- Total added: ~125MB
- Render free tier: 512MB ✅ (plenty of space)

## Testing Voice Transcription

After deployment:

1. Send a voice message to your Telegram bot
2. Bot responds: "🎙️ Transcribing your voice message..."
3. Wait 5-30 seconds (first time is slower)
4. Bot processes the transcribed text as a regular message

**Example:**
- Send voice: "I lent Ahmad 10,000 rupees"
- Bot transcribes and responds: "✅ Recorded loan: PKR 10,000 to Ahmad..."

## Troubleshooting

### Error: "ffmpeg not found"

**Symptom:** Voice messages fail with FileNotFoundError

**Solution:** 
- Verify build command is set to `bash render-build.sh`
- Check Render build logs for "✅ System dependencies installed"
- Redeploy if needed

### Error: "Model download timeout"

**Symptom:** First voice message times out

**Solution:**
- This is normal on first use (downloads 74MB model)
- Just try again - model is now cached
- Subsequent requests will be fast

### Voice Transcription is Slow

**Normal Timing:**
- First message: 20-30 seconds (model download)
- Subsequent: 3-5 seconds per 10-second voice message

**If consistently slow:**
- Check Render instance size (upgrade if needed)
- Consider OpenAI Whisper API alternative

## Alternative: OpenAI Whisper API

If faster-whisper is problematic on Render, use OpenAI's API:

**Cost:** ~$0.006/minute of audio

**Implementation:**

1. Add OpenAI API key to Render environment:
   ```
   OPENAI_API_KEY=your_key_here
   ```

2. Update `backend/services/voice_transcriber.py`:
   ```python
   # Option: Use OpenAI Whisper API instead
   import openai
   
   async def transcribe_audio(self, audio_file_path: str):
       with open(audio_file_path, 'rb') as audio:
           transcript = openai.Audio.transcribe("whisper-1", audio)
       return transcript['text']
   ```

## Monitoring

Check Render logs for:
```
✅ System dependencies installed
✅ Python dependencies installed
Loading Whisper model: base
Whisper model loaded successfully
Transcribed voice message: [text]
```

## Success Checklist

- [ ] `render-build.sh` created in project root
- [ ] Render build command updated to `bash render-build.sh`
- [ ] Deployed successfully (check build logs)
- [ ] Sent test voice message
- [ ] Bot transcribed and processed message
- [ ] Subsequent voice messages are fast

## Notes

- ffmpeg is only needed on the server (Render), not locally for development
- Model downloads once per deployment
- Voice transcription works in any language Whisper supports
- Default model: "base" (good balance of speed/accuracy)
- Can upgrade to "small" or "medium" for better accuracy (edit voice_transcriber.py)

---

**Status:** Ready for deployment! Voice transcription will work on Render with this setup. 🎙️✅

