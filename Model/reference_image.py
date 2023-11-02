from torchvision import transforms
from torchvision import models
import torch
from PIL import Image
import torch.nn as nn
import io
import numpy as np

# The following code was used to exmine what a transformed image looks like as it is sent for training or inference

def input_fn(file_name):
    image_data = Image.open(file_name, mode='r')       
    image_data = image_data.convert('RGB')
    mode_to_nptype = {'I': np.int32, 'I;16': np.int16, 'F': np.float32}
    img = torch.from_numpy(
        np.array(image_data, mode_to_nptype.get(image_data.mode, np.uint8), copy=True)
    )
    image_transform = transforms.Compose([
        transforms.Resize(size=480),
        transforms.CenterCrop(size=480),
        transforms.ToTensor()
        #transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    return image_transform(image_data)
    
def save_processed_tensor_image(tensor):
    transform = transforms.ToPILImage()

    # convert the tensor to PIL image using above transform
    img = transform(tensor)
    print(type(img))

    img.show()
    #img.save(filename)
def main():
    #transform = input_fn('//images-for-training/train/NoFight/11-31-22.559346.jpg')
    transform = input_fn('/extra/Fight/Fight_1.jpg')
    save_processed_tensor_image(transform)


if __name__ == '__main__':
    main()
    
    
