"""
Pydantic models for the transcription pipeline.

These models represent transcription jobs, results, and pipeline state
for the AWS Batch transcription workflow that processes YouTube audio
with faster-whisper.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field


JobStatus = Literal[
    "SUBMITTED",
    "PENDING",
    "RUNNABLE",
    "STARTING",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
]


class TranscriptionSegment(BaseModel):
    """A single transcribed segment with timestamps."""

    model_config = ConfigDict(frozen=True)

    start: float
    end: float
    text: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration(self) -> float:
        """Duration of this segment in seconds."""
        return self.end - self.start


class TranscriptionResult(BaseModel):
    """
    Output of a single file transcription.

    Matches the JSON structure produced by parallel_transcribe.py.
    """

    model_config = ConfigDict(frozen=True)

    file: str = Field(description="Audio file name")
    language: str = Field(description="Detected language code")
    language_probability: float = Field(description="Confidence of language detection")
    duration_seconds: float = Field(description="Total audio duration in seconds")
    transcription_time_seconds: float = Field(description="Wall-clock time to transcribe")
    segments: list[TranscriptionSegment] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def segment_count(self) -> int:
        """Number of segments in the transcription."""
        return len(self.segments)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def full_text(self) -> str:
        """Concatenated text from all segments."""
        return " ".join(seg.text for seg in self.segments)


class TranscriptionJob(BaseModel):
    """An AWS Batch transcription job."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    job_name: str
    s3_input_uri: str
    s3_output_uri: str
    status: JobStatus = "SUBMITTED"
    created_at: datetime = Field(default_factory=datetime.now)
    channel_name: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_terminal(self) -> bool:
        """Whether the job has reached a final state."""
        return self.status in ("SUCCEEDED", "FAILED")


class ChannelDownload(BaseModel):
    """Metadata about a downloaded YouTube channel's audio files."""

    channel_name: str
    youtube_url: str = ""
    local_audio_dir: str = ""
    file_count: int = 0
    s3_prefix: str = ""


class TranscriptionPipeline(BaseModel):
    """
    Top-level view of a transcription pipeline run for a channel.

    Tracks downloads, jobs, and provides summary status.
    """

    channel_name: str
    download: ChannelDownload | None = None
    jobs: list[TranscriptionJob] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_jobs(self) -> int:
        return len(self.jobs)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def succeeded(self) -> int:
        return sum(1 for j in self.jobs if j.status == "SUCCEEDED")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def failed(self) -> int:
        return sum(1 for j in self.jobs if j.status == "FAILED")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def in_progress(self) -> int:
        return sum(1 for j in self.jobs if not j.is_terminal)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_complete(self) -> bool:
        """Whether all jobs have reached a terminal state."""
        return len(self.jobs) > 0 and all(j.is_terminal for j in self.jobs)
