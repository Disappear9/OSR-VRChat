from .base_handler import BaseHandler
from loguru import logger
import time, asyncio
from collections import deque

class StrokeHandler(BaseHandler):
    def __init__(self, SETTINGS: dict) -> None:


        self.SETTINGS = SETTINGS
        self.OSR_CONN = None
        self.stop_flag = 0
        self.use_udp = SETTINGS['osr2']['use_udp_server']

        self.stroke_settings = SETTINGS['osr2']
        self.objective = self.stroke_settings['objective']
        self.max_pos = self.stroke_settings['max_pos']
        self.min_pos = self.stroke_settings['min_pos']
        self.updates_per_second = self.stroke_settings['updates_per_second']
        self.max_velocity = self.stroke_settings['max_velocity']
        # self.max_acceleration = self.stroke_settings['max_acceleration']
        # self.ema_filter = self.stroke_settings['ema_filter']
        self.vrchat_min = self.stroke_settings['vrchat_min']
        self.vrchat_max = self.stroke_settings['vrchat_max']
        # self.last_levels = deque(maxlen=5)
        self.expected_time = 1/self.updates_per_second


        self.panel_data = {
            "raw_level":0,
            "raw_velocity":0,
            "raw_acceleration":0,
            "processed_velocity":0,
            "processed_acceleration":0,
            "processed_level":0,
            "output_level":0
        }

        self._handler = self.handler_linear
        if self.objective in ['inserting_self', 'inserting_others']:
            self.last_level = 1 - (self.min_pos/1000)
        else:
            self.last_level = self.min_pos/1000
        self.last_update_time = None
        self.last_velocity = 0
        
    def get_panel_data(self):
    
        return self.panel_data

    def set_connector(self,connector):
        self.OSR_CONN = connector


    def clamp(self, value, min_value, max_value):
        """Clamp value between min and max bounds."""
        return max(min(value, max_value), min_value)


    def calculate_new_position_linear(self, new_level):
        now = time.time()
        time_delta_real = now - self.last_update_time
        set_duration = 1/self.updates_per_second

        if time_delta_real <= self.expected_time*0.9:#self.updates_per_second > 0 and time_delta_real < (set_duration):
            return self.last_level, -1,0
        

        duration = set_duration
        # duration *= 1.25
        if time_delta_real > 1.5*set_duration:
            duration = set_duration*1.2
        else:
            duration = time_delta_real
        new_level = (self.clamp(new_level, self.vrchat_min/1000, self.vrchat_max/1000) - self.vrchat_min/1000) / (self.vrchat_max/1000 - self.vrchat_min/1000)
        # logger.info(f"Last Level{self.last_level}, new level{new_level}, delta{time_delta_real}")
        #apply ema filtering
        # new_level = self.ema_filter * new_level + (1-self.ema_filter)* self.last_level
        # weights = [0.1, 0.1, 0.25, 0.25, 0.3]
        # self.last_levels.append(new_level)
        # if len(list(self.last_levels)) >=5:
        #     new_level = sum(v * w for v, w in zip(list(self.last_levels), weights))


        new_velocity = 1000 * (new_level - self.last_level) / duration
        new_velocity = min(abs(new_velocity), self.max_velocity)
        acceleration = (new_velocity - self.last_velocity) / duration

        # if abs(acceleration) > self.max_acceleration:
        #     if acceleration < 0:
        #         new_velocity = self.last_velocity + (-1 * self.max_acceleration * duration)
        #         acceleration = -1 * self.max_acceleration
        #     else:
        #         new_velocity = self.last_velocity + self.max_acceleration * duration
        #         acceleration = self.max_acceleration


        
        self.expected_time = 1000 * (new_level - self.last_level) / abs(new_velocity)
        self.panel_data["raw_level"] = new_level*1000
        self.panel_data["raw_velocity"] = new_velocity
        self.panel_data["raw_acceleration"] = acceleration
        
        

        # if abs(new_velocity) > self.max_velocity:
        #     if new_velocity < 0:
        #         new_level = self.last_level + (-1 * self.max_velocity * duration / 1000)
        #         new_velocity = -1 * self.max_velocity
        #     else:
        #         new_level = self.last_level + (self.max_velocity * duration / 1000)
        #         new_velocity = self.max_velocity


        
            
        self.panel_data["processed_level"] = new_level*1000
        self.panel_data["processed_velocity"] = new_velocity
        self.panel_data["processed_acceleration"] = acceleration

        self.last_update_time = now
        self.last_level = new_level
        self.last_velocity = new_velocity
        

        if self.objective in ['inserting_self', 'inserting_others']:
            new_level = 1 - new_level

        range_limit = (self.max_pos/1000) - (self.min_pos/1000)
        final_level = range_limit * new_level + (self.min_pos/1000)
        
        self.panel_data["output_level"] = final_level*1000
        
        return final_level, duration, new_velocity

    def osc_handler(self, address, *args):
        # logger.info(f"VRCOSC: {address}: {args}")
        if "PenOthers" in address and self.objective == "inserting_others":
            # logger.info(f"VRCOSC: {address}: {args}")
            val = self.param_sanitizer(args)
            if self.last_update_time is None:
                self.last_update_time = time.time()
            asyncio.create_task(self._handler(val))
            return

        elif "PenSelf" in address and self.objective == "inserting_self":
            # logger.info(f"VRCOSC: {address}: {args}")
            val = self.param_sanitizer(args)
            if self.last_update_time is None:
                self.last_update_time = time.time()
            asyncio.create_task(self._handler(val))
            return
    

    def build_tcode_interval(self, level, duration):
        return f"L0{int(round(level,3)*1000)}I{int(round(duration,3)*1000)}"
    
    def build_tcode_velocity(self, level, velocity):
        logger.info(f"L0{int(round(level,3)*1000)}S{int(round(velocity,3))}")
        return f"L0{int(round(level,3)*1000)}S{int(round(velocity,3))}"

    async def handler_linear(self, level):
        new_level, duration, new_velocity = self.calculate_new_position_linear(new_level=level)
        if duration <= 0:
            return
        logger.info(f"Calculated new level:{new_level}, duration:{duration}")
        tcode = self.build_tcode_velocity(new_level, abs(new_velocity))
        if not self.OSR_CONN is None:
            if (self.use_udp == False):
                await self.OSR_CONN.async_write_to_serial(tcode)
            else:
                await self.OSR_CONN.async_write_to_udp(tcode)
        return
    
    def start_background_jobs(self):
        # logger.info(f"Channel: {self.channel}, background job started.")
        asyncio.ensure_future(self.clear_check())


    async def clear_check(self):
        # logger.info(f'Channel {self.channel} started clear check.')
        sleep_time = 0.05
        while 1:
            await asyncio.sleep(sleep_time)
            current_time = time.time()
            logger.info(current_time)
            if (self.stop_flag):
                break


