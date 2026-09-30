import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_share = get_package_share_directory('diff_robot')

    waypoints_file = LaunchConfiguration('waypoints_file')
    world = LaunchConfiguration('world')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    gui = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_waypoints = DeclareLaunchArgument(
        'waypoints_file',
        default_value=os.path.join(pkg_share, 'config', 'waypoints.yaml'),
        description='要依次执行的航点 yaml 文件')
    declare_world = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(pkg_share, 'worlds', 'my_room.world'),
        description='Gazebo 世界文件路径')
    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_share, 'maps', 'fin_room_map.yaml'),
        description='用于定位的地图 yaml 文件')
    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(pkg_share, 'config', 'nav2_params.yaml'),
        description='Nav2 参数文件')
    declare_gui = DeclareLaunchArgument('gui', default_value='true')
    declare_rviz = DeclareLaunchArgument('rviz', default_value='true')
    declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true')

    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'navigation.launch.py')),
        launch_arguments={
            'world': world,
            'map': map_yaml,
            'params_file': params_file,
            'gui': gui,
            'rviz': rviz,
            'use_sim_time': use_sim_time,
        }.items()
    )

    waypoints_node = ExecuteProcess(
        cmd=['ros2', 'run', 'diff_robot', 'waypoints.py',
             '--file', waypoints_file],
        output='screen')

    return LaunchDescription([
        declare_waypoints,
        declare_world,
        declare_map,
        declare_params,
        declare_gui,
        declare_rviz,
        declare_use_sim_time,
        navigation,
        waypoints_node,
    ])
