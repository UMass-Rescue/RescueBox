import { AppMetadata } from '../generated_models';

const isrAppMetadata: AppMetadata = {
  name: 'Image Super Resolution',
  info: `
# Image Super Resolution
This model upscales low-resolution images to higher resolutions, improving the clarity and detail of the images.

### Inputs
- **Low Resolution Images**: Upload images in **.png**, **.jpg**, or **.jpeg** format.

### Outputs
- **High Resolution Images**: The processed images with enhanced resolution.

### Parameters
- **Scale**: The factor by which the image resolution is increased. Acceptable values are between 1.0 and 4.0.
- **Model Weights**: Choose from the following model weights for different enhancement techniques:
  | Weights       | Description |
  |---------------|-------------|
  | gans          | Uses Generative Adversarial Networks for high-quality image enhancement. |
  | psnr-small    | Optimized for Peak Signal-to-Noise Ratio with smaller model size. |
  | psnr-large    | Optimized for Peak Signal-to-Noise Ratio with larger model size for better quality. |
  | noise-cancel  | Reduces noise in the images while enhancing resolution. |

### Constraints
- The image must be in .png, .jpg, or .jpeg format.
`,
  author: 'Mr Bob',
  version: '1.0.0',
};

export default isrAppMetadata;
