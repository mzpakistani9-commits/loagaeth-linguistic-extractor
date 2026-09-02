# Vesuvius Frag1 ink-detection detector — reproducible container
#
# Vision-API (Claude) tile-based ink detection over a Herculaneum fragment
# surface volume. No GPU required: all inference happens in the cloud vision
# API, so this runs on any machine (developers without GPUs included).
#
# Build:  docker build -t vesuvius-ink-detector .
# Run:    docker run --rm \
#           -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
#           -v $PWD/Frag1:/data/Frag1:ro \
#           -v $PWD/out:/out \
#           vesuvius-ink-detector \
#             --max-tiles 64 --threshold 0.05
FROM python:3.11-slim

WORKDIR /app

# Detection runs on the CPU; only lightweight deps required.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY vesuvius_ink_detector.py .
COPY fuse_4layer.py .

# Mount the fragment data read-only at /data and outputs at /out.
ENV VESUVIUS_SCROLL=/data/Frag1/surface_volume/28.tif
ENV OUTPUT_DIR=/out

ENTRYPOINT ["python", "vesuvius_ink_detector.py"]
