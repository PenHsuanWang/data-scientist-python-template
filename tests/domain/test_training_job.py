"""
TrainingJob Aggregate Root — Domain 測試 (SDD §65)。

純 in-memory 測試，不啟動 PostgreSQL / Kafka / FastAPI。
驗證 State Machine 轉換 (SDD §32-33) 與 Domain Event 產生。
"""

import pytest

from src.ml_platform.domain.training.events import (
    TrainingCompleted,
    TrainingJobCreated,
    TrainingStarted,
)
from src.ml_platform.domain.training.exceptions import (
    InvalidStateTransitionError,
)
from src.ml_platform.domain.training.training_job import (
    JobStatus,
    TrainingJob,
)
from src.ml_platform.domain.training.value_objects import (
    HyperParameters,
    TrainingConfig,
    TrainingMetrics,
)


@pytest.fixture()
def sample_config() -> TrainingConfig:
    """標準訓練設定 fixture。"""
    return TrainingConfig(
        dataset_id="dataset-001",
        experiment_name="test-experiment",
        hyper_parameters=HyperParameters(
            learning_rate=0.01,
            random_state=42,
        ),
    )


class TestTrainingJobCreation:
    """TrainingJob.create() 工廠方法測試。"""

    def test_create_sets_status_to_created(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """建立後狀態應為 CREATED。"""
        job = TrainingJob.create(config=sample_config)

        assert job.status == JobStatus.CREATED
        assert job.config.dataset_id == "dataset-001"
        assert len(job.runs) == 0

    def test_create_produces_training_job_created_event(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """建立時應產生 TrainingJobCreated 事件。"""
        job = TrainingJob.create(config=sample_config)
        events = job.collect_events()

        assert len(events) == 1
        assert isinstance(events[0], TrainingJobCreated)
        assert events[0].aggregate_id == str(job.id)
        assert events[0].dataset_id == "dataset-001"
        assert events[0].event_type == "ml.training.job.created.v1"

    def test_collect_events_clears_pending(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """collect_events 後待發佈事件應被清空。"""
        job = TrainingJob.create(config=sample_config)
        _ = job.collect_events()
        assert len(job.collect_events()) == 0


class TestTrainingJobStateTransitions:
    """TrainingJob 狀態機轉換測試 (SDD §32)。"""

    def test_created_to_queued(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """CREATED → QUEUED。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        assert job.status == JobStatus.QUEUED

    def test_queued_to_running_creates_run(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """QUEUED → RUNNING，同時建立 TrainingRun。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        run = job.start()

        assert job.status == JobStatus.RUNNING
        assert len(job.runs) == 1
        assert run.status.value == "RUNNING"
        assert job.current_run is run

    def test_running_to_completed(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """RUNNING → COMPLETED。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        run = job.start()

        metrics = TrainingMetrics(values={"accuracy": 0.95, "loss": 0.05})
        job.complete(run=run, metrics=metrics, artifact_uri="s3://models/v1")

        assert job.status == JobStatus.COMPLETED
        assert run.status.value == "COMPLETED"
        assert run.metrics.values["accuracy"] == 0.95
        assert run.artifact_uri == "s3://models/v1"

    def test_running_to_failed(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """RUNNING → FAILED。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        run = job.start()

        job.fail(run=run, error_message="OOM")

        assert job.status == JobStatus.FAILED
        assert run.status.value == "FAILED"
        assert run.error_message == "OOM"

    def test_cancel_from_created(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """CREATED → CANCELLED。"""
        job = TrainingJob.create(config=sample_config)
        job.cancel()
        assert job.status == JobStatus.CANCELLED

    def test_cancel_from_queued(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """QUEUED → CANCELLED。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        job.cancel()
        assert job.status == JobStatus.CANCELLED

    def test_cancel_from_running(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """RUNNING → CANCELLING → CANCELLED。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        _ = job.start()
        job.cancel()

        assert job.status == JobStatus.CANCELLED
        # 進行中的 Run 也應被取消
        assert job.runs[0].status.value == "CANCELLED"

    def test_completed_events_chain(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """完整流程應產生 Created → Started → Completed 事件。"""
        job = TrainingJob.create(config=sample_config)
        _ = job.collect_events()  # clear creation event

        job.enqueue()
        run = job.start()
        metrics = TrainingMetrics(values={"accuracy": 0.95})
        job.complete(run=run, metrics=metrics)

        events = job.collect_events()
        assert len(events) == 2
        assert isinstance(events[0], TrainingStarted)
        assert isinstance(events[1], TrainingCompleted)
        assert events[1].metrics == {"accuracy": 0.95}


class TestTrainingJobInvariants:
    """TrainingJob 不變量測試 (SDD §33)。"""

    def test_completed_cannot_go_to_running(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """SDD §33.1: COMPLETED 不可回到 RUNNING。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        run = job.start()
        job.complete(run=run, metrics=TrainingMetrics())

        with pytest.raises(InvalidStateTransitionError):
            job.start()

    def test_cancelled_cannot_go_to_running(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """SDD §33.2: CANCELLED 不可直接變成 RUNNING。"""
        job = TrainingJob.create(config=sample_config)
        job.cancel()

        with pytest.raises(InvalidStateTransitionError):
            job.start()

    def test_failed_is_terminal(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """FAILED 為終端狀態。"""
        job = TrainingJob.create(config=sample_config)
        job.enqueue()
        run = job.start()
        job.fail(run=run, error_message="error")

        assert job.is_terminal
        with pytest.raises(InvalidStateTransitionError):
            job.enqueue()

    def test_double_cancel_on_terminal(
        self,
        sample_config: TrainingConfig,
    ) -> None:
        """已取消的 Job 不能再次取消。"""
        job = TrainingJob.create(config=sample_config)
        job.cancel()

        with pytest.raises(InvalidStateTransitionError):
            job.cancel()
