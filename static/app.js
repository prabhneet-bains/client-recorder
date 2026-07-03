const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const finalizeBtn = document.getElementById('finalizeBtn');
const sessionIdText = document.getElementById('sessionId');
const chunkCountText = document.getElementById('chunkCount');
const statusText = document.getElementById('statusText');
const transcriptEl = document.getElementById('transcript');
const notesEl = document.getElementById('notes');
const downloadLink = document.getElementById('downloadJson');

let mediaRecorder;
let sessionId = crypto.randomUUID().slice(0, 8);
let chunkCounter = 0;
let savedResponse = null;

sessionIdText.textContent = sessionId;

function setStatus(message) {
  statusText.textContent = message;
}

function setButtons(recording) {
  startBtn.disabled = recording;
  stopBtn.disabled = !recording;
  finalizeBtn.disabled = recording || chunkCounter === 0;
}

async function sendChunk(chunkBlob) {
  const form = new FormData();
  form.append('session_id', sessionId);
  form.append('file', chunkBlob, `chunk_${sessionId}_${chunkCounter}.webm`);

  setStatus(`Uploading chunk ${chunkCounter + 1}...`);

  try {
    const response = await fetch('/append_chunk', {
      method: 'POST',
      body: form,
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    chunkCounter += 1;
    chunkCountText.textContent = chunkCounter;
    setStatus(`Chunk ${chunkCounter} uploaded.`);
  } catch (err) {
    console.error(err);
    setStatus(`Upload failed: ${err.message}`);
  }
}

startBtn.addEventListener('click', async () => {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    setStatus('Microphone access is not supported in this browser.');
    return;
  }

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

  mediaRecorder.addEventListener('dataavailable', async (event) => {
    if (event.data && event.data.size > 0) {
      await sendChunk(event.data);
    }
  });

  mediaRecorder.addEventListener('stop', () => {
    setStatus('Recording stopped. Ready to finalize.');
    setButtons(false);
  });

  mediaRecorder.start(30000);
  setStatus('Recording live session. Chunks will upload automatically every 30 seconds.');
  setButtons(true);
});

stopBtn.addEventListener('click', () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }
});

finalizeBtn.addEventListener('click', async () => {
  setStatus('Finalizing notes...');
  finalizeBtn.disabled = true;

  try {
    const form = new FormData();
    form.append('session_id', sessionId);

    const response = await fetch('/finalize_session', {
      method: 'POST',
      body: form,
    });

    if (!response.ok) {
      throw new Error(await response.text());
    }

    const data = await response.json();
    transcriptEl.textContent = data.transcript || 'No transcript returned.';
    notesEl.textContent = data.notes || 'No notes returned.';
    savedResponse = data;
    downloadLink.classList.remove('hidden');
    downloadLink.href = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }));
    setStatus('Finalization complete. Review the notes below.');
  } catch (err) {
    console.error(err);
    setStatus(`Finalization failed: ${err.message}`);
    finalizeBtn.disabled = false;
  }
});

setButtons(false);
