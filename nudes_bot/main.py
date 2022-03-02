from nudenet import NudeClassifier
from moviepy.editor import *

class ClipPoint:
    def __init__(self, point_time, is_nsfw) -> None:
        self.point_time = point_time
        self.is_nsfw = is_nsfw

class ClipRange:
    def __init__(self, start_point: ClipPoint, end_point: ClipPoint) -> None:
        self.start_point: ClipPoint = start_point
        self.end_point: ClipPoint = end_point

c = NudeClassifier()

result = c.classify_video("C:\\Users\\AdamFull\\Desktop\\botnet\\nudes_bot\\samples\\2022.02.19_sweetiewow_1.mp4")
predicates = result["preds"]

clip = VideoFileClip("C:\\Users\\AdamFull\\Desktop\\botnet\\nudes_bot\\samples\\2022.02.19_sweetiewow_1.mp4")

# > 90 - light and hard, > 95 - medium and hard, >  99 - hard only
points = [ClipPoint(int(int(key)/clip.fps), predicates[key]["unsafe"] > 0.992) for key in predicates]

start_point: ClipPoint = None
end_point: ClipPoint = None

ranges = []
counted = 0
for point in points:
    if not start_point and point.is_nsfw:
        start_point = point
    elif not end_point and not point.is_nsfw and start_point:
        end_point = point
    elif not end_point and counted >= len(points) - 1:
        end_point = point

    # adding subclip
    if start_point and end_point:
        ranges.append(ClipRange(start_point, end_point))
        start_point = end_point = None

    counted = counted + 1
 
clips = [clip.subclip(rng.start_point.point_time, rng.end_point.point_time) for rng in ranges]
final_video = concatenate_videoclips(clips)
final_video.write_videofile("my_concatenation.mp4")