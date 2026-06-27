include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "map",
  tracking_frame = "base_link",
  published_frame = "base_link",
  odom_frame = "odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = false,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

MAP_BUILDER.use_trajectory_builder_2d = true

-- ✅ FIXED: Better LIDAR accuracy
TRAJECTORY_BUILDER_2D.min_range = 0.12
TRAJECTORY_BUILDER_2D.max_range = 6.0  -- ← INCREASED for better scan matching
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 1.0
TRAJECTORY_BUILDER_2D.use_imu_data = false
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

-- ✅ FIXED: Better real-time scan matching
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.linear_search_window = 0.1  -- ← INCREASED
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.angular_search_window = math.rad(10.)  -- ← INCREASED
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.translation_delta_cost_weight = 1e2  -- ← INCREASED
TRAJECTORY_BUILDER_2D.real_time_correlative_scan_matcher.rotation_delta_cost_weight = 1e2  -- ← INCREASED

-- ✅ FIXED: Ceres optimization (more weight on accuracy)
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.occupied_space_weight = 25.  -- ← INCREASED
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.translation_weight = 100.  -- ← INCREASED
TRAJECTORY_BUILDER_2D.ceres_scan_matcher.rotation_weight = 100.  -- ← INCREASED

-- ✅ FIXED: Motion filter (better detail preservation)
TRAJECTORY_BUILDER_2D.motion_filter.max_time_seconds = 5.
TRAJECTORY_BUILDER_2D.motion_filter.max_distance_meters = 0.3  -- ← REDUCED (more scans)
TRAJECTORY_BUILDER_2D.motion_filter.max_angle_radians = math.rad(1.0)  -- ← REDUCED

-- ✅ FIXED: Better submaps
TRAJECTORY_BUILDER_2D.submaps.num_range_data = 60
TRAJECTORY_BUILDER_2D.submaps.grid_options_2d.resolution = 0.025  -- ← INCREASED RESOLUTION (5cm → 2.5cm)

-- ✅ FIXED: Pose graph optimization (stricter loop closure)
POSE_GRAPH.optimize_every_n_nodes = 45  -- ← REDUCED (optimize more often)
POSE_GRAPH.constraint_builder.min_score = 0.65  -- ← INCREASED (only good matches)
POSE_GRAPH.constraint_builder.global_localization_min_score = 0.7  -- ← INCREASED

-- ✅ FIXED: Loop closure (more aggressive)
POSE_GRAPH.constraint_builder.max_constraint_distance = 50.  -- ← INCREASED search range
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.linear_search_window = 15.  -- ← INCREASED
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.angular_search_window = math.rad(60.)  -- ← INCREASED
POSE_GRAPH.constraint_builder.fast_correlative_scan_matcher.branch_and_bound_depth = 8  -- ← INCREASED

-- ✅ FIXED: Global optimization (trust LIDAR more, odometry less)
POSE_GRAPH.constraint_builder.loop_closure_translation_weight = 1e5  -- ← INCREASED (trust loop closure)
POSE_GRAPH.constraint_builder.loop_closure_rotation_weight = 1e6  -- ← INCREASED
POSE_GRAPH.optimization_problem.huber_scale = 1e0  -- ← REDUCED (stricter)
POSE_GRAPH.optimization_problem.acceleration_weight = 1e2  -- ← REDUCED
POSE_GRAPH.optimization_problem.rotation_weight = 1e6  -- ← INCREASED

-- ✅ FIXED: Odometry weights (reduce drift influence)
POSE_GRAPH.optimization_problem.odometry_translation_weight = 1e4  -- ← REDUCED (don't trust encoders too much)
POSE_GRAPH.optimization_problem.odometry_rotation_weight = 1e4  -- ← REDUCED

return options
