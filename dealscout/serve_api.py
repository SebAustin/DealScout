#!/usr/bin/env python3
"""Start FastAPI — works when run from inside dealscout/."""
import sys
from pathlib import Path

# Parent of dealscout/ must be on path for `import dealscout`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "dealscout.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
