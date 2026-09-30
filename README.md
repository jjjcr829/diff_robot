# diff_robot — 差速移动机器人仿真 · 建图 · 定位导航（ROS 2 Humble + Gazebo）

面向 ROS 组考核任务：自建室内仿真场景，搭建差速小车（方形车身 + 四个轮子 + 二维激光雷达），
完成 SLAM 建图、地图保存、AMCL 定位、Nav2 多点导航（直行 / 转弯 / 绕障 / 到点停车）。

## 1. 环境与依赖

- Ubuntu 22.04 LTS
- ROS 2 Humble
- Gazebo Classic 11（gazebo_ros / gazebo_plugins）

```bash
sudo apt install -y \
  ros-humble-robot-state-publisher ros-humble-xacro ros-humble-rviz2 \
  ros-humble-gazebo-ros-pkgs ros-humble-gazebo-plugins \
  ros-humble-slam-toolbox ros-humble-nav2-bringup ros-humble-nav2-simple-commander \
  ros-humble-teleop-twist-keyboard
```



## 2. 工作空间与编译

```bash
mkdir -p ~/diff_ws/src
# 把本仓库的 diff_robot 包放到 ~/diff_ws/src/ 下（git clone 或拷贝）
cd ~/diff_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

> 注意：`--symlink-install` 只会把**编译时已存在**的文件软链接到 install。
> 之后**新增**的文件（新建的 world、地图、rviz 配置等）必须重新执行
> `colcon build --symlink-install`，否则用默认路径启动时找不到文件
> （Gazebo 会退化成空场景：没有墙、激光全是 inf、RViz 显示异常）。
> 修改已有文件不需要重新编译（软链接会直接生效）。

## 3. 目录结构

```
src/diff_robot/
├── urdf/diff_robot.urdf.xacro     # 模型：方车身 + 四轮全驱（双差速插件）+ 2D 雷达；轮子碰撞用球体保证直行
├── worlds/indoor.world            # 室内场景：四面墙 + 1m 方块 + 两个圆柱障碍
├── config/
│   ├── slam_params.yaml           # slam_toolbox 建图参数
│   ├── nav2_params.yaml           # AMCL + NavFn + DWB + waypoint_follower 参数
│   └── waypoints.yaml             # 依次执行的导航目标点（现场可改）
├── launch/
│   ├── gazebo.launch.py           # 只启动仿真（场景 + 机器人）
│   ├── mapping.launch.py          # 仿真 + slam_toolbox + RViz
│   ├── navigation.launch.py       # 仿真 + map_server + AMCL + Nav2 + RViz
│   └── waypoint_navigation.launch.py  # 一键：完整导航栈 + 自动依次执行航点
├── rviz/mapping.rviz / navigation.rviz
├── maps/my_room_map.pgm/.yaml     # 默认地图（与 my_room.world 对应）
├── maps/fishbot_map.pgm/.yaml     # indoor.world 场景的示例地图
└── scripts/
    ├── waypoints.py               # 依次执行 waypoints.yaml 中的目标点
    └── save_map.sh                # 保存地图
```

## 4. 使用步骤

### 4.1 启动仿真（验证模型）

```bash
ros2 launch diff_robot gazebo.launch.py
```

可观察：机器人可动、`/scan` 激光、`/odom` 里程计、TF 链路完整。

### 4.2 建图（SLAM）

**终端 1**：启动 仿真 + slam_toolbox + RViz

```bash
ros2 launch diff_robot mapping.launch.py
# 默认场景为 my_room.world、出生点 (1.5, 0.5)，无需额外参数
# 要用 indoor 场景：world:=$HOME/diff_ws/src/diff_robot/worlds/indoor.world x:=-1.45 y:=-0.55
```

**终端 2**：键盘遥控（先点一下这个终端窗口让它获得焦点）

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

| 按键 | 作用 |
|---|---|
| `i` / `,` | 前进 / 后退 |
| `j` / `l` | 左转 / 右转 |
| `k` | 停车 |
| `q` / `z` | 加大 / 减小速度 |
| `Ctrl+C` | 退出遥控 |

建图技巧：

- 速度降到 0.15~0.2 m/s，转弯慢一点，避免建图漂移
- 沿墙走一圈，再走一遍中间通道，障碍物周围也扫到
- **最后开回起点附近**触发回环闭合，墙线才会对齐
- 终端 1 的 RViz 里实时观察 `/map` 逐渐成形

### 4.3 保存地图

遥控退出后，在终端 2 执行：

```bash
ros2 run nav2_map_server map_saver_cli -f $HOME/diff_ws/src/diff_robot/maps/my_room_map
# 或使用脚本（默认保存为 maps/my_map.*）
bash ~/diff_ws/src/diff_robot/scripts/save_map.sh
```

输出两个文件（验收要提交的地图图像与元数据）：

- `my_room_map.pgm` —— 栅格地图图像
- `my_room_map.yaml` —— 元数据（分辨率、原点、阈值）

### 4.4 重新启动：加载地图 + 定位 + 导航

```bash
# ① 先在建图的终端 1 按 Ctrl+C 结束建图（否则 slam 和 amcl 会同时发布 map→odom）

# ② 启动 仿真 + map_server + AMCL + Nav2 + RViz（默认场景/地图/出生点即 my_room）
ros2 launch diff_robot navigation.launch.py
# 出生点或地图不同时显式指定：
# ros2 launch diff_robot navigation.launch.py world:=<world文件> map:=<地图yaml> x:=<x> y:=<y>
# AMCL 初始位姿在 config/nav2_params.yaml 的 initial_pose（已默认 1.5, 0.5）
```

RViz 里检查定位对齐：

- `Fixed Frame` 选 `map`
- 红色激光点应贴合地图墙边、机器人位姿稳定
- 不贴合时用工具栏 `2D Pose Estimate`：在机器人实际位置按住鼠标拖出朝向

手动发单点目标：RViz 工具栏 `Nav2 Goal` 点一下目标位置并拖出朝向；
批量按顺序执行见 4.5。

### 4.5 依次执行 n 个目标点

编辑 `config/waypoints.yaml`（map 坐标系，x/y 单位 m，yaw 单位度），然后：

```bash
ros2 run diff_robot waypoints.py
# 或指定文件
ros2 run diff_robot waypoints.py --file /path/to/waypoints.yaml
```

**在 RViz 里点击记录目标点**（推荐，现场给点最方便）：

```bash
# 导航启动后，另开一个终端运行记录器
ros2 run diff_robot record_waypoints.py \
  --file ~/diff_ws/src/diff_robot/config/waypoints_recorded.yaml
```

然后在 RViz 里用 `Nav2 Goal` 工具逐一点击目标位置并拖出朝向，每点一次自动追加一个点
（格式与 waypoints.yaml 相同）；`Ctrl+C` 结束记录。之后按顺序执行：

```bash
ros2 run diff_robot waypoints.py \
  --file ~/diff_ws/src/diff_robot/config/waypoints_recorded.yaml
```

（提示：点击 `Nav2 Goal` 会同时让机器人立即导航到该点，属正常现象；想从零开始加 `--overwrite`。）

航点文件里默认给的是 indoor.world 的示例坐标；当前默认场景是 my_room.world，使用前请按你的地图改成对应坐标（示例坐标对应三个考核场景：直行 / 转弯 / 绕障）：

| 序号 | 目标点 (x, y, yaw) | 场景 |
|---|---|---|
| 1 | (-1.15, 2.05, 90°) | 自出生点直行到左上角 |
| 2 | (0.50, 1.95, 0°) | 转弯向东 |
| 3 | (1.50, -0.50, -90°) | 转弯向南 |
| 4 | (1.00, -2.00, 180°) | 转弯向西南 |
| 5 | (-2.20, 0.00, 90°) | 直线被中间 1m 方块阻挡，全局路径需绕障 |

到点停车：`waypoint_follower` 每到达一个点自动停车，并停留 2 秒（`waypoint_pause_duration`）。

### 4.6 停车区显示

导航 launch 会自动启动 `parking_zone_publisher`，在 `map` 坐标系发布 `/parking_zone`
深蓝色标记（右上角 `(3.27, 1.35)`，0.55m × 0.51m = 车长宽各 +0.25m）；
RViz 的 `ParkingZone` 显示已配置好。机器人出生点与最后一个航点都在该区域内，
goal checker 容差 0.08m/0.12rad（满足 ≤0.25m / 15°）。

### 4.7 一键执行分段导航

```bash
ros2 launch diff_robot waypoint_navigation.launch.py
# 指定其它航点文件
ros2 launch diff_robot waypoint_navigation.launch.py \
  waypoints_file:=$HOME/diff_ws/src/diff_robot/config/waypoints.yaml
```

该 launch 一次性启动完整导航栈（仿真 + 地图 + AMCL + Nav2 + RViz），并自动运行
`waypoints.py`：等 Nav2 激活后依次执行航点文件中的目标点，无需再开第二个终端；
最后一个航点为回到起始位置和朝向。

> `waypoints.py` 启动时会先把**起始位姿**（默认 `x=3.27, y=1.35, yaw=180°`）发布给 AMCL——
> 否则 BasicNavigator 默认的 `(0,0,0)` 会覆盖定位导致 AMCL 跑飞（这是之前导航失败的原因）；
> 之后等 Nav2 激活再等 10s 让定位收敛才发第一个点。
> 可用 `--initial-x/--initial-y/--initial-yaw/--start-delay` 调整。

## 5. 节点 · 话题 · 坐标系（现场讲解要点）

**TF 链路**

```
map ──(AMCL)──> odom ──(Gazebo 差速插件)──> base_footprint ──(URDF)──> base_link ──> lidar_link / *_wheel_link
```

- 建图时 `map→odom` 由 slam_toolbox 发布
- 导航时 `map→odom` 由 AMCL 发布
- `odom→base_footprint` 由 gazebo_ros_diff_drive 插件发布（轮式里程计）
- `base_link→各传感器/轮子` 由 robot_state_publisher 根据 `/joint_states` 发布

**主要话题**

| 话题 | 说明 |
|---|---|
| `/scan` | 2D 激光（10Hz，240 点，0.12~8m） |
| `/odom` | 轮式里程计 |
| `/cmd_vel` | 速度指令（差速插件订阅） |
| `/map` | 栅格地图（建图时由 slam_toolbox 发布） |
| `/plan` `/local_plan` | 全局 / 局部路径（RViz 可视化） |
| `/amcl_pose` | 定位结果 |
| `/joint_states` | 轮子关节状态 |

**导航链路**：AMCL 提供定位 → NavFn 全局规划（`/plan`）→ DWB 局部规划与避障（`/local_plan`）→
差速插件执行 `/cmd_vel` → `waypoint_follower` 依次下发目标点。

**主要配置文件**

- `slam_params.yaml`：建图分辨率、雷达量程、回环参数
- `nav2_params.yaml`：AMCL 定位、代价地图（footprint/inflation）、NavFn、DWB、goal checker 容差（0.15m/0.15rad）、waypoint_follower

## 6. 自建场景（my_room.world，默认）

`worlds/my_room.world` 为自建室内场景（Gazebo Building Editor 绘制，约 7.9m × 4.5m，
外围围墙 + 内部隔断 + 一个圆柱障碍），出生点 `(1.5, 0.5)`，地图为 `maps/my_room_map.*`。
**已设为各 launch 的默认场景**，以下参数可省略，列出以便切换其他场景时参考：

```bash
ros2 launch diff_robot gazebo.launch.py \
  world:=$HOME/diff_ws/src/diff_robot/worlds/my_room.world x:=1.5 y:=0.5

ros2 launch diff_robot mapping.launch.py \
  world:=$HOME/diff_ws/src/diff_robot/worlds/my_room.world x:=1.5 y:=0.5

ros2 launch diff_robot navigation.launch.py \
  world:=$HOME/diff_ws/src/diff_robot/worlds/my_room.world \
  map:=$HOME/diff_ws/src/diff_robot/maps/my_room_map.yaml
```

换场景后必须重新建图；`nav2_params.yaml` 中 AMCL 的 `initial_pose` 要与出生点一致，
或在 RViz 中用 `2D Pose Estimate` 重新给定。

## 7. 第三方来源说明

- `worlds/my_room.world`：自建场景（Gazebo Building Editor 绘制）
- `worlds/indoor.world` 与 `maps/fishbot_map.*`：来自鱼香 ROS fishbot 教程场景
- `nav2_params.yaml` 基线：`nav2_bringup/params/nav2_params.yaml`
- `slam_params.yaml` 基线：`slam_toolbox/config/mapper_params_online_async.yaml`
- `rviz/navigation.rviz` 基线：`nav2_bringup/rviz/nav2_default_view.rviz`
- URDF 模型、各 launch、航点脚本、参数调优为本项目编写

## 8. 常见问题

**小车斜着走 / 不听遥控 / 乱跑**
1. 检查是否有旧会话残留（最常见原因）：`pgrep -a gzserver`、`ros2 node list`、
   `ros2 topic info /cmd_vel`（正常只应有 1 个发布者）。
   残留的 Nav2 节点会同时往 `/cmd_vel` 发指令，与遥控叠加导致斜行。
2. 彻底清理残留。注意：Linux 进程名超过 15 字符会被截断，`pkill -x robot_state_publisher`
   这类写法**无效**，必须用 `-f` 匹配完整命令行（方括号写法避免误杀自己）：
   ```bash
   pkill -9 -f "ros2 laun[c]h"
   pkill -9 -x gzserver; pkill -9 -x gzclient; pkill -9 -x rviz2
   pkill -9 -f "robot_state_publishe[r]"
   pkill -9 -f "async_slam_toolbo[x]"
   pkill -9 -f "teleop_twist_keyboar[d]"
   pkill -9 -f "velocity_smoothe[r]"; pkill -9 -f "controller_serve[r]"
   pkill -9 -f "planner_serve[r]"; pkill -9 -f "bt_navigato[r]"
   pkill -9 -f "behavior_serve[r]"; pkill -9 -f "waypoint_followe[r]"
   pkill -9 -x amcl; pkill -9 -x map_server
   ```
3. 启动后用 `ros2 topic info /cmd_vel` 自检：**订阅数应为 2**（四驱前后轴各一个）。
   只有 1 个说明后轴插件没起来，此时直行会跑偏，需要清理环境后重启。
4. 停止仿真请优先在 launch 终端按 `Ctrl+C`（会连带清理子节点），避免直接 `kill -9` 父进程。

**直行时缓慢跑偏**
模型为四轮全驱（前后轴各挂一个差速插件，后轴不发布里程计），轮子碰撞体用球体
并统一摩擦。实测直行 1.6m 横向偏差 <1cm、偏航 <0.1°，转向正常，无需额外处理。

**仿真很慢 / 运动只有命令值的一半**
本机（X250）运动时实时率约 0.5，属正常现象；Nav2 基于仿真时间工作，
导航精度不受影响。关闭 VSCode/浏览器、使用 `gui:=false` 可提升实时率。

**地图显示 No map received / Nav2 节点一直不激活**
1. 先确认地图文件本身能被加载：
   ```bash
   ros2 run nav2_map_server map_server --ros-args -r __node:=ms_test \
     -p yaml_filename:=$HOME/diff_ws/src/diff_robot/maps/fin_room_map.yaml
   ros2 lifecycle set /ms_test configure    # 成功会打印 Read map ... 152 X 84
   pkill -f ms_tes[t]
   ```
   （注意：地图 pgm 必须是严格的 P5 格式，文件大小 = 头部 + 宽×高，多一字节都会加载失败。）
2. 环境里配置了真机 WiFi 用的 CycloneDDS 单播配置（`~/cyclonedds.xml`，绑定网卡 + 单播 Peer），
   这种配置下退出/被杀掉的进程不会从发现列表清除，多次启停会积累"幽灵节点"，
   导致 Nav2 生命周期调用（Configure/Activate）超时失败。**三个 launch 已自动为本机仿真清除该配置**；
   手动运行其它工具时可用：
   ```bash
   env -u CYCLONEDDS_URI -u FASTRTPS_DEFAULT_PROFILES_FILE ros2 launch diff_robot navigation.launch.py
   ```
3. RViz 的 `Fixed Frame` 应设为 `map`（地图与导航都在 map 坐标系下）。
