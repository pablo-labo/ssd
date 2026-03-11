from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    model: str
    draft_model: str | None = None
    max_num_seqs: int = 1
    max_model_len: int = 8192
    num_gpus: int = 1
    enforce_eager: bool = False
    speculate: bool = False
    speculate_k: int = 1
    draft_async: bool = False
    async_fan_out: int = 2
    verbose: bool = False
    max_steps: int | None = None

    def __post_init__(self) -> None:
        if not Path(self.model).is_dir():
            raise FileNotFoundError(f"Model path does not exist: {self.model}")
        if self.draft_model is not None and not Path(self.draft_model).is_dir():
            raise FileNotFoundError(f"Draft model path does not exist: {self.draft_model}")
        if self.num_gpus < 1:
            raise ValueError("num_gpus must be >= 1")
        if self.max_num_seqs < 1:
            raise ValueError("max_num_seqs must be >= 1")
        if self.max_model_len < 1:
            raise ValueError("max_model_len must be >= 1")
        if self.speculate_k < 1:
            raise ValueError("speculate_k must be >= 1")
        if self.draft_async and self.num_gpus < 2:
            raise ValueError("draft_async requires at least 2 GPUs")
        if self.speculate and self.draft_model is None:
            raise ValueError("speculate=True requires draft_model")
