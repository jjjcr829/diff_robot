import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('diff_robot')
    slam_share = get_package_share_directory('slam_toolbox')

    default_world = os.path.join(pkg_share, 'worlds', 'my_room.world')

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    rviz = LaunchConfiguration('rviz')
    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_world = DeclareLaunchArgument(
        'world', default_value=default_world, description='Gazebo 世界文件路径')
    declare_gui = DeclareLaunchArgument('gui', default_value='true')
    declare_rviz = DeclareLaunchArgument('rviz', default_value='true')
    declare_use_sim_time = DeclareLaunchArgument('use_sim_time', default_value='true')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'gazebo.launch.py')),
        launch_arguments={
            'world': world,
            'gui': gui,
            'use_sim_time': use_sim_time,
        }.items()
    )

    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(slam_share, 'launch', 'online_async_launch.py')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'slam_params_file': os.path.join(pkg_share, 'config', 'slam_params.yaml'),
        }.items()
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join(pkg_share, 'rviz', 'mapping.rviz')],
        condition=IfCondition(rviz)
    )

    return LaunchDescription([
        SetEnvironmentVariable('CYCLONEDDS_URI', ''),
        SetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE', ''),
        declare_world,
        declare_gui,
        declare_rviz,
        declare_use_sim_time,
        gazebo,
        slam,
        rviz_node,
    ])
