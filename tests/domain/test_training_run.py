"""
TrainingRun Entity — Domain 測試 (SDD §65)。

測試 TrainingRun 的生命週期轉換。
"""

import pytest

from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.training_run import (
    RunStatus,
    TrainingRun,
)
from src.ml_platform.domain.training.value_objects import TrainingMetrics


@pytest.fixture()
def sample_run() -> TrainingRun:
    """建立標準 TrainingRun fixture。"""
    return TrainingRun.create(
        job_id=EntityId.generate(),
    )


class TestTrainingRunCreation:
    """TrainingRun.create() 測試。"""

    def test_create_sets_pending_status(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """新建 Run 狀態應為 PENDING。"""
        assert sample_run.status == RunStatus.PENDING
        assert sample_run.started_at is None
        assert sample_run.completed_at is None

    def test_create_assigns_unique_id(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """每次建立應有唯一 ID。"""
        another = TrainingRun.create(job_id=sample_run.job_id)
        assert sample_run.id != another.id


class TestTrainingRunTransitions:
    """TrainingRun 狀態轉換測試。"""

    def test_pending_to_running(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """PENDING → RUNNING。"""
        sample_run.mark_running()
        assert sample_run.status == RunStatus.RUNNING
        assert sample_run.started_at is not None

    def test_running_to_completed(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """RUNNING → COMPLETED。"""
        sample_run.mark_running()
        metrics = TrainingMetrics(values={"accuracy": 0.9})
        sample_run.mark_completed(
            metrics=metrics,
            artifact_uri="s3://model",
        )

        assert sample_run.status == RunStatus.COMPLETED
        assert sample_run.metrics.values["accuracy"] == 0.9
        assert sample_run.artifact_uri == "s3://model"
        assert sample_run.completed_at is not None

    def test_running_to_failed(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """RUNNING → FAILED。"""
        sample_run.mark_running()
        sample_run.mark_failed("OOM kill")

        assert sample_run.status == RunStatus.FAILED
        assert sample_run.error_message == "OOM kill"
        assert sample_run.completed_at is not None

    def test_pending_to_cancelled(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """PENDING → CANCELLED。"""
        sample_run.mark_cancelled()
        assert sample_run.status == RunStatus.CANCELLED

    def test_running_to_cancelled(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """RUNNING → CANCELLED。"""
        sample_run.mark_running()
        sample_run.mark_cancelled()
        assert sample_run.status == RunStatus.CANCELLED


class TestTrainingRunInvariants:
    """TrainingRun 不變量測試。"""

    def test_cannot_start_completed_run(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """COMPLETED 不能回到 RUNNING。"""
        sample_run.mark_running()
        sample_run.mark_completed(metrics=TrainingMetrics())

        with pytest.raises(ValueError, match="Cannot start run"):
            sample_run.mark_running()

    def test_cannot_complete_pending_run(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """PENDING 不能直接 COMPLETED。"""
        with pytest.raises(ValueError, match="Cannot complete run"):
            sample_run.mark_completed(metrics=TrainingMetrics())

    def test_cannot_fail_pending_run(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """PENDING 不能直接 FAILED。"""
        with pytest.raises(ValueError, match="Cannot fail run"):
            sample_run.mark_failed("error")

    def test_cannot_cancel_completed_run(
        self,
        sample_run: TrainingRun,
    ) -> None:
        """COMPLETED 不能取消。"""
        sample_run.mark_running()
        sample_run.mark_completed(metrics=TrainingMetrics())

        with pytest.raises(ValueError, match="Cannot cancel run"):
            sample_run.mark_cancelled()
