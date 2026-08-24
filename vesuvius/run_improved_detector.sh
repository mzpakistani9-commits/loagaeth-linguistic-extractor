#!/bin/bash
# Improved ink detection - FIXED launcher (Aug 24)
# Fixes vs old version:
#   1. Sets VESUVIUS_SCROLL per layer (old bug: all layers silently ran layer 28)
#   2. cd to Desktop so outputs land in Desktop/results/ (OUTPUT_DIR is relative)
# REQUIREMENT: AgentRouter balance >= ~$10 (one 583-tile layer scan costs ~$9)

: "${ANTHROPIC_API_KEY:?Set ANTHROPIC_API_KEY first: export ANTHROPIC_API_KEY=sk-...}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://agentrouter.org/}"
export VESUVIUS_MODEL="${VESUVIUS_MODEL:-claude-opus-4-8}"

LAYERS="${LAYERS:-26}"          # default: only missing layer; override e.g. LAYERS="26 27"
RESULTS_DIR="/home/zubair/Desktop/results"
cd /home/zubair/Desktop || exit 1

echo "=== Improved Ink Detection v2 ==="
echo "Model: $VESUVIUS_MODEL via AgentRouter | Layers: $LAYERS"

for LAYER in $LAYERS; do
    echo "Starting layer ${LAYER} at $(date)"
    VESUVIUS_SCROLL="/home/zubair/Desktop/vesuvius_data/Frag1/surface_volume/${LAYER}.tif" \
      python3 /home/zubair/Desktop/vesuvius_ink_detector.py \
      --max-tiles 583 --threshold 0.05 \
      > "${RESULTS_DIR}/run_layer${LAYER}.log" 2>&1 &
    echo "  PID $! -> ${RESULTS_DIR}/run_layer${LAYER}.log"
done

echo "Monitor: tail -f ${RESULTS_DIR}/run_layer*.log"
