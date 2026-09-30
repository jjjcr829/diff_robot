cmake_minimum_required(VERSION 3.8)
project(diff_robot)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
  launch
  urdf
  worlds
  config
  rviz
  maps
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/waypoints.py
  scripts/save_map.sh
  scripts/parking_marker.py
  scripts/record_waypoints.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
