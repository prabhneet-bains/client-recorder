
import os
import time
import uuid
import queue
import threading
import sounddevice as sd
from scipy.io import wavfile
import numpy as np
import requests

# ==========================================
# CONFIGURATION
# ==========================================
PUBLIC_SERVER_URL = "https://impulse-perfume-afterlife.ngrok-free.dev" # Your Ngrok/Cloudflare URL
API_KEY = "jskjdbcskdcs987345873468"

APPEND_URL = f"{PUBLIC_SERVER_URL}/append_chunk"
FINALIZE_URL = f"{PUBLIC_SERVER_URL}/finalize_session"
HEADERS = {"X-API-KEY": API_KEY}

SAMPLE_RATE = 16000
CHUNK_DURATION = 30  # Send data every 30 seconds
CHANNELS = 1

audio_queue = queue.Queue()
session_id = str(uuid.uuid4())[:8] # Generate a short unique ID for this consultation

def upload_worker():
    """Background thread that handles uploading audio chunks to the server."""
    chunk_index = 0
    while True:
        item = audio_queue.get()
        if item is None: 
            break  # Signal to stop thread
            
        audio_chunk, idx = item
        temp_filename = f"client_chunk_{session_id}_{idx}.wav"
        wavfile.write(temp_filename, SAMPLE_RATE, audio_chunk)
        
        # Post the chunk over the internet natively
        try:
            with open(temp_filename, "rb") as f:
                res = requests.post(
                    APPEND_URL, 
                    files={"file": f}, 
                    data={"session_id": session_id}, 
                    headers=HEADERS, 
                    timeout=45
                )
            if res.status_code == 200:
                print(f" -> Background sync successful for chunk {idx}.")
            else:
                print(f" ⚠️ Sync failed for chunk {idx}: {res.text}")
        except Exception as e:
            print(f" ⚠️ Network connection issue on chunk {idx}: {e}")
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)
                
        audio_queue.task_done()

def record_session():
    print(f"\n=======================================================")
    print(f"   PHYSIO SCRIBE: REAL-TIME CHUNKING ACTIVE (ID: {session_id})")
    print(f"=======================================================")
    print(" Recording... Every 30s is automatically streamed to GPU Server.")
    print(" Press Ctrl+C when the consultation is completely finished.")
    print("=======================================================\n")
    
    # Start the background pipeline thread
    worker_thread = threading.Thread(target=upload_worker, daemon=True)
    worker_thread.start()
    
    recording_buffer = []
    chunk_idx = 0
    samples_per_chunk = SAMPLE_RATE * CHUNK_DURATION
    
    def callback(indata, frames, time_info, status):
        recording_buffer.append(indata.copy())
        
        # Check if we accumulated 30 seconds of audio data
        current_samples = sum(len(b) for b in recording_buffer)
        if current_samples >= samples_per_chunk:
            # Concatenate and slice exactly 30s
            full_block = np.concatenate(recording_buffer, axis=0)
            chunk_to_send = full_block[:samples_per_chunk]
            # Keep leftover samples for the next block
            recording_buffer.clear()
            if len(full_block) > samples_per_chunk:
                recording_buffer.append(full_block[samples_per_chunk:])
                
            # Throw the block to the background worker to deal with upload
            nonlocal chunk_idx
            audio_queue.put((chunk_to_send, chunk_idx))
            chunk_idx += 1

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=callback):
            while True:
                sd.sleep(1000)
    except KeyboardInterrupt:
        print("\n\n🛑 Consultation stopped. Compiling final remaining seconds...")
        
        # Flush whatever audio was left inside the buffer at the end
        if recording_buffer:
            final_block = np.concatenate(recording_buffer, axis=0)
            audio_queue.put((final_block, chunk_idx))
            
    # Wait for the background queue to completely finish uploading remaining pieces
    print("⌛ Waiting for final background sync packets to settle...")
    audio_queue.join()
    audio_queue.put(None) # Kill worker
    worker_thread.join()
    
    # Request finalization and SOAP note generation
    print("📡 Requesting Final AI SOAP Note formulation...")
    try:
        res = requests.post(FINALIZE_URL, data={"session_id": session_id}, headers=HEADERS, timeout=120)
        if res.status_code == 200:
            data = res.json()
            print("\n=======================================================")
            print("📋 FINAL GENERATED CLINICAL SOAP NOTES")
            print("=======================================================")
            print(data.get('notes'))
            print("=======================================================\n")
        else:
            print(f"❌ Error during note finalization: {res.text}")
    except Exception as e:
        print(f"❌ Connection broken at finalization stage: {e}")

if __name__ == "__main__":
    record_session()