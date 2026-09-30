#!/bin/bash
set -e

OUT_BASE="${1:-$HOME/diff_ws/src/diff_robot/maps/my_map}"

ros2 run nav2_map_server map_saver_cli -f "$OUT_BASE"

echo "地图已保存: ${OUT_BASE}.pgm / ${OUT_BASE}.yaml"
