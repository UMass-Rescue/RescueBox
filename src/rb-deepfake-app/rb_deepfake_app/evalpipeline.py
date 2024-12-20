import os
import pandas as pd
import torch
from typing import List, Optional
from os.path import join
from video_evaluator import VideoEvaluator

def find_video_files(search_path: str, extensions: Optional[List[str]] = None) -> List[str]:
    """Recursively search for video files in the given directory."""
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v', '.mpg', '.mpeg']

    video_files = []
    for root, _, files in os.walk(search_path):
        video_files.extend(
            os.path.abspath(os.path.join(root, f))
            for f in files if any(f.lower().endswith(ext) for ext in extensions)
        )
    return video_files

def run_detection(video_paths: List[str], 
                  output_path: str = './detection_results', 
                  cuda: bool = False) -> pd.DataFrame:
    """
    Process a list of videos and generate detection results.
    
    Args:
        video_paths (List[str]): List of paths to video files
        output_path (str): Path to save output results
        cuda (bool): Whether to use CUDA acceleration
    
    Returns:
        pd.DataFrame: DataFrame with detection results
    """

    # Initialize results list
    results = []
    
    # Initialize video evaluator
    video_evaluator = VideoEvaluator(model_path='weights/xception-b5690688.pth',output_path=output_path, cuda=cuda)
    
    # Process each video
    for video_path in video_paths:
        try:
            # Evaluate video and get results
            result = video_evaluator.evaluate_video(video_path, output_mode='json', verbose=False)
            
            # Compile result
            results.append({
                'video_path': video_path,
                'final_label': result['final_label'],
                'frames_analyzed': result['frames_analyzed'],
                'frames_with_faces': result['frames_with_faces'],
                'confidence_real': result['confidence_scores']['real'],
                'confidence_fake': result['confidence_scores']['fake'],
                'average_prediction': result['average_prediction']
            })
        
        except Exception as e:
            print(f"Error processing {video_path}: {e}")
            results.append({
                'video_path': video_path,
                'final_label': 'error',
                'frames_analyzed': 0,
                'frames_with_faces': 0,
                'confidence_real': 0,
                'confidence_fake': 0,
                'average_prediction': 0
            })
    
    # Convert to DataFrame
    return pd.DataFrame(results)

def process_video_directory(search_path: str, output_csv: Optional[str] = None) -> pd.DataFrame:
    """Process videos in the specified directory and save results."""
    video_paths = find_video_files(search_path)
    print(f"Found {len(video_paths)} video files in {search_path}")

    # Use CUDA if available
    cuda = torch.cuda.is_available()
    
    # Generate results
    results_df = run_detection(video_paths, cuda=cuda)
    
    # Save to CSV if output path provided
    if output_csv:
        results_df.to_csv(output_csv, index=False)
        print(f"Results saved to {output_csv}")
    
    return results_df

def main():
    """Main entry point of the script."""
    search_directories = ['path/to/dataset', 'path/to/dataset']
    ctr = 0
    for search_directory in search_directories:
        # Process directory and save results
        output_csv = f'./deepfake_detection_results_{ctr}.csv'
        ctr+=1

        results_df = process_video_directory(search_directory, output_csv)
        
        # Display some basic information
        print("\nDetection Summary:")
        print(f"Total videos processed: {len(results_df)}")
        print(f"Videos with faces detected: {(results_df['frames_with_faces'] > 0).sum()}")
        print(f"Videos classified as fake: {(results_df['final_label'] == 'probably fake').sum()}")
        print(f"Videos classified as real: {(results_df['final_label'] == 'probably real').sum()}")

if __name__ == "__main__":
    main()