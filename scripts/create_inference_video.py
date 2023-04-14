from dataclasses import dataclass
from pathlib import Path
import cv2
import os
import numpy as np
import torch

from monai.data.video_dataset import VideoFileDataset
from monai.visualize.utils import blend_images

from surg_seg.Datasets.VideoDatasets import CombinedVidDataset

# from surg_seg.Datasets.ImageDataset import ImageDataset

from surg_seg.Networks.Models import FlexibleUnet1InferencePipe, AbstractInferencePipe


@dataclass
class VideoCreator:
    fps: float

    def __post_init__(self):
        self.get_codec()
        self.fourcc = cv2.VideoWriter_fourcc(*self.codec)

    def create_video(
        self,
        model_pipe: AbstractInferencePipe,
        output_file,
        ds: CombinedVidDataset,
        check_codec=True,
    ):
        if check_codec:
            self.check_codec

        print(f"{len(ds)} frames @ {self.fps} fps: {output_file}...")

        for idx in range(len(ds)):
            img = ds[idx]["image"]
            inferred_single_ch = model_pipe.infer(img)
            blended = blend_images(img, inferred_single_ch, cmap="viridis", alpha=0.8)

            if idx == 0:
                width_height = blended.shape[1:][::-1]
                video = cv2.VideoWriter(output_file, self.fourcc, self.fps, width_height)

            blended = (np.moveaxis(blended, 0, -1) * 254).astype(np.uint8)
            blended = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)
            video.write(blended)

        video.release()

        if not os.path.isfile(output_file):
            raise RuntimeError("video not created:", output_file)

        print("Success!")

    def get_codec(self):
        codecs = VideoFileDataset.get_available_codecs()
        self.codec, self.ext = next(iter(codecs.items()))
        print(self.codec, self.ext)

    def check_codec(self):
        codec_success = cv2.VideoWriter().open("test" + self.ext, self.fourcc, 1, (10, 10))
        if not codec_success:
            raise RuntimeError("failed to open video.")
        os.remove("test" + self.ext)


def main():

    device = "cuda"
    # path_to_weights = Path("./assets/weights/myweights_image_all_datasets/myweights.pt")
    path_to_weights = Path("assets/weights/myweights_3d_med_2_all_ds3/myweights.pt")
    model_pipe = FlexibleUnet1InferencePipe(path_to_weights, device, out_channels=5)

    ## Data loading
    rec_num = 1
    vid_root = Path(
        f"/home/juan1995/research_juan/accelnet_grant/data/phantom2_data_processed/rec{rec_num:02d}/"
    )
    vid_filepath = vid_root / f"raw/rec{rec_num:02d}_seg_raw.avi"
    seg_filepath = vid_root / f"annotation2colors/rec{rec_num:02d}_seg_annotation2colors.avi"

    ds = CombinedVidDataset(vid_filepath, seg_filepath)

    output_path = vid_root / "inferred.mp4"

    # create video
    fps = ds.ds_img.get_fps()
    print(f"fps {fps}")
    video_creator = VideoCreator(fps)

    with torch.no_grad():
        video_creator.create_video(model_pipe, str(output_path), ds)


if __name__ == "__main__":
    main()
