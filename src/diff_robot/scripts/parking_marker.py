#!/usr/bin/env python3
import rclpy
from geometry_msgs.msg import Point
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from visualization_msgs.msg import Marker, MarkerArray

ZONE_CENTER = (3.27, 1.35)
ZONE_SIZE = (0.55, 0.51)
FILL_COLOR = (0.0, 0.0, 0.55, 1.0)
BORDER_COLOR = (0.2, 0.2, 1.0, 1.0)


class ParkingZonePublisher(Node):
    def __init__(self):
        super().__init__('parking_zone_publisher')
        qos = QoSProfile(
            depth=1,
            history=HistoryPolicy.KEEP_LAST,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.pub = self.create_publisher(MarkerArray, 'parking_zone', qos)
        self.timer = self.create_timer(1.0, self.publish)
        self.publish()

    def publish(self):
        stamp = self.get_clock().now().to_msg()
        arr = MarkerArray()

        fill = Marker()
        fill.header.frame_id = 'map'
        fill.header.stamp = stamp
        fill.ns = 'parking_zone'
        fill.id = 0
        fill.type = Marker.CUBE
        fill.action = Marker.ADD
        fill.pose.position.x = ZONE_CENTER[0]
        fill.pose.position.y = ZONE_CENTER[1]
        fill.pose.position.z = 0.005
        fill.pose.orientation.w = 1.0
        fill.scale.x = ZONE_SIZE[0]
        fill.scale.y = ZONE_SIZE[1]
        fill.scale.z = 0.01
        fill.color.r, fill.color.g, fill.color.b, fill.color.a = FILL_COLOR
        arr.markers.append(fill)

        border = Marker()
        border.header.frame_id = 'map'
        border.header.stamp = stamp
        border.ns = 'parking_zone'
        border.id = 1
        border.type = Marker.LINE_STRIP
        border.action = Marker.ADD
        border.pose.orientation.w = 1.0
        border.scale.x = 0.03
        border.color.r, border.color.g, border.color.b, border.color.a = BORDER_COLOR
        hx, hy = ZONE_SIZE[0] / 2.0, ZONE_SIZE[1] / 2.0
        for sx, sy in ((1, 1), (1, -1), (-1, -1), (-1, 1), (1, 1)):
            p = Point()
            p.x = ZONE_CENTER[0] + sx * hx
            p.y = ZONE_CENTER[1] + sy * hy
            p.z = 0.01
            border.points.append(p)
        arr.markers.append(border)

        self.pub.publish(arr)


def main():
    rclpy.init()
    node = ParkingZonePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
