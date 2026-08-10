import pytest
from src.ml_core.pipeline import TrainingPipeline, TrainingResult


def test_pipeline_run_with_tracker(mocker, dummy_config):
    """Pipeline.run() 應整合 tracker 進行追蹤並回傳 TrainingResult。"""
    mock_loader = mocker.Mock()
    mock_preprocessor = mocker.Mock()
    mock_trainer = mocker.Mock()
    mock_tracker = mocker.Mock()

    mock_preprocessor.fit_transform.return_value = (
        mocker.Mock(),
        mocker.Mock(),
    )
    mock_trainer.fit.return_value = {"accuracy": 0.9}
    mock_tracker.start_run.return_value = "test-run-id"
    mock_tracker.log_model.return_value = "models:/test/1"

    pipeline = TrainingPipeline(
        config=dummy_config,
        loader=mock_loader,
        preprocessor=mock_preprocessor,
        trainer=mock_trainer,
        tracker=mock_tracker,
    )
    result = pipeline.run()

    # 驗證結果型別
    assert isinstance(result, TrainingResult)
    assert result.run_id == "test-run-id"
    assert result.metrics == {"accuracy": 0.9}

    # 驗證元件呼叫順序
    mock_tracker.start_run.assert_called_once()
    mock_loader.fetch.assert_called_once_with(dummy_config.data_path)
    mock_preprocessor.fit_transform.assert_called_once()
    mock_trainer.fit.assert_called_once()
    mock_tracker.log_params.assert_called_once()
    mock_tracker.log_metrics.assert_called_once_with({"accuracy": 0.9})
    mock_tracker.end_run.assert_called_once()


def test_pipeline_run_ensures_end_run_on_error(mocker, dummy_config):
    """即使訓練過程出錯，tracker.end_run() 仍必須被呼叫。"""
    mock_loader = mocker.Mock()
    mock_loader.fetch.side_effect = Exception("data error")
    mock_preprocessor = mocker.Mock()
    mock_trainer = mocker.Mock()
    mock_tracker = mocker.Mock()
    mock_tracker.start_run.return_value = "fail-run-id"

    pipeline = TrainingPipeline(
        config=dummy_config,
        loader=mock_loader,
        preprocessor=mock_preprocessor,
        trainer=mock_trainer,
        tracker=mock_tracker,
    )

    with pytest.raises(Exception, match="data error"):
        pipeline.run()

    mock_tracker.end_run.assert_called_once()


def test_pipeline_run_no_local_save_when_path_is_none(mocker, dummy_config):
    """model_save_path 為 None 時不應呼叫 trainer.save()。"""
    mock_loader = mocker.Mock()
    mock_preprocessor = mocker.Mock()
    mock_trainer = mocker.Mock()
    mock_tracker = mocker.Mock()

    mock_preprocessor.fit_transform.return_value = (
        mocker.Mock(),
        mocker.Mock(),
    )
    mock_trainer.fit.return_value = {"accuracy": 0.9}
    mock_tracker.start_run.return_value = "test-run-id"
    mock_tracker.log_model.return_value = "models:/test/1"

    pipeline = TrainingPipeline(
        config=dummy_config,
        loader=mock_loader,
        preprocessor=mock_preprocessor,
        trainer=mock_trainer,
        tracker=mock_tracker,
    )
    pipeline.run()

    # model_save_path is None，不應呼叫 save
    mock_trainer.save.assert_not_called()
