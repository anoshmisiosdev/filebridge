# FileBridge

**Notes**: 


---

This is a more agnostic solution for camera systems that allow local storage systems like Arlo and Blink to be properly RTSP'd into applications like Frigate.

Once the RTSP streams are available, you can use them in applications such as [Frigate NVR](https://github.com/blakeblackshear/frigate) (e.g. for better person detection) or [Scrypted](https://github.com/koush/scrypted) (e.g. for Homekit Secure Video support).

# How it works

1. blinkbridge downloads the latest clip for each enabled camera from the Blink server
2. FFmpeg extracts the last frame from each clip and creates a short still video (~0.5s) from it 
3. The still video is published on a loop to MediaMTX (using [FFMpeg's concat demuxer](https://trac.ffmpeg.org/wiki/Concatenate#demuxer))
4. When motion is detected, the new clip is downloaded and published
5. A still video from the last frame of the new clip is then published on a loop

# Usage

1. Download `compose.yaml` from this repo and modify accordingly
2. Download `config/config.json`, save to `./config/` and modify accordingly (be sure to enter your Blink login creditials)
3. Run `docker compose run blinkbridge` and enter your Blink verification code when prompted (this only has to be done once and will be saved in `config/.cred.json`). Exit with CTRL+c
4. Run `docker compose up` to start the service. The RTSP URLs will be printed to the console.


# Related projects

* https://github.com/kaffetorsk/arlo-streamer


