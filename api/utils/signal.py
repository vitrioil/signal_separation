class AudioExtension:

    def read_mp3(stream: bytes):
        pass

    def read_wav(stream: bytes):
        pass

    def read_flac(stream: bytes):
        pass

    def read_m4a(stream: bytes):
        pass


def read_audio(stream: bytes, extension: str):
    if extension.endswith("mp3"):
        AudioExtension.read_mp3(stream)
    elif extension.endswith("wav"):
        AudioExtension.read_wav(stream)
    elif extension.endswith("wav"):
        AudioExtension.read_wav(stream)
    elif extension.endswith("flac"):
        AudioExtension.read_flac(stream)
    else:
        return
