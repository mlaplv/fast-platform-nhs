import inspect
import importlib
import edge_tts
import edge_tts.communicate

file_path = inspect.getfile(edge_tts.communicate)
with open(file_path, "r") as f:
    content = f.read()

if "audio-24khz-48kbitrate-mono-mp3" in content:
    content = content.replace("audio-24khz-48kbitrate-mono-mp3", "webm-24khz-16bit-mono-opus")
    with open(file_path, "w") as f:
        f.write(content)
    importlib.reload(edge_tts.communicate)
    edge_tts.Communicate = edge_tts.communicate.Communicate
    print("PATCHED")
else:
    print("Already patched")

c = edge_tts.Communicate("test")
print("webm-24khz" in inspect.getsource(c.stream))
