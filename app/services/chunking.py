import re
from typing import List

def split_into_chunks(text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
    """Simple, fast chunker: paragraph-aware, hard wrap to ~chunk_size with overlap."""
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: List[str] = []
    buf = ""
    for p in paras:
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= chunk_size:
            buf += "\n\n" + p
        else:
            chunks.append(buf)
            # start new with overlap tail
            tail = buf[-overlap:]
            buf = (tail + "\n\n" + p) if overlap > 0 else p
    if buf:
        chunks.append(buf)
    return chunks