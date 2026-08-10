"""
Training Context — Domain Exceptions。

定義 Training 領域中的業務邏輯錯誤，
所有例外皆繼承自共用的 ``TrainingDomainError``。
"""


class TrainingDomainError(Exception):
    """Training Context 的基底例外。"""

    pass


class InvalidStateTransitionError(TrainingDomainError):
    """
    Training Job 狀態機不允許的狀態轉換。

    例如：COMPLETED → RUNNING。
    """

    def __init__(self, current_state: str, target_state: str) -> None:
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(f"Invalid state transition: {current_state} → {target_state}")


class TrainingJobNotFoundError(TrainingDomainError):
    """指定的 TrainingJob 不存在。"""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Training job not found: {job_id}")


class TrainingRunNotFoundError(TrainingDomainError):
    """指定的 TrainingRun 不存在。"""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        super().__init__(f"Training run not found: {run_id}")
