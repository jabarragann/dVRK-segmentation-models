from pathlib import Path
from autonomy_utils.ambf_utils import ImageSaver
import cv2
import torch
import numpy as np

from monai.visualize.utils import blend_images
from surg_seg.Networks.Models import FlexibleUnet1InferencePipe
from surg_seg.Datasets.ImageDataset import ImageTransforms


def main():

    image_saver = ImageSaver()

    device = "cuda"
    path_to_weights = Path("./assets/weights/myweights_image_all_datasets/myweights.pt")
    model_pipe = FlexibleUnet1InferencePipe(path_to_weights, device, out_channels=5)

    while True:
        frame = image_saver.get_current_frame("left")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        tensor = ImageTransforms.img_transforms(frame).to(device)
        tensor = torch.unsqueeze(tensor, 0)  # Add batch dimension. 4D tensor

        inferred = model_pipe.model(tensor)[0]  # go back to 3D tensor
        inferred = inferred.argmax(dim=0, keepdim=True)

        inferred = inferred.detach().cpu()
        tensor = tensor.detach().cpu()[0]

        blended = blend_images(tensor, inferred, cmap="viridis", alpha=0.8).numpy()
        blended = (np.transpose(blended, (1, 2, 0)) * 254).astype(np.uint8)
        blended = cv2.cvtColor(blended, cv2.COLOR_RGB2BGR)

        cv2.imshow("image", blended)

        if cv2.waitKey(30) & 0xFF == ord("q"):
            cv2.destroyAllWindows()
            break


if __name__ == "__main__":

    with torch.no_grad():
        main()