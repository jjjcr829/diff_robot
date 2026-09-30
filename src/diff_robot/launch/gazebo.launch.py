import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg_share = get_package_share_directory('diff_robot')
    gazebo_ros_share = get_package_share_directory('gazebo_ros')

    default_world = os.path.join(pkg_share, 'worlds', 'my_room.world')
    xacro_path = os.path.join(pkg_share, 'urdf', 'diff_robot.urdf.xacro')

    world = LaunchConfiguration('world')
    gui = LaunchConfiguration('gui')
    use_sim_time = LaunchConfiguration('use_sim_time')
    spawn_x = LaunchConfiguration('x')
    spawn_y = LaunchConfiguration('y')
    spawn_yaw = LaunchConfiguration('yaw')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_path]), value_type=str)

    declare_gui = DeclareLaunchArgument(
        'gui', default_value='true', description='是否启动 Gazebo 图形界面')
    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true', description='使用仿真时间')
    declare_world = DeclareLaunchArgument(
        'world', default_value=default_world, description='Gazebo 世界文件路径')
    declare_x = DeclareLaunchArgument('x', default_value='3.27', description='出生点 x')
    declare_y = DeclareLaunchArgument('y', default_value='1.35', description='出生点 y')
    declare_yaw = DeclareLaunchArgument('yaw', default_value='3.14159', description='出生朝向(rad)')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description,
            'use_sim_time': use_sim_time,
        }]
    )

    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gzserver.launch.py')),
        launch_arguments={
            'world': world,
            'verbose': 'false',
            'pause': 'false',
        }.items()
    )

    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_ros_share, 'launch', 'gzclient.launch.py')),
        condition=IfCondition(gui)
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_entity',
        output='screen',
        arguments=[
            '-topic', 'robot_description',
            '-entity', 'diff_robot',
            '-x', spawn_x,
            '-y', spawn_y,
            '-z', '0.02',
            '-Y', spawn_yaw,
        ]
    )

    return LaunchDescription([
        SetEnvironmentVariable('CYCLONEDDS_URI', ''),
        SetEnvironmentVariable('FASTRTPS_DEFAULT_PROFILES_FILE', ''),
        declare_gui,
        declare_use_sim_time,
        declare_world,
        declare_x,
        declare_y,
        declare_yaw,
        robot_state_publisher,
        gzserver,
        gzclient,
        spawn_entity,
    ])
