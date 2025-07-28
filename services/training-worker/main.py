"""
Training Worker Service

This service handles background training tasks for voice cloning models:
- Voice model training and fine-tuning
- Model evaluation and validation
- Training data management and preprocessing
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import json

from celery import Celery
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
celery_app = Celery(
    "training_worker",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=["training_worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour timeout
    task_soft_time_limit=3300,  # 55 minutes soft timeout
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    task_compression="gzip",
    result_compression="gzip",
)


class TrainingStatus(str, Enum):
    PENDING = "pending"
    STARTED = "started"
    PREPROCESSING = "preprocessing"
    TRAINING = "training"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrainingTask(BaseModel):
    task_id: str
    user_id: str
    model_name: str
    training_data_urls: List[str]
    config: Dict[str, Any]
    status: TrainingStatus = TrainingStatus.PENDING
    progress: int = 0
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    model_metrics: Optional[Dict[str, float]] = None


@celery_app.task(bind=True, name="training_worker.train_voice_model")
def train_voice_model(self, task_data: Dict[str, Any]):
    """
    Train a voice cloning model

    Args:
        task_data: Training task configuration and data
    """

    try:
        task = TrainingTask(**task_data)
        task.status = TrainingStatus.STARTED
        task.started_at = datetime.utcnow()

        logger.info(f"Starting voice model training: {task.task_id}")

        # Update task status
        self.update_state(
            state=TrainingStatus.STARTED,
            meta={"progress": 0, "status": "Training started", "current_step": "initializing"},
        )

        # Step 1: Preprocess training data
        task.status = TrainingStatus.PREPROCESSING
        self.update_state(
            state=TrainingStatus.PREPROCESSING,
            meta={
                "progress": 10,
                "status": "Preprocessing training data",
                "current_step": "preprocessing",
            },
        )

        processed_data = preprocess_training_data(task.training_data_urls, task.config)

        # Step 2: Initialize training
        self.update_state(
            state=TrainingStatus.TRAINING,
            meta={
                "progress": 20,
                "status": "Initializing training",
                "current_step": "training_init",
            },
        )

        model_config = initialize_training_config(task.config)

        # Step 3: Train model (this would be the main training loop)
        task.status = TrainingStatus.TRAINING

        for epoch in range(model_config.get("epochs", 100)):
            # Simulate training progress
            progress = 20 + (epoch / model_config.get("epochs", 100)) * 60

            self.update_state(
                state=TrainingStatus.TRAINING,
                meta={
                    "progress": int(progress),
                    "status": f"Training epoch {epoch + 1}/{model_config.get('epochs', 100)}",
                    "current_step": "training",
                    "epoch": epoch + 1,
                    "total_epochs": model_config.get("epochs", 100),
                },
            )

            # Simulate training step
            train_step_result = simulate_training_step(processed_data, model_config, epoch)

            # Check for early stopping or cancellation
            if self.is_aborted():
                task.status = TrainingStatus.CANCELLED
                raise Exception("Training cancelled by user")

        # Step 4: Evaluate model
        task.status = TrainingStatus.EVALUATING
        self.update_state(
            state=TrainingStatus.EVALUATING,
            meta={
                "progress": 85,
                "status": "Evaluating trained model",
                "current_step": "evaluation",
            },
        )

        evaluation_metrics = evaluate_trained_model(processed_data, model_config)
        task.model_metrics = evaluation_metrics

        # Step 5: Save and finalize model
        self.update_state(
            state=TrainingStatus.COMPLETED,
            meta={"progress": 95, "status": "Saving trained model", "current_step": "saving"},
        )

        model_path = save_trained_model(task.model_name, model_config, evaluation_metrics)

        # Complete training
        task.status = TrainingStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.progress = 100

        logger.info(f"Training completed successfully: {task.task_id}")

        return {
            "status": "completed",
            "task_id": task.task_id,
            "model_path": model_path,
            "metrics": evaluation_metrics,
            "training_time": (task.completed_at - task.started_at).total_seconds(),
            "progress": 100,
        }

    except Exception as e:
        logger.error(f"Training failed for task {task_data.get('task_id', 'unknown')}: {str(e)}")

        task.status = TrainingStatus.FAILED
        task.error_message = str(e)
        task.completed_at = datetime.utcnow()

        self.update_state(
            state=TrainingStatus.FAILED,
            meta={"progress": task.progress, "status": "Training failed", "error": str(e)},
        )

        raise


@celery_app.task(name="training_worker.evaluate_model")
def evaluate_model(model_path: str, test_data_urls: List[str]) -> Dict[str, float]:
    """
    Evaluate a trained model against test data

    Args:
        model_path: Path to the trained model
        test_data_urls: URLs to test data

    Returns:
        Evaluation metrics
    """

    try:
        logger.info(f"Starting model evaluation: {model_path}")

        # Load test data
        test_data = load_test_data(test_data_urls)

        # Load trained model
        model = load_trained_model(model_path)

        # Run evaluation
        metrics = run_model_evaluation(model, test_data)

        logger.info(f"Model evaluation completed: {metrics}")

        return metrics

    except Exception as e:
        logger.error(f"Model evaluation failed: {str(e)}")
        raise


@celery_app.task(name="training_worker.cleanup_training_data")
def cleanup_training_data(task_id: str, keep_model: bool = True):
    """
    Clean up temporary training data and artifacts

    Args:
        task_id: Training task ID
        keep_model: Whether to keep the trained model
    """

    try:
        logger.info(f"Cleaning up training data for task: {task_id}")

        # Remove temporary files
        cleanup_temp_files(task_id)

        # Remove training data if not needed
        if not keep_model:
            remove_training_artifacts(task_id)

        logger.info(f"Cleanup completed for task: {task_id}")

    except Exception as e:
        logger.error(f"Cleanup failed for task {task_id}: {str(e)}")
        raise


def preprocess_training_data(data_urls: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """Preprocess training data for model training"""

    logger.info(f"Preprocessing {len(data_urls)} training files")

    # Placeholder - would implement actual data preprocessing
    processed_data = {
        "audio_files": data_urls,
        "sample_rate": config.get("sample_rate", 22050),
        "duration_total": len(data_urls) * 30,  # Assume 30s per file
        "preprocessing_config": config,
    }

    return processed_data


def initialize_training_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize training configuration"""

    default_config = {
        "epochs": 100,
        "batch_size": 32,
        "learning_rate": 0.001,
        "model_architecture": "tacotron2",
        "optimizer": "adam",
        "loss_function": "mse",
    }

    # Merge with user config
    training_config = {**default_config, **config}

    logger.info(f"Training configuration: {training_config}")

    return training_config


def simulate_training_step(
    data: Dict[str, Any], config: Dict[str, Any], epoch: int
) -> Dict[str, float]:
    """Simulate a training step"""

    # Simulate training metrics
    import random

    loss = max(0.1, 2.0 - epoch * 0.018 + random.uniform(-0.1, 0.1))
    accuracy = min(0.99, epoch * 0.009 + random.uniform(-0.02, 0.02))

    return {"loss": loss, "accuracy": accuracy, "epoch": epoch}


def evaluate_trained_model(data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, float]:
    """Evaluate the trained model"""

    # Placeholder evaluation metrics
    metrics = {
        "mel_cepstral_distortion": 4.2,
        "voice_similarity_score": 0.89,
        "naturalness_score": 4.3,
        "intelligibility_score": 4.7,
        "overall_quality": 4.2,
    }

    logger.info(f"Model evaluation metrics: {metrics}")

    return metrics


def save_trained_model(model_name: str, config: Dict[str, Any], metrics: Dict[str, float]) -> str:
    """Save the trained model"""

    model_path = f"/models/{model_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    # Create model directory
    os.makedirs(model_path, exist_ok=True)

    # Save model metadata
    metadata = {
        "model_name": model_name,
        "training_config": config,
        "evaluation_metrics": metrics,
        "created_at": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }

    with open(f"{model_path}/metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Model saved to: {model_path}")

    return model_path


def load_trained_model(model_path: str):
    """Load a trained model"""

    # Placeholder - would load actual model
    logger.info(f"Loading model from: {model_path}")
    return {"model_path": model_path, "loaded": True}


def load_test_data(test_data_urls: List[str]) -> Dict[str, Any]:
    """Load test data for evaluation"""

    # Placeholder - would load actual test data
    return {"test_files": test_data_urls, "loaded": True}


def run_model_evaluation(model, test_data: Dict[str, Any]) -> Dict[str, float]:
    """Run model evaluation against test data"""

    # Placeholder evaluation
    return {"test_loss": 0.25, "test_accuracy": 0.92, "inference_time": 0.15}


def cleanup_temp_files(task_id: str):
    """Clean up temporary files for a training task"""

    temp_dir = f"/tmp/training_{task_id}"
    if os.path.exists(temp_dir):
        import shutil

        shutil.rmtree(temp_dir)
        logger.info(f"Removed temporary directory: {temp_dir}")


def remove_training_artifacts(task_id: str):
    """Remove training artifacts if model is not needed"""

    # Placeholder - would remove training artifacts
    logger.info(f"Removing training artifacts for task: {task_id}")


if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()
