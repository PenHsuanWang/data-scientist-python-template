"""
CreateTrainingJob Use Case — Application 測試 (SDD §66)。

使用 Fake/Stub Port，驗證：
Command → Use Case → Domain Rule → State Change → Event
"""

import pytest

from src.ml_platform.application.training.commands import (
    CancelTrainingCommand,
    CompleteTrainingCommand,
    CreateTrainingJobCommand,
    FailTrainingCommand,
    StartTrainingCommand,
)
from src.ml_platform.application.training.use_cases import (
    CancelTrainingUseCase,
    CompleteTrainingUseCase,
    CreateTrainingJobUseCase,
    FailTrainingUseCase,
    StartTrainingUseCase,
)
from src.ml_platform.domain.training.events import (
    TrainingCancelled,
    TrainingCompleted,
    TrainingFailed,
    TrainingJobCreated,
    TrainingStarted,
)
from src.ml_platform.domain.training.exceptions import (
    TrainingJobNotFoundError,
)
from src.ml_platform.domain.training.training_job import JobStatus

from tests.conftest import FakeEventPublisher, FakeTrainingJobRepository


@pytest.fixture()
def repo() -> FakeTrainingJobRepository:
    """Fake repository。"""
    return FakeTrainingJobRepository()


@pytest.fixture()
def publisher() -> FakeEventPublisher:
    """Fake event publisher。"""
    return FakeEventPublisher()


class TestCreateTrainingJobUseCase:
    """建立 Training Job Use Case 測試。"""

    @pytest.mark.asyncio()
    async def test_creates_job_and_persists(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """應建立 Job、存入 Repository、發佈事件。"""
        use_case = CreateTrainingJobUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        command = CreateTrainingJobCommand(
            dataset_id="ds-001",
            experiment_name="exp-1",
            learning_rate=0.05,
        )

        job = await use_case.execute(command)

        # Job persisted
        stored = await repo.get(job.id)
        assert stored is not None
        assert stored.status == JobStatus.CREATED
        assert stored.config.dataset_id == "ds-001"
        assert stored.config.hyper_parameters.learning_rate == 0.05

        # Event published
        assert len(publisher.published_events) == 1
        assert isinstance(
            publisher.published_events[0],
            TrainingJobCreated,
        )


class TestStartTrainingUseCase:
    """開始 Training Use Case 測試。"""

    @pytest.mark.asyncio()
    async def test_starts_job_and_creates_run(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """應將 Job 從 CREATED 推進到 RUNNING 並建立 Run。"""
        # Arrange: create job first
        create_uc = CreateTrainingJobUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await create_uc.execute(
            CreateTrainingJobCommand(dataset_id="ds-001"),
        )

        # Act
        start_uc = StartTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        updated = await start_uc.execute(
            StartTrainingCommand(job_id=str(job.id)),
        )

        assert updated.status == JobStatus.RUNNING
        assert len(updated.runs) == 1
        assert updated.current_run is not None

        # Events: Created + Started
        started_events = [
            e for e in publisher.published_events if isinstance(e, TrainingStarted)
        ]
        assert len(started_events) == 1

    @pytest.mark.asyncio()
    async def test_start_nonexistent_job_raises(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """不存在的 Job 應拋出 TrainingJobNotFoundError。"""
        use_case = StartTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )

        with pytest.raises(TrainingJobNotFoundError):
            await use_case.execute(
                StartTrainingCommand(
                    job_id="00000000-0000-0000-0000-000000000000",
                ),
            )


class TestCompleteTrainingUseCase:
    """完成 Training Use Case 測試。"""

    @pytest.mark.asyncio()
    async def test_completes_job(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """應將 RUNNING Job 標記為 COMPLETED。"""
        # Arrange
        create_uc = CreateTrainingJobUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await create_uc.execute(
            CreateTrainingJobCommand(dataset_id="ds-001"),
        )
        start_uc = StartTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await start_uc.execute(
            StartTrainingCommand(job_id=str(job.id)),
        )

        # Act
        complete_uc = CompleteTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await complete_uc.execute(
            CompleteTrainingCommand(
                job_id=str(job.id),
                run_id=str(job.current_run.id),
                metrics={"accuracy": 0.95},
                artifact_uri="s3://models/v1",
            ),
        )

        assert job.status == JobStatus.COMPLETED
        assert job.current_run.artifact_uri == "s3://models/v1"

        completed_events = [
            e for e in publisher.published_events if isinstance(e, TrainingCompleted)
        ]
        assert len(completed_events) == 1
        assert completed_events[0].metrics["accuracy"] == 0.95


class TestFailTrainingUseCase:
    """失敗 Training Use Case 測試。"""

    @pytest.mark.asyncio()
    async def test_fails_job(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """應將 RUNNING Job 標記為 FAILED。"""
        create_uc = CreateTrainingJobUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await create_uc.execute(
            CreateTrainingJobCommand(dataset_id="ds-001"),
        )
        start_uc = StartTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await start_uc.execute(
            StartTrainingCommand(job_id=str(job.id)),
        )

        fail_uc = FailTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await fail_uc.execute(
            FailTrainingCommand(
                job_id=str(job.id),
                run_id=str(job.current_run.id),
                error_message="OOM",
            ),
        )

        assert job.status == JobStatus.FAILED
        assert job.current_run.error_message == "OOM"

        failed_events = [
            e for e in publisher.published_events if isinstance(e, TrainingFailed)
        ]
        assert len(failed_events) == 1


class TestCancelTrainingUseCase:
    """取消 Training Use Case 測試。"""

    @pytest.mark.asyncio()
    async def test_cancels_created_job(
        self,
        repo: FakeTrainingJobRepository,
        publisher: FakeEventPublisher,
    ) -> None:
        """應能取消 CREATED 狀態的 Job。"""
        create_uc = CreateTrainingJobUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await create_uc.execute(
            CreateTrainingJobCommand(dataset_id="ds-001"),
        )

        cancel_uc = CancelTrainingUseCase(
            repository=repo,
            event_publisher=publisher,
        )
        job = await cancel_uc.execute(
            CancelTrainingCommand(
                job_id=str(job.id),
                reason="User cancelled",
            ),
        )

        assert job.status == JobStatus.CANCELLED

        cancelled_events = [
            e for e in publisher.published_events if isinstance(e, TrainingCancelled)
        ]
        assert len(cancelled_events) == 1
