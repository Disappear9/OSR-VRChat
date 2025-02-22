def calculate_new_position_linear(self, new_level, max_velocity, max_acceleration, duration_mult, updates_per_second):
    """
    Calculate the new position and the duration required to reach the given level, based on linear motion parameters.

    Args:
    - new_level (float): The desired level (normalized between 0 and 1).
    - max_velocity (float): Maximum velocity for the movement.
    - max_acceleration (float): Maximum acceleration for the movement.
    - duration_mult (float): Multiplier for the duration of the movement.
    - updates_per_second (int): Rate of updates per second to calculate the duration.

    Returns:
    - new_level (float): The new level, clamped between 0 and 1.
    - duration (float): The time required to reach the new level.
    """
    # Ensure we have valid global values for last level, velocity, and acceleration
    if self.last_level is None:
        self.last_level = 0  # Initial level if None
    if self.last_velocity is None:
        self.last_velocity = 0  # Initial velocity if None
    if self.last_acceleration is None:
        self.last_acceleration = max_acceleration  # Assume default acceleration if None

    # Time delta calculation
    time_delta = 1000 / updates_per_second  # Time for each update (ms)
    time_delta_seconds = time_delta / 1000  # Time in seconds for each update

    # Initial position (current level) and target position
    current_position = self.last_level
    target_position = new_level

    # Velocity and acceleration management
    old_velocity = self.last_velocity
    max_velocity = self.clamp(max_velocity, 0, 1)
    max_acceleration = self.clamp(max_acceleration, 0, 100)  # Assuming maximum acceleration should be reasonable

    # Calculate required stopping distance (smooth stop)
    abs_distance_required_to_stop_smoothly = (old_velocity ** 2) / (2 * max_acceleration)
    stop_position = current_position + (old_velocity < 0 and -1 or 1) * abs_distance_required_to_stop_smoothly
    from_stop_position_to_target = target_position - stop_position

    # Compute new velocity depending on acceleration/deceleration
    new_velocity_if_we_add = old_velocity + max_acceleration * time_delta_seconds
    new_velocity_if_we_subtract = old_velocity - max_acceleration * time_delta_seconds

    # Clamp new velocities to maximum velocity
    if abs(new_velocity_if_we_add) > max_velocity:
        new_velocity_if_we_add = (new_velocity_if_we_add > 0 and 1 or -1) * max_velocity
    if abs(new_velocity_if_we_subtract) > max_velocity:
        new_velocity_if_we_subtract = (new_velocity_if_we_subtract > 0 and 1 or -1) * max_velocity

    # Determine the best direction to move toward the target
    new_pos_if_we_add = current_position + new_velocity_if_we_add * time_delta_seconds
    new_pos_if_we_subtract = current_position + new_velocity_if_we_subtract * time_delta_seconds

    if target_position == new_pos_if_we_add:
        new_velocity = new_velocity_if_we_add
    elif target_position == new_pos_if_we_subtract:
        new_velocity = new_velocity_if_we_subtract
    else:
        new_velocity = (from_stop_position_to_target > 0 and new_velocity_if_we_add or new_velocity_if_we_subtract)

    # Final new position calculation
    new_position = current_position + new_velocity * time_delta_seconds

    # Clamp the new position between 0 and 1
    if new_position > 1:
        new_position = 1
        new_velocity = 0
    if new_position < 0:
        new_position = 0
        new_velocity = 0

    # Set the final new level
    new_level = self.clamp(new_position, 0, 1)

    # Calculate the duration required to reach the new level
    # Assume linear movement; time required = distance / velocity
    if new_velocity != 0:
        duration = abs(target_position - current_position) / new_velocity
    else:
        duration = 0  # If no movement occurs, no duration

    # Apply duration multiplier
    duration *= duration_mult

    # Store new values for next update
    self.last_level = new_position
    self.last_velocity = new_velocity

    return new_level, duration


def clamp(self, value, min_value, max_value):
    """Clamp value between min and max bounds."""
    return max(min(value, max_value), min_value)
