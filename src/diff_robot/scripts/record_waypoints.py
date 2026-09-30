#!/usr/bin/env python3
import argparse
import math
import os

import rclpy
import yaml
from geometry_msgs.msg import PointStamped, PoseStamped
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy


def quat_to_yaw(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z))


ZONE_START_POSE = (3.27, 1.35, 180.0)


class WaypointRecorder(Node):
    def __init__(self, out_file, overwrite, end_at_start):
        super().__init__('waypoint_recorder')
        self.out_file = out_file
        self.end_at_start = end_at_start
        self.waypoints = []
        if not overwrite:
            try:
                with open(out_file) as f:
                    data = yaml.safe_load(f) or {}
                self.waypoints = data.get('waypoints', [])
            except FileNotFoundError:
                pass
        self._save()
        qos = QoSProfile(
            depth=10,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.BEST_EFFORT)
        self.create_subscription(PoseStamped, '/goal_pose', self.on_goal, qos)
        self.create_subscription(
            PoseStamped, '/move_base_simple/goal', self.on_goal, qos)
        self.create_subscription(
            PointStamped, '/clicked_point', self.on_point, qos)
        self.get_logger().info(
            f'在 RViz 里点击记录目标点（Nav2 Goal / 2D Goal Pose / Publish Point 都支持，'
            f'当前已记录 {len(self.waypoints)} 个）')
        self.get_logger().info(f'记录文件: {self.out_file}')

    def finish(self):
        if not self.end_at_start or not self.waypoints:
            return
        last = self.waypoints[-1]
        sx, sy, syaw = ZONE_START_POSE
        if (abs(last['x'] - sx) < 1e-3 and abs(last['y'] - sy) < 1e-3
                and abs(last['yaw'] - syaw) < 0.5):
            return
        self._append(sx, sy, syaw, 'auto')
        print(f'已自动把起始位姿追加为最后一个点: x={sx} y={sy} yaw={syaw}')

    def _save(self):
        with open(self.out_file, 'w') as f:
            yaml.safe_dump({'waypoints': self.waypoints}, f, sort_keys=False)

    def _append(self, x, y, yaw, source):
        self.waypoints.append({
            'x': round(x, 3),
            'y': round(y, 3),
            'yaw': round(yaw, 1),
        })
        self._save()
        self.get_logger().info(
            f'已记录第 {len(self.waypoints)} 个点: x={x:.3f} y={y:.3f} '
            f'yaw={yaw:.1f} (来自 {source})')

    def on_goal(self, msg):
        self._append(
            msg.pose.position.x,
            msg.pose.position.y,
            math.degrees(quat_to_yaw(msg.pose.orientation)),
            'goal')

    def on_point(self, msg):
        self._append(msg.point.x, msg.point.y, 0.0, 'clicked_point')


def main():
    parser = argparse.ArgumentParser(description='在 RViz 中点击记录导航目标点')
    parser.add_argument(
        '--file', default='waypoints_recorded.yaml',
        help='输出 yaml 文件（默认当前目录 waypoints_recorded.yaml）')
    parser.add_argument(
        '--overwrite', action='store_true', help='清空已有记录，从头开始')
    parser.add_argument(
        '--no-end-at-start', dest='end_at_start', action='store_false',
        help='结束时不要自动追加起始位姿')
    args = parser.parse_args()

    out_file = os.path.abspath(args.file)
    rclpy.init()
    node = WaypointRecorder(out_file, args.overwrite, args.end_at_start)
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    node.finish()
    try:
        node.destroy_node()
    except Exception:
        pass
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
