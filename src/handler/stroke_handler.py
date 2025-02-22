import numpy as np
import collections
from .base_handler import BaseHandler
from loguru import logger
import time, asyncio, math, json

# from ..connector.coyotev3ws import DGConnection


class StrokeHandler(BaseHandler):
    def __init__(self, SETTINGS: dict) -> None:
        self.SETTINGS = SETTINGS
        self.OSR_CONN = None
        self.stroke_settings = SETTINGS['osr2']

        self.stroke_mode  = self.stroke_settings['stroke_mode']
        self.user_type = self.stroke_settings['user_type']
        
        if self.stroke_mode == 'linear':
            self._handler = self.handler_linear
        elif self.stroke_mode == 'motion':
            self._handler = self.handler_motion
        else:
            raise ValueError(f"Not supported mode: {self.stroke_mode}, only supports [linear/motion]")
        
        self.last_level = 1
        self.last_update_time = None
        self.last_velocity = None
        
        
        self.bg_wave_update_time_window = 0.1
        self.bg_wave_current_strength = 0

        self.touch_dist_arr = collections.deque(maxlen=20)

        self.to_clear_time    = 0
        self.is_cleared       = True




    def set_connector(self,connector):
        self.OSR_CONN = connector
    
    def start_background_jobs(self):
        logger.info(f"background job started.")
        # asyncio.ensure_future(self.clear_check())
        # if self.shock_mode == 'shock':
        #     asyncio.ensure_future(self.feed_wave())
        print(f"Shock mode:{self.stroke_mode}")
        # if self.stroke_mode == 'binary':
        #     asyncio.ensure_future(self.test_feeder())
        # elif self.stroke_mode == 'float':
        #     asyncio.ensure_future(self.test_feeder())


    def clamp(self, value, min_value, max_value):
        """Clamp value between min and max bounds."""
        return max(min(value, max_value), min_value)


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
        now = time.time()
        time_delta_real = now - self.last_push_time
        if updates_per_second > 0 and time_delta_real < (1 / updates_per_second):
            return self.last_level
        time_delta = min(time_delta_real, 0.25)  # Safety limit for max time delta (250 ms)
        time_delta_seconds = time_delta / 1000

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


    



    def osc_handler(self, address, *args):
        logger.info(f"VRCOSC: {address}: {args}")
        val = self.param_sanitizer(args)
        if self.last_update_time is None:
            self.last_update_time = time.time()
        asyncio.create_task(self._handler(val))
        return 1
    


    async def handler_motion(self, level):
        raise NotImplemented
    

    async def handler_linear(self, level):
        new_level, duration = self.calculate_new_position_linear(new_level=level, max_acceleration=20, duration_mult=1, updates_per_second=10)
        logger.info(f"Calculated new level:{new_level}, duration:{duration}")
        return
    

    async def handler_shock(self, distance):
        current_time = time.time()
        if distance > self.mode_config['trigger_range']['bottom'] and current_time > self.to_clear_time:
            shock_duration = self.mode_config['shock']['duration']
            await self.set_clear_after(shock_duration)
            logger.success(f'Channel {self.channel}: Shocking for {shock_duration} s.')
            asyncio.create_task(self.send_shock_wave(shock_duration, self.mode_config['shock']['wave']))

    async def handler_touch(self, distance):
        await self.set_clear_after(0.5)
        out_distance = self.normalize_distance(distance)
        if out_distance == 0:
            return
        t = time.time()
        self.touch_dist_arr.append([t,out_distance])









    # async def clear_check(self):
    #     # logger.info(f'Channel {self.channel} started clear check.')
    #     sleep_time = 0.05
    #     while 1:
    #         await asyncio.sleep(sleep_time)
    #         current_time = time.time()
    #         # logger.debug(current_time)
    #         # logger.debug(f"{str(self.is_cleared)}, {current_time}, {self.to_clear_time}")
    #         # if not self.is_cleared and current_time > self.to_clear_time:
    #         #     self.is_cleared = True
    #         #     self.bg_wave_current_strength = 0
    #         #     self.touch_dist_arr.clear()
    #         #     # await self.DG_CONN.broadcast_clear_wave(self.channel)
    #         #     logger.info(f'Channel {self.channel}, wave cleared after timeout.')
    
    # async def feed_wave(self):
    #     raise NotImplemented
    #     logger.info(f'Channel {self.channel} started wave feeding.')
    #     sleep_time = 1
    #     while 1:
    #         await asyncio.sleep(sleep_time)
    #         await self.DG_CONN.broadcast_wave(channel=self.channel, wavestr=self.shock_settings['shock_wave'])

    # async def set_clear_after(self, val):
    #     self.is_cleared = False
    #     self.to_clear_time = time.time() + val

    # @staticmethod
    # def generate_wave_100ms(freq, from_, to_):
    #     assert 0 <= from_ <= 1, "Invalid wave generate."
    #     assert 0 <= to_   <= 1, "Invalid wave generate."
    #     from_ = int(100*from_)
    #     to_   = int(100*to_)
    #     ret = ["{:02X}".format(freq)]*4
    #     delta = (to_ - from_) // 4
    #     ret += ["{:02X}".format(min(max(from_ + delta*i, 0),100)) for i in range(1,5,1)]
    #     ret = ''.join(ret)
    #     return json.dumps([ret],separators=(',', ':'))
    
    # def normalize_distance(self, distance):
    #     out_distance = 0
    #     trigger_bottom = self.mode_config['trigger_range']['bottom']
    #     trigger_top = self.mode_config['trigger_range']['top']
    #     if distance > self.mode_config['trigger_range']['bottom']:
    #         out_distance = (
    #                 distance - trigger_bottom
    #             ) / (
    #                 trigger_top - trigger_bottom
    #             )
    #         out_distance = 1 if out_distance > 1 else out_distance
    #     return out_distance

    # async def handler_distance(self, distance):
    #     await self.set_clear_after(0.5)
    #     self.bg_wave_current_strength = self.normalize_distance(3)

    # async def distance_background_wave_feeder(self):
    #     tick_time_window = self.bg_wave_update_time_window / 20
    #     next_tick_time   = 0
    #     last_strength    = 0
    #     while 1:
    #         current_time = time.time()
    #         if current_time < next_tick_time:
    #             await asyncio.sleep(tick_time_window)
    #             continue
    #         next_tick_time = current_time + self.bg_wave_update_time_window
    #         current_strength = self.bg_wave_current_strength
    #         if current_strength == last_strength == 0:
    #             continue
    #         wave = self.generate_wave_100ms(
    #             self.mode_config['distance']['freq_ms'], 
    #             last_strength, 
    #             current_strength
    #         )
    #         logger.success(f'Channel {self.channel}, strength {last_strength:.3f} to {current_strength:.3f}, Sending {wave}')
    #         last_strength = current_strength
    #         await self.DG_CONN.broadcast_wave(self.channel, wavestr=wave)
    
    # async def send_shock_wave(self, shock_time, shockwave: str):
    #     shockwave_duration = (shockwave.count(',')+1) * 0.1
    #     send_times = math.ceil(shock_time // shockwave_duration)
    #     for _ in range(send_times):
    #         await self.DG_CONN.broadcast_wave(self.channel, wavestr=self.mode_config['shock']['wave'])
    #         await asyncio.sleep(shockwave_duration)
    

    
    # def compute_derivative(self):
    #     data = self.touch_dist_arr
    #     if len(data) < 4:
    #         # logger.warning('At least 4 samples are required to calculate acc and jerk.')
    #         return 0, 0, 0, 0

    #     time_ = np.array([point[0] for point in data])
    #     distance = np.array([point[1] for point in data])

    #     window_size = 3
    #     distance = np.convolve(distance, np.ones(window_size) / window_size, mode='valid')
    #     time_ = time_[:len(distance)]

    #     velocity = np.gradient(distance, time_)
    #     acceleration = np.gradient(velocity, time_)
    #     jerk = np.gradient(acceleration, time_)
    #     # logger.success(f"{distance[-1]:9.4f} {velocity[-1]:9.4f} {acceleration[-1]:9.4f} {jerk[-1]:9.4f}")
    #     return distance[-1], velocity[-1], acceleration[-1], jerk[-1]

    # async def touch_background_wave_feeder(self):
    #     tick_time_window = self.bg_wave_update_time_window / 20
    #     next_tick_time   = 0
    #     last_strength    = 0
    #     while 1:
    #         current_time = time.time()
    #         if current_time < next_tick_time:
    #             await asyncio.sleep(tick_time_window)
    #             continue
    #         next_tick_time = current_time + self.bg_wave_update_time_window
    #         n_derivative = self.mode_config['touch']['n_derivative']
    #         current_strength = self.compute_derivative()[n_derivative]
    #         derivative_params = self.mode_config['touch']['derivative_params'][n_derivative]
    #         current_strength = max(min(derivative_params['bottom'],abs(current_strength)),derivative_params['top'])/(derivative_params['top']-derivative_params['bottom'])

    #         self.bg_wave_current_strength = current_strength
    #         if current_strength == last_strength == 0:
    #             continue
    #         wave = self.generate_wave_100ms(
    #             self.mode_config['touch']['freq_ms'], 
    #             last_strength, 
    #             current_strength
    #         )
    #         logger.success(f'Channel {self.channel}, strength {last_strength:.3f} to {current_strength:.3f}, Sending {wave}')
    #         last_strength = current_strength
    #         # await self.DG_CONN.broadcast_wave(self.channel, wavestr=wave)
