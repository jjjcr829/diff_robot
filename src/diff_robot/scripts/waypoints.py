#!/usr/bin/env python3
import argparse
import math
import os
import time

import rclpy
import yaml
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def build_pose(navigator, x, y, yaw_deg):
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    yaw = math.radians(float(yaw_deg))
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


def main():
    default_file = os.path.join(
        get_package_share_directory('diff_robot'), 'config', 'waypoints.yaml')

    parser = argparse.ArgumentParser(description='依次执行 waypoints.yaml 中的导航目标点')
    parser.add_argument('--file', default=default_file, help='目标点 yaml 文件路径')
    parser.add_argument(
        '--start-delay', type=float, default=10.0,
        help='Nav2 激活后额外等待秒数，让定位收敛（默认 10s）')
    parser.add_argument('--initial-x', type=float, default=3.27, help='起始位置 x')
    parser.add_argument('--initial-y', type=float, default=1.35, help='起始位置 y')
    parser.add_argument('--initial-yaw', type=float, default=180.0, help='起始朝向(度)')
    args = parser.parse_args()

    try:
        with open(args.file, 'r') as f:
            waypoints = yaml.safe_load(f)['waypoints']
    except FileNotFoundError:
        print(f'航点文件不存在: {args.file}')
        print('可先运行 record_waypoints.py 在 RViz 里点击记录，或手动创建该 yaml')
        return

    rclpy.init()
    navigator = BasicNavigator()

    initial = PoseStamped()
    initial.header.frame_id = 'map'
    initial.pose.position.x = float(args.initial_x)
    initial.pose.position.y = float(args.initial_y)
    yaw0 = math.radians(float(args.initial_yaw))
    initial.pose.orientation.z = math.sin(yaw0 / 2.0)
    initial.pose.orientation.w = math.cos(yaw0 / 2.0)
    navigator.setInitialPose(initial)
    navigator.get_logger().info(
        f'已设置初始位姿: x={args.initial_x} y={args.initial_y} yaw={args.initial_yaw}°')

    navigator.get_logger().info('等待 Nav2 激活...')
    navigator.waitUntilNav2Active()

    if args.start_delay > 0:
        navigator.get_logger().info(
            f'等待 {args.start_delay:.0f}s 让 AMCL 定位收敛...')
        time.sleep(args.start_delay)

    poses = [build_pose(navigator, wp['x'], wp['y'], wp['yaw']) for wp in waypoints]
    navigator.get_logger().info(f'开始依次执行 {len(poses)} 个目标点')

    navigator.followWaypoints(poses)

    last_index = -1
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback is not None and feedback.current_waypoint != last_index:
            last_index = feedback.current_waypoint
            navigator.get_logger().info(
                f'正在前往第 {last_index + 1}/{len(poses)} 个目标点')
        time.sleep(0.2)

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info('全部目标点执行完成')
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warn('任务被取消')
    else:
        navigator.get_logger().error('存在未到达的目标点')

    navigator.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
