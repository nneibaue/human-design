"""Shared types for agent tools.

This module defines Pydantic models for common data structures used across
all agent tools. These types provide:
- Type safety for tool inputs/outputs
- Automatic validation at tool boundaries
- IDE autocomplete support
- Clear documentation via Field descriptions
"""

from pydantic import BaseModel, Field
from typing import Annotated
from pathlib import Path as PathType

# Custom type aliases for domain concepts
FilePath = Annotated[str, Field(description="Path to a file relative to workspace root")]
DirectoryPath = Annotated[str, Field(description="Path to a directory relative to workspace root")]
GitRef = Annotated[str, Field(description="Git reference (commit SHA, branch, tag)")]
SearchPattern = Annotated[str, Field(description="Search pattern (regex or plain text)")]


class FileContent(BaseModel):
    """Type-safe representation of file contents.
    
    Returned by read_file tool. Includes metadata for context.
    """
    path: FilePath
    content: str = Field(..., description="File contents as string")
    line_count: int = Field(..., ge=0, description="Number of lines in content")
    encoding: str = Field(default="utf-8", description="File encoding")
    size_bytes: int = Field(..., ge=0, description="Size of content in bytes")
    
    @property
    def lines(self) -> list[str]:
        """Split content into lines for easier processing."""
        return self.content.splitlines()


class WriteFileResult(BaseModel):
    """Result of write_file operation."""
    status: str = Field(default="success", description="Operation status")
    path: FilePath
    bytes_written: int = Field(..., ge=0, description="Number of bytes written")
    created_directories: list[DirectoryPath] = Field(
        default_factory=list,
        description="Parent directories created during write"
    )


class SearchMatch(BaseModel):
    """Single match from code search."""
    file_path: FilePath
    line_number: int = Field(..., ge=1, description="Line number (1-indexed)")
    line_content: str = Field(..., description="Content of matched line")
    context_before: list[str] = Field(
        default_factory=list,
        description="Lines before match (if context requested)"
    )
    context_after: list[str] = Field(
        default_factory=list,
        description="Lines after match (if context requested)"
    )


class SearchResult(BaseModel):
    """Result of grep/code search operation."""
    pattern: SearchPattern
    matches: list[SearchMatch] = Field(default_factory=list)
    total_matches: int = Field(..., ge=0, description="Total number of matches found")
    truncated: bool = Field(
        default=False,
        description="True if results were limited by max_results"
    )
    search_paths: list[str] = Field(
        default_factory=list,
        description="Paths that were searched"
    )


class GitCommit(BaseModel):
    """Representation of a Git commit."""
    sha: str = Field(..., min_length=7, max_length=40, description="Commit SHA")
    short_sha: str = Field(..., min_length=7, max_length=12, description="Short commit SHA")
    author: str = Field(..., description="Commit author name")
    email: str = Field(..., description="Commit author email")
    date: str = Field(..., description="Commit date (ISO 8601)")
    message: str = Field(..., description="Commit message")
    files_changed: list[str] = Field(
        default_factory=list,
        description="List of files changed in this commit"
    )


class GitLogResult(BaseModel):
    """Result of git log operation."""
    commits: list[GitCommit] = Field(default_factory=list)
    total_commits: int = Field(..., ge=0, description="Total commits in result")
    ref: GitRef | None = Field(None, description="Git reference used for log")
    truncated: bool = Field(
        default=False,
        description="True if commits were limited by max_commits"
    )


class GitFileContent(BaseModel):
    """Content of a file at a specific Git reference."""
    path: FilePath
    content: str = Field(..., description="File contents at specified ref")
    ref: GitRef = Field(..., description="Git reference where file was retrieved")
    sha: str = Field(..., description="Commit SHA of the ref")
    size_bytes: int = Field(..., ge=0, description="Size of content in bytes")


class GitTagInfo(BaseModel):
    """Information about a Git tag."""
    name: str = Field(..., description="Tag name")
    ref: str = Field(..., description="Full ref path (refs/tags/...)")
    commit_sha: str = Field(..., description="Commit SHA the tag points to")
    message: str | None = Field(None, description="Annotated tag message (if applicable)")
    tagger: str | None = Field(None, description="Tagger name (for annotated tags)")
    date: str | None = Field(None, description="Tag date (ISO 8601, for annotated tags)")


class DirectoryListing(BaseModel):
    """Result of listing directory contents."""
    path: DirectoryPath
    files: list[str] = Field(default_factory=list, description="Files in directory")
    directories: list[str] = Field(default_factory=list, description="Subdirectories")
    total_items: int = Field(..., ge=0, description="Total items in directory")
    hidden_items_included: bool = Field(
        default=False,
        description="Whether hidden files/dirs are included"
    )
