from .base_handler import BaseHandler
from loguru import logger
import time, asyncio

class StrokeHandler(BaseHandler):
    def __init__(self, SETTINGS: dict) -> None:


        self.SETTINGS = SETTINGS
        self.OSR_CONN = None


        self.stroke_settings = SETTINGS['osr2']
        self.objective = self.stroke_settings['objective']
        self.max_pos = self.stroke_settings['max_pos']
        self.min_pos = self.stroke_settings['min_pos']
        self.updates_per_second = self.stroke_settings['updates_per_second']
        self.max_velocity = self.stroke_settings['max_velocity']
        
        self._handler = self.handler_linear
        
        self.last_level = 1
        self.last_update_time = None


    def set_connector(self,connector):
        self.OSR_CONN = connector


    def clamp(self, value, min_value, max_value):
        """Clamp value between min and max bounds."""
        return max(min(value, max_value), min_value)


    def calculate_new_position_linear(self, new_level):
        now = time.time()
        time_delta_real = now - self.last_update_time
        if self.updates_per_second > 0 and time_delta_real < (1 / self.updates_per_second):
            return self.last_level, -1


        duration = 1/self.updates_per_second
        velocity = 1000 * (new_level-self.last_level) / duration


        self.last_update_time = now
        self.last_level = new_level

        if abs(velocity) > self.max_velocity:
            new_level = self.last_level + (self.max_velocity * duration / 1000)
        
        if self.objective in ['inserting_self', 'inserting_others']:
            new_level = 1 - new_level

        return self.clamp(new_level, self.min_pos/1000, self.max_pos/1000), duration

    def osc_handler(self, address, *args):
        logger.info(f"VRCOSC: {address}: {args}")
        val = self.param_sanitizer(args)
        if self.last_update_time is None:
            self.last_update_time = time.time()
        asyncio.create_task(self._handler(val))
        return 1
    

    def build_tcode(self, level, duration):
        return f"L0{int(round(level,3)*1000)}I{int(round(duration,3)*1000)}"
    

    async def handler_linear(self, level):
        new_level, duration = self.calculate_new_position_linear(new_level=level)
        if duration <= 0 or new_level > 0.9 or new_level <0.1:
            return
        logger.info(f"Calculated new level:{new_level}, duration:{duration}")
        tcode = self.build_tcode(new_level, duration)
        if not self.OSR_CONN is None:
            await self.OSR_CONN.async_write_to_serial(tcode)
        return

