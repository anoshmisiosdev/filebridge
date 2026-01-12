import asyncio
from collections import defaultdict
from datetime import datetime, timedelta 
import logging
from typing import Dict, Tuple, Union, List
from pathlib import Path
from blinkbridge.config import *


log = logging.getLogger(__name__)


class CameraManager:
    def __init__(self):
        self.camera_last_file = defaultdict(lambda: None)
        self.blink_root = CONFIG.get('cameras', {}).get('blink_root', None)
        
    def _parse_blink_filename(self, filename: str) -> Union[datetime, None]:
        '''
        Parse Blink local storage filename format: DD-HH-MM-SS_CameraName_ID.mp4
        Returns datetime if parsed successfully, None otherwise
        '''
        try:
            parts = filename.replace('.mp4', '').split('_')
            if len(parts) < 2:
                return None
            
            time_parts = parts[0].split('-')
            if len(time_parts) != 4:
                return None
            
            day, hour, minute, second = map(int, time_parts)
            return datetime(1900, 1, day, hour, minute, second)
        except (ValueError, IndexError):
            return None
    
    def _get_video_files_for_camera(self, camera_name: str) -> List[Path]:
        '''Get all video files for a camera from Blink local storage structure'''
        if not self.blink_root:
            log.warning(f"{camera_name}: blink_root not configured")
            return []
        
        blink_path = Path(self.blink_root)
        if not blink_path.exists():
            log.warning(f"{camera_name}: Blink root directory does not exist: {blink_path}")
            return []
        
        video_files = []
        
        # Search through year/month folders (YY-MM format)
        for year_month_dir in blink_path.iterdir():
            if not year_month_dir.is_dir():
                continue
            
            # Look for video files matching the camera name
            for video_file in year_month_dir.glob('*.mp4'):
                # Check if filename contains the camera name
                if camera_name.lower() in video_file.name.lower():
                    video_files.append(video_file)
        
        # Sort by parsed timestamp, newest first
        video_files_with_time = []
        for f in video_files:
            parsed_time = self._parse_blink_filename(f.name)
            if parsed_time:
                video_files_with_time.append((f, parsed_time))
        
        # Sort by time, newest first
        video_files_with_time.sort(key=lambda x: x[1], reverse=True)
        return [f[0] for f in video_files_with_time]
    async def save_latest_clip(self, camera_name: str, force: bool=False) -> Union[Path, None]:
        '''
        Get the latest video file for a camera
        ''' 
        camera_name_sanitized = camera_name.lower().replace(' ', '_')
        dest_file_name = PATH_VIDEOS / f"{camera_name_sanitized}_latest.mp4"
    
        # don't process if clip already exists and not forcing
        if dest_file_name.exists() and not force:
            log.debug(f"{camera_name}: using existing file, {dest_file_name}")
            return dest_file_name

        video_files = self._get_video_files_for_camera(camera_name)
        
        if not video_files:
            log.warning(f"{camera_name}: no video files found")
            return None
        
        latest_video = video_files[0]
        log.debug(f'{camera_name}: using video file: {latest_video}')
        
        # Copy/link the video file to the output location
        if latest_video.suffix.lower() == '.mp4':
            # If already MP4, create a symlink
            if dest_file_name.exists():
                dest_file_name.unlink()
            dest_file_name.symlink_to(latest_video)
        else:
            # For other formats, would need ffmpeg conversion
            # For now, just symlink and let downstream handle conversion if needed
            if dest_file_name.exists():
                dest_file_name.unlink()
            dest_file_name.symlink_to(latest_video)
        
        log.debug(f'{camera_name}: linked video to {dest_file_name}')
        return dest_file_name
    
    async def check_for_motion(self, camera_name: str) -> Union[Path, None]:
        '''
        Check if a new video file is available for the camera
        '''
        video_files = self._get_video_files_for_camera(camera_name)
        
        if not video_files:
            return None
        
        latest_video = video_files[0]
        
        # Check if this is a new file
        if self.camera_last_file[camera_name] == latest_video:
            return None

        log.debug(f"{camera_name}: new video detected: {latest_video}")
        
        camera_name_sanitized = camera_name.lower().replace(' ', '_')
        dest_file_name = PATH_VIDEOS / f"{camera_name_sanitized}_latest.mp4"
        
        # Link/copy the new video file
        if dest_file_name.exists():
            dest_file_name.unlink()
        
        if latest_video.suffix.lower() == '.mp4':
            dest_file_name.symlink_to(latest_video)
        else:
            dest_file_name.symlink_to(latest_video)
        
        self.camera_last_file[camera_name] = latest_video
        
        log.debug(f"{camera_name}: linked new video to {dest_file_name}")
        return dest_file_name
        
    def get_cameras(self) -> List[str]:
        '''Get list of configured cameras'''
        return list(self.cameras_config.keys())
    
    async def start(self) -> None:
        '''Initialize the camera manager'''
        log.debug(f"Initialized with {len(self.get_cameras())} camera(s)")
        for camera in self.get_cameras():
            log.debug(f"  - {camera}: {self.cameras_config[camera]}")
    
    async def close(self) -> None:
        '''Clean up resources'''
        pass

async def test() -> None:
    cm = CameraManager()

    await cm.start()

    for camera in cm.get_cameras():
        file_name = await cm.save_latest_clip(camera)
        print(f"{camera}: {file_name}")

    await cm.close()

if __name__ == "__main__":
    asyncio.run(test())
