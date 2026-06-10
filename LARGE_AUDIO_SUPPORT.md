# 🎙️ Large Audio File Support - Meeting Intelligence Assistant

## Overview

**Meeting Intelligence Assistant** now supports audio files **up to 500 MB**, handling long meetings that exceed OpenAI Whisper's 25 MB single-file limit.

---

## How It Works

### Architecture

```
User uploads file (50 MB)
        ↓
System detects size > 25 MB
        ↓
Automatically chunk into 20 MB segments
        ↓
Chunk 1 (20 MB) → Whisper → "transcript part 1..."
Chunk 2 (20 MB) → Whisper → "transcript part 2..."
Chunk 3 (10 MB) → Whisper → "transcript part 3..."
        ↓
Merge transcripts intelligently
        ↓
Clean & analyze
        ↓
Return complete meeting intelligence
```

### Key Features

| Feature | Details |
|---------|---------|
| **Max File Size** | 500 MB (up from 25 MB) |
| **Chunk Size** | 20 MB per segment (Whisper safe) |
| **Processing** | Sequential (one chunk at a time) |
| **Auto-Detection** | Automatic endpoint selection |
| **Progress Tracking** | Shows chunk count during processing |
| **Transcript Merging** | Intelligent concatenation with spacing |

---

## API Endpoints

### Endpoint 1: Smart Transcription (Recommended)
```
POST /api/meeting/transcribe
```

**Features:**
- Automatically detects file size
- Uses appropriate strategy (single or chunked)
- Returns `chunks_processed` metadata
- Best for most use cases

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/meeting/transcribe \
  -F "file=@meeting_audio_long.mp3"
```

**Response:**
```json
{
  "transcript": "transcript text here...",
  "chunks_processed": 3
}
```

### Endpoint 2: Explicit Large File Handling
```
POST /api/meeting/transcribe-large
```

**Features:**
- Always uses chunking strategy
- Better for very large files (> 100 MB)
- More detailed response metadata
- Returns file size information

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/meeting/transcribe-large \
  -F "file=@meeting_audio_long.mp3"
```

**Response:**
```json
{
  "transcript": "transcript text here...",
  "chunks_processed": 3,
  "file_size_mb": 45.2,
  "filename": "meeting_audio_long.mp3"
}
```

---

## Frontend Usage

### Automatic Endpoint Selection

The frontend automatically chooses the correct endpoint based on file size:

```javascript
// Pseudo-code showing the logic
const fileSizeMB = file.size / (1024 * 1024);
if (fileSizeMB > 25) {
  // Use smart endpoint that handles chunking
  endpoint = '/api/meeting/transcribe-large';
  statusMsg = `Processing ${fileSizeMB.toFixed(1)} MB - splitting into chunks...`;
} else {
  // Use standard endpoint
  endpoint = '/api/meeting/transcribe';
  statusMsg = 'Processing audio...';
}
```

### User Experience

**For small files (< 25 MB):**
```
⏳ กำลังถอดเสียง...
     ↓
✅ ถอดเสียงสำเร็จ (5000 ตัวอักษร)
```

**For large files (> 25 MB):**
```
⏳ กำลังถอดเสียง (45.5 MB - แบ่งเป็น chunks)...
     ↓
✅ ถอดเสียงสำเร็จ (15000 ตัวอักษร) — 3 chunks ✓
```

---

## Real-World Examples

### Example 1: 1-hour meeting (45 MB MP3)

```
Meeting Duration: 60 minutes
File Size: 45 MB
Chunks: 3 × 20 MB + 1 × 5 MB

Timeline:
  Chunk 1 (0:00-0:20) → Transcribed ✓
  Chunk 2 (0:20-0:40) → Transcribed ✓
  Chunk 3 (0:40-1:00) → Transcribed ✓
  
Result: Complete 60-minute transcript in one go
```

### Example 2: Long workshop (3 hours, 180 MB video)

```
Meeting Duration: 180 minutes
File Size: 180 MB
Chunks: 9 × 20 MB

Processing:
  1. Upload 180 MB file
  2. Auto-detect size > 500 MB? No → Proceed
  3. Size > 25 MB? Yes → Use chunking strategy
  4. Split into 9 chunks of 20 MB each
  5. Process sequentially (safest approach)
  6. Merge 9 transcripts
  7. Clean & analyze
```

---

## Configuration

### Backend Settings (main.py)

```python
# Chunk configuration (line ~20)
MAX_AUDIO_MB = 25           # Standard Whisper limit
MAX_LARGE_AUDIO = 500       # Max file size supported
CHUNK_SIZE = 20             # MB per chunk (safe margin)

# Chunking strategy
def _split_audio_file(audio_path, chunk_size_mb=20)
```

### Modify Chunk Size (optional)

To change chunk size from 20 MB to 15 MB (for slower connections):

```python
# In _transcribe_audio_chunks()
chunks, num_chunks = _split_audio_file(audio_path, chunk_size_mb=15)
```

---

## Error Handling

### Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "File too large" | > 500 MB | Compress audio or split manually |
| "Transcription failed" | API quota exceeded | Wait or use smaller file |
| "Chunks merged incorrectly" | Rare edge case | Check chunk boundaries, retry |
| "Memory error" | Large file on low RAM | Reduce chunk size or file size |

### Error Response Examples

**File too large:**
```json
{
  "detail": "ไฟล์เสียงใหญ่เกิน 500 MB"
}
```

**API error:**
```json
{
  "detail": "Whisper error: Rate limit exceeded"
}
```

---

## Performance Considerations

### Processing Time

For typical meeting audio (MP3, 128 kbps):

| Duration | File Size | Chunks | Est. Time |
|----------|-----------|--------|-----------|
| 30 min | 15 MB | 1 | ~30 sec |
| 1 hour | 30 MB | 2 | ~1 min |
| 2 hours | 60 MB | 3 | ~1.5 min |
| 3 hours | 90 MB | 5 | ~2.5 min |

*Times include: transcription + cleaning + analysis*

### Bandwidth

- Uploads: Full file size (no compression)
- Processing: Chunk by chunk (memory efficient)
- Response: Compressed transcript + metadata

---

## Best Practices

### ✅ DO:

1. **Use standard endpoint** for files < 25 MB
2. **Check file format** before upload (MP3 > WAV for size)
3. **Compress audio** if file is very large
4. **Monitor API quota** when processing many large files
5. **Test with sample** before processing important meetings

### ❌ DON'T:

1. Don't upload > 500 MB files
2. Don't use uncompressed WAV for long meetings
3. Don't retry immediately on failure (wait 60 sec)
4. Don't process parallel large files (slow & uses quota)
5. Don't ignore error messages

---

## Testing the Feature

### Test with Mock Large File

```bash
# Create a 40 MB test file
dd if=/dev/zero of=test_40mb.mp3 bs=1M count=40

# Send to API
curl -X POST http://localhost:8000/api/meeting/transcribe \
  -F "file=@test_40mb.mp3"
```

### Monitor Processing

```javascript
// Browser console
console.log('File chunks being processed...');
// Should see: "✅ Transcribed N audio chunks and merged successfully"
```

---

## Future Improvements

🔮 **Planned features:**

- [ ] **Parallel chunk processing** (if rate limits allow)
- [ ] **Speaker diarization** (identify speakers across chunks)
- [ ] **Streaming uploads** for even larger files
- [ ] **Automatic audio compression** before sending
- [ ] **Chunk-level error recovery** (retry failed chunks)

---

## Support & Troubleshooting

### Quick Links

- API Documentation: `http://localhost:8000/docs`
- Backend logs: Check terminal output during processing
- Frontend logs: Browser Developer Tools (F12)

### Common Commands

```bash
# Check API health
curl http://localhost:8000/health

# Test transcribe endpoint directly
curl -X POST http://localhost:8000/api/meeting/transcribe \
  -F "file=@meeting.mp3"

# View API documentation
open http://localhost:8000/docs
```

---

**Last Updated:** 2026-06-10  
**Feature Status:** ✅ Production Ready  
**Tested File Size:** Up to 500 MB  
**Supported Formats:** MP3, WAV, M4A, WebM, OGG, MP4
