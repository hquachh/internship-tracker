"""
Main entry point for the Internship Tracker application.

This script orchestrates the complete workflow:
1. First run: Setup authentication, build training data, train model
2. Regular runs: Fetch new emails, classify, and update Google Sheets

    python run.py --setup          # first time setup
    python run.py --update         # regular update (fetch + classify + update sheets)
    python run.py --train          # retrain model with new data
    python run.py --help           # show help
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

def setup_first_run():
    # complete first-time setup -- authentication only, model is pre-trained
    print("Starting first-time setup...")

    try:
        # authentication
        print("Setting up Gmail authentication...")
        from src.scraping.authenticate_gmail import authenticate
        authenticate()

        print("Setup complete! The pre-trained model is ready to use.")
        print("Run 'python run.py --update' to start tracking applications.")

    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

def update_applications():
    # regular workflow - fetch emails, classify, update sheets
    print("Fetching and processing new applications...")

    try:
        # main prediction and update workflow
        from src.prediction.predict import predict_and_update
        predict_and_update()

        print("Applications updated successfully!")

    except Exception as e:
        print(f"L Update failed: {e}")
        sys.exit(1)

def retrain_model():
    # retrain the model with updated training data
    print("Retraining model...")

    try:
        # rebuild dataset with any new labeled data
        from src.preprocessing.build_dataset import build_training_dataset
        build_training_dataset()

        # retrain model
        from src.training.train import train_model
        train_model()

        print("Model retrained successfully!")

    except Exception as e:
        print(f"Retraining failed: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Internship Tracker - Automatically track job applications from Gmail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py --setup     # First time setup (authentication)
  python run.py --update    # Regular update (recommended for daily use)
  python run.py --retrain   # Retrain model with your starred emails
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--setup', action='store_true',
                      help='First-time setup: authenticate Gmail and Google Sheets')
    group.add_argument('--update', action='store_true',
                      help='Regular update: fetch new emails, classify, update Google Sheets')
    group.add_argument('--retrain', action='store_true',
                      help='Retrain the model with your starred emails for better accuracy')

    args = parser.parse_args()

    if args.setup:
        setup_first_run()
    elif args.update:
        update_applications()
    elif args.retrain:
        retrain_model()

if __name__ == "__main__":
    main()