import kagglehub
import os

os.environ['KAGGLE_CONFIG_DIR'] = os.path.expanduser("~/.kaggle")

path = kagglehub.dataset_download("amitanshjoshi/spotify-1million-tracks")
print("Path to dataset files:", path)
