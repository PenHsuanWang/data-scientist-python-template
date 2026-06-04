import pytest
from src.ml_core.pipeline import TrainingPipeline
from src.ml_core.config import ProjectConfig


@pytest.fixture
def dummy_config(mock_data_path, mock_model_path):
    return ProjectConfig(data_path=mock_data_path, model_save_path=mock_model_path)


def test_pipeline_run(mocker, dummy_config):
    mock_loader = mocker.Mock()
    mock_preprocessor = mocker.Mock()
    mock_trainer = mocker.Mock()

    mock_preprocessor.fit_transform.return_value = (mocker.Mock(), mocker.Mock())
    mock_trainer.fit.return_value = {"accuracy": 0.9}

    pipeline = TrainingPipeline(
        dummy_config, mock_loader, mock_preprocessor, mock_trainer
    )
    pipeline.run()

    mock_loader.fetch.assert_called_once_with(dummy_config.data_path)
    mock_preprocessor.fit_transform.assert_called_once()
    mock_trainer.fit.assert_called_once()
    mock_trainer.save.assert_called_once_with(dummy_config.model_save_path)
