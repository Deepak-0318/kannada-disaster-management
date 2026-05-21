"""Test TTS functionality"""
import asyncio
import edge_tts
import os

async def test_tts():
    text = "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ ಎತ್ತರ ಪ್ರದೇಶಕ್ಕೆ ಹೋಗಬೇಕು"
    output_path = "test_tts_output.mp3"
    
    print(f"Testing TTS with text: {text}")
    print(f"Output file: {output_path}")
    
    try:
        communicate = edge_tts.Communicate(
            text,
            voice="kn-IN-SapnaNeural"
        )
        await communicate.save(output_path)
        
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"✅ TTS Success! File created: {output_path} ({file_size} bytes)")
        else:
            print("❌ TTS Failed: File not created")
            
    except Exception as e:
        print(f"❌ TTS Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tts())
