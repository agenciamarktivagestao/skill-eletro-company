"""Grava sequências de quadros PIL direto num arquivo de vídeo via ffmpeg."""
import os
import subprocess

from brand import W, H, FPS


class FrameWriter:
    """alpha=False → MP4 H.264 (telas opacas); alpha=True → MOV PNG (sobreposições)."""

    def __init__(self, path, alpha=False, size=(W, H), fps=FPS):
        self.path = path
        self.alpha = alpha
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        pix = "rgba" if alpha else "rgb24"
        codec = ["-c:v", "png", "-pix_fmt", "rgba"] if alpha else \
            ["-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd,format=yuv420p",
             "-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p",
             "-color_range", "tv", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", pix,
               "-s", f"{size[0]}x{size[1]}", "-r", str(fps), "-i", "-", *codec, path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        self.n = 0

    def write(self, im):
        im = im.convert("RGBA" if self.alpha else "RGB")
        self.p.stdin.write(im.tobytes())
        self.n += 1

    def close(self):
        self.p.stdin.close()
        if self.p.wait() != 0:
            raise RuntimeError(f"ffmpeg falhou ao gravar {self.path}")
        return self.n
