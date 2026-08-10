"""
Training Context — Application Use Cases (SDD §60)。

Use Case 協調 Domain 操作與 Port 互動：

.. code-block:: text

    Command → Use Case → Domain → Repository / Port → Event

Application Layer 不應包含 HTTP、Database、Kafka 等特定邏輯。
"""

from __future__ import annotations

import logging

from src.ml_platform.application.training.commands import (
    CancelTrainingCommand,
    CompleteTrainingCommand,
    CreateTrainingJobCommand,
    FailTrainingCommand,
    StartTrainingCommand,
)
from src.ml_platform.domain.shared.entity_id import EntityId
from src.ml_platform.domain.training.exceptions import (
    TrainingJobNotFoundError,
)
from src.ml_platform.domain.training.training_job import TrainingJob
from src.ml_platform.domain.training.value_objects import (
    HyperParameters,
    TrainingConfig,
    TrainingMetrics,
)
from src.ml_platform.ports.messaging.event_publisher import (
    EventPublisher,
)
from src.ml_platform.ports.repositories.training_repository import (
    TrainingJobRepository,
)

logger = logging.getLogger(__name__)


class CreateTrainingJobUseCase:
    """
    建立 Training Job 的 Use Case。

    協調：Command → Domain(create) → Repository(save) → EventPublisher(publish)

    :param repository: TrainingJob 持久化 Port。
    :param event_publisher: Domain Event 發佈 Port。
    """

    def __init__(
        self,
        repository: TrainingJobRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(
        self,
        command: CreateTrainingJobCommand,
    ) -> TrainingJob:
        """
        執行建立 TrainingJob 的業務邏輯。

        :param command: 建立 Training Job 的 Command。
        :return: 新建的 TrainingJob。
        """
        config = TrainingConfig(
            dataset_id=command.dataset_id,
            experiment_name=command.experiment_name,
            registered_model_name=command.registered_model_name,
            hyper_parameters=HyperParameters(
                learning_rate=command.learning_rate,
                random_state=command.random_state,
                extra=dict(command.extra_params),
            ),
        )

        job = TrainingJob.create(config=config)

        await self._repository.save(job)
        await self._event_publisher.publish_all(job.collect_events())

        logger.info(
            "TrainingJob created: job_id=%s, dataset_id=%s",
            job.id,
            config.dataset_id,
        )
        return job


class StartTrainingUseCase:
    """
    開始執行 Training 的 Use Case。

    :param repository: TrainingJob 持久化 Port。
    :param event_publisher: Domain Event 發佈 Port。
    """

    def __init__(
        self,
        repository: TrainingJobRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(self, command: StartTrainingCommand) -> TrainingJob:
        """
        將 TrainingJob 從 QUEUED 轉換到 RUNNING 並建立 Run。

        :param command: 開始訓練的 Command。
        :return: 更新後的 TrainingJob。
        :raises TrainingJobNotFoundError: 若 Job 不存在。
        """
        job_id = EntityId.from_string(command.job_id)
        job = await self._repository.get(job_id)
        if job is None:
            raise TrainingJobNotFoundError(command.job_id)

        job.enqueue()
        job.start()

        await self._repository.save(job)
        await self._event_publisher.publish_all(job.collect_events())

        logger.info("TrainingJob started: job_id=%s", job.id)
        return job


class CompleteTrainingUseCase:
    """
    標記 Training 完成的 Use Case (Worker 回報)。

    :param repository: TrainingJob 持久化 Port。
    :param event_publisher: Domain Event 發佈 Port。
    """

    def __init__(
        self,
        repository: TrainingJobRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(
        self,
        command: CompleteTrainingCommand,
    ) -> TrainingJob:
        """
        標記 TrainingJob 為完成。

        :param command: 完成訓練的 Command。
        :return: 更新後的 TrainingJob。
        :raises TrainingJobNotFoundError: 若 Job 不存在。
        """
        job_id = EntityId.from_string(command.job_id)
        job = await self._repository.get(job_id)
        if job is None:
            raise TrainingJobNotFoundError(command.job_id)

        run = job.current_run
        if run is None:
            raise TrainingJobNotFoundError(command.run_id)

        metrics = TrainingMetrics(values=dict(command.metrics))
        job.complete(
            run=run,
            metrics=metrics,
            artifact_uri=command.artifact_uri,
        )

        await self._repository.save(job)
        await self._event_publisher.publish_all(job.collect_events())

        logger.info(
            "TrainingJob completed: job_id=%s, run_id=%s",
            job.id,
            run.id,
        )
        return job


class FailTrainingUseCase:
    """
    標記 Training 失敗的 Use Case (Worker 回報)。

    :param repository: TrainingJob 持久化 Port。
    :param event_publisher: Domain Event 發佈 Port。
    """

    def __init__(
        self,
        repository: TrainingJobRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(self, command: FailTrainingCommand) -> TrainingJob:
        """
        標記 TrainingJob 為失敗。

        :param command: 失敗訓練的 Command。
        :return: 更新後的 TrainingJob。
        :raises TrainingJobNotFoundError: 若 Job 不存在。
        """
        job_id = EntityId.from_string(command.job_id)
        job = await self._repository.get(job_id)
        if job is None:
            raise TrainingJobNotFoundError(command.job_id)

        run = job.current_run
        if run is None:
            raise TrainingJobNotFoundError(command.run_id)

        job.fail(run=run, error_message=command.error_message)

        await self._repository.save(job)
        await self._event_publisher.publish_all(job.collect_events())

        logger.info(
            "TrainingJob failed: job_id=%s, error=%s",
            job.id,
            command.error_message,
        )
        return job


class CancelTrainingUseCase:
    """
    取消 Training 的 Use Case。

    :param repository: TrainingJob 持久化 Port。
    :param event_publisher: Domain Event 發佈 Port。
    """

    def __init__(
        self,
        repository: TrainingJobRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._repository = repository
        self._event_publisher = event_publisher

    async def execute(
        self,
        command: CancelTrainingCommand,
    ) -> TrainingJob:
        """
        取消 TrainingJob。

        :param command: 取消訓練的 Command。
        :return: 更新後的 TrainingJob。
        :raises TrainingJobNotFoundError: 若 Job 不存在。
        """
        job_id = EntityId.from_string(command.job_id)
        job = await self._repository.get(job_id)
        if job is None:
            raise TrainingJobNotFoundError(command.job_id)

        job.cancel()

        await self._repository.save(job)
        await self._event_publisher.publish_all(job.collect_events())

        logger.info(
            "TrainingJob cancelled: job_id=%s, reason=%s",
            job.id,
            command.reason,
        )
        return job
