#!/usr/bin/env python3
"""Prepare a photo for ASCII conversion.

Usage: python scripts/prep_photo.py source-photo.jpg [left,top,right,bottom]
The optional box crops the photo first, in pixels of the original image.

1. Remove the background with rembg (u2net, about 170 MB, downloaded on first run).
2. Lift local contrast with CLAHE so a flat face gets real highlights and shadows.
3. Composite onto black, because the portrait prints light glyphs on a dark panel:
   black maps to blank space, bright skin maps to dense glyphs.

Writes source-prepped.png (grayscale).
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageOps
from rembg import new_session, remove

MAX_SIDE = 1200
GAMMA = 0.7  # below 1 lifts dark hair and clothes so they still print on the dark panel


def main() -> None:
    if len(sys.argv) not in (2, 3):
        sys.exit("usage: prep_photo.py <photo> [left,top,right,bottom]")

    img = ImageOps.exif_transpose(Image.open(sys.argv[1])).convert("RGB")
    if len(sys.argv) == 3:
        img = img.crop(tuple(int(v) for v in sys.argv[2].split(",")))
    # Upscale small crops too, so the background removal has enough detail to work with.
    scale = MAX_SIDE / max(img.size)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)

    alpha = np.asarray(remove(img, session=new_session("u2net")).convert("RGBA"))[:, :, 3].astype(np.float32) / 255.0
    gray = np.asarray(img.convert("L"))

    # Stretch using subject pixels only, so a bright background cannot skew the range.
    subject = gray[alpha > 0.5]
    if subject.size == 0:
        sys.exit("no subject found in the photo")
    lo, hi = np.percentile(subject, (1, 99))
    stretched = np.clip((gray.astype(np.float32) - lo) * 255.0 / max(hi - lo, 1), 0, 255).astype(np.uint8)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    boosted = clahe.apply(stretched).astype(np.float32)
    boosted = 255.0 * (boosted / 255.0) ** GAMMA

    out = (boosted * alpha).astype(np.uint8)

    # Crop to the subject with a small margin.
    ys, xs = np.where(alpha > 0.5)
    pad = int(0.04 * max(out.shape))
    top, bottom = max(ys.min() - pad, 0), min(ys.max() + pad, out.shape[0])
    left, right = max(xs.min() - pad, 0), min(xs.max() + pad, out.shape[1])

    Image.fromarray(out[top:bottom, left:right]).save("source-prepped.png")
    print("wrote source-prepped.png")


if __name__ == "__main__":
    main()
