"""Git history tools for agents.

Provides type-safe Git operations:
- git_log: Get commit history
- git_show: Show file contents at specific ref
- git_tag: List or create Git tags
- git_diff: Show changes between refs
- git_blame: Show line-by-line commit history

All tools operate on a Git repository (validated at initialization).
"""

from dataclasses import dataclass
from pathlib import Path
from pydantic import Field
from pydantic_ai import RunContext
import subprocess
import logging
from datetime import datetime

from .types import (
    GitCommit,
    GitLogResult,
    GitFileContent,
    GitTagInfo,
    GitRef,
    FilePath,
)
from .base import (
    BaseToolDeps,
    validate_file_path,
    log_tool_call,
    log_tool_result,
)

logger = logging.getLogger(__name__)


@dataclass
class GitHistoryDeps(BaseToolDeps):
    """Dependencies for Git history operations.
    
    Inherits workspace_root from BaseToolDeps (should be repo root).
    """
    max_commits_default: int = 50
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate Git repository."""
        super().__post_init__()
        
        # Check that workspace is a git repo
        git_dir = self.workspace_root / ".git"
        if not git_dir.exists():
            raise ValueError(
                f"Workspace is not a Git repository: {self.workspace_root} "
                "(missing .git directory)"
            )
        
        if self.max_commits_default <= 0:
            raise ValueError("max_commits_default must be positive")
        
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


def _run_git_command(
    repo_path: Path,
    args: list[str],
    timeout: int = 30,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Run a git command in the repository.
    
    Args:
        repo_path: Path to git repository
        args: Git command arguments (e.g., ["log", "--oneline"])
        timeout: Command timeout in seconds
        check: Whether to raise on non-zero exit
        
    Returns:
        CompletedProcess with stdout/stderr
        
    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        subprocess.TimeoutExpired: If command times out
    """
    cmd = ["git", "-C", str(repo_path)] + args
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Git command failed: {' '.join(cmd)}\nStderr: {e.stderr}")
        raise
    except subprocess.TimeoutExpired as e:
        logger.error(f"Git command timed out after {timeout}s: {' '.join(cmd)}")
        raise


def register_git_history_tools(agent, deps: GitHistoryDeps) -> None:
    """Register Git history tools with an agent.
    
    Args:
        agent: Pydantic AI Agent instance
        deps: GitHistoryDeps configuration
        
    Registers:
        - git_log: Get commit history
        - git_show: Show file at specific ref
        - git_tag: List/create Git tags
        - git_diff: Show changes between refs
        - git_current_branch: Get current branch name
    """
    
    @agent.tool
    async def git_log(
        ctx: RunContext[GitHistoryDeps],
        ref: GitRef | None = None,
        max_commits: int | None = None,
        file_path: FilePath | None = None,
        author: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> GitLogResult:
        """Get Git commit history.
        
        Retrieves commit log with optional filtering by ref, file, author, date range.
        
        Args:
            ref: Git reference (branch, tag, SHA) to get log for (default: HEAD)
            max_commits: Maximum commits to return (default: 50)
            file_path: Filter to commits affecting this file
            author: Filter to commits by this author
            since: Filter to commits after this date (e.g., "2024-01-01", "1 week ago")
            until: Filter to commits before this date
            
        Returns:
            GitLogResult with commits list and metadata
            
        Raises:
            ValueError: If ref invalid or git command fails
        """
        log_tool_call(
            "git_log",
            ref=ref,
            max_commits=max_commits,
            file_path=file_path,
        )
        
        max_commits = max_commits or ctx.deps.max_commits_default
        ref = ref or "HEAD"
        
        # Build git log command
        # Format: %H (full SHA), %h (short SHA), %an (author name), %ae (email),
        #         %aI (ISO date), %s (subject), %b (body)
        format_str = "%H%x00%h%x00%an%x00%ae%x00%aI%x00%s%x00%b%x00"
        
        args = [
            "log",
            f"--format={format_str}",
            f"-n{max_commits}",
            ref,
        ]
        
        if author:
            args.append(f"--author={author}")
        if since:
            args.append(f"--since={since}")
        if until:
            args.append(f"--until={until}")
        if file_path:
            args.append("--")
            args.append(file_path)
        
        # Run git log
        try:
            result = _run_git_command(
                ctx.deps.workspace_root,
                args,
                timeout=ctx.deps.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Git log failed: {e.stderr}")
        
        # Parse commits
        commits = []
        if result.stdout.strip():
            commit_strings = result.stdout.strip().split("\x00\n")
            
            for commit_str in commit_strings:
                if not commit_str.strip():
                    continue
                
                parts = commit_str.split("\x00")
                if len(parts) < 7:
                    logger.warning(f"Malformed git log entry: {commit_str[:100]}")
                    continue
                
                sha, short_sha, author_name, email, date, subject, body = parts[:7]
                
                # Get files changed in this commit
                files_args = ["show", "--name-only", "--format=", sha]
                try:
                    files_result = _run_git_command(
                        ctx.deps.workspace_root,
                        files_args,
                        timeout=ctx.deps.timeout_seconds,
                    )
                    files_changed = [
                        f.strip()
                        for f in files_result.stdout.strip().splitlines()
                        if f.strip()
                    ]
                except subprocess.CalledProcessError:
                    files_changed = []
                
                # Combine subject and body into full message
                message = subject
                if body.strip():
                    message += "\n\n" + body.strip()
                
                commits.append(
                    GitCommit(
                        sha=sha,
                        short_sha=short_sha,
                        author=author_name,
                        email=email,
                        date=date,
                        message=message,
                        files_changed=files_changed,
                    )
                )
        
        truncated = len(commits) == max_commits
        result_obj = GitLogResult(
            commits=commits,
            total_commits=len(commits),
            ref=ref,
            truncated=truncated,
        )
        
        log_tool_result("git_log", success=True, commits=len(commits))
        return result_obj
    
    @agent.tool
    async def git_show(
        ctx: RunContext[GitHistoryDeps],
        ref: GitRef,
        file_path: FilePath,
    ) -> GitFileContent:
        """Show file contents at a specific Git reference.
        
        Retrieves file as it existed at a given commit/branch/tag.
        
        Args:
            ref: Git reference (commit SHA, branch, tag)
            file_path: Path to file relative to repository root
            
        Returns:
            GitFileContent with file contents at specified ref
            
        Raises:
            ValueError: If ref or file invalid, or file doesn't exist at ref
        """
        log_tool_call("git_show", ref=ref, file_path=file_path)
        
        # Validate file path format (even though it might not exist in current tree)
        try:
            validate_file_path(ctx.deps.workspace_root, file_path)
        except ValueError as e:
            raise ValueError(f"Invalid file path: {e}")
        
        # Get file contents at ref
        args = ["show", f"{ref}:{file_path}"]
        
        try:
            result = _run_git_command(
                ctx.deps.workspace_root,
                args,
                timeout=ctx.deps.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            if "does not exist" in e.stderr or "exists on disk" in e.stderr:
                raise ValueError(f"File {file_path} does not exist at ref {ref}")
            raise ValueError(f"Git show failed: {e.stderr}")
        
        content = result.stdout
        
        # Get commit SHA for the ref
        sha_args = ["rev-parse", ref]
        try:
            sha_result = _run_git_command(
                ctx.deps.workspace_root,
                sha_args,
                timeout=ctx.deps.timeout_seconds,
            )
            commit_sha = sha_result.stdout.strip()
        except subprocess.CalledProcessError:
            commit_sha = ref  # Fallback if rev-parse fails
        
        result_obj = GitFileContent(
            path=file_path,
            content=content,
            ref=ref,
            sha=commit_sha,
            size_bytes=len(content.encode("utf-8")),
        )
        
        log_tool_result("git_show", success=True, bytes=result_obj.size_bytes)
        return result_obj
    
    @agent.tool
    async def git_tag(
        ctx: RunContext[GitHistoryDeps],
        pattern: str | None = None,
        create_tag: str | None = None,
        tag_message: str | None = None,
        ref: GitRef = "HEAD",
    ) -> list[GitTagInfo]:
        """List or create Git tags.
        
        Without create_tag: Lists existing tags matching pattern.
        With create_tag: Creates a new tag at specified ref.
        
        Args:
            pattern: Filter tags by pattern (e.g., "v*" for version tags)
            create_tag: Name of tag to create (if provided)
            tag_message: Message for annotated tag (requires create_tag)
            ref: Git reference to tag (default: HEAD, used with create_tag)
            
        Returns:
            List of GitTagInfo for matching/created tags
            
        Raises:
            ValueError: If tag creation fails or invalid parameters
        """
        log_tool_call("git_tag", pattern=pattern, create_tag=create_tag)
        
        # Create tag mode
        if create_tag:
            args = ["tag"]
            
            if tag_message:
                args.extend(["-a", create_tag, "-m", tag_message, ref])
            else:
                args.extend([create_tag, ref])
            
            try:
                _run_git_command(
                    ctx.deps.workspace_root,
                    args,
                    timeout=ctx.deps.timeout_seconds,
                )
                logger.info(f"Created tag: {create_tag} at {ref}")
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Failed to create tag {create_tag}: {e.stderr}")
        
        # List tags mode
        list_args = ["tag", "-l"]
        if pattern:
            list_args.append(pattern)
        
        try:
            list_result = _run_git_command(
                ctx.deps.workspace_root,
                list_args,
                timeout=ctx.deps.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to list tags: {e.stderr}")
        
        tag_names = [t.strip() for t in list_result.stdout.splitlines() if t.strip()]
        
        # Get detailed info for each tag
        tags = []
        for tag_name in tag_names:
            # Get commit SHA for tag
            sha_args = ["rev-list", "-n", "1", tag_name]
            try:
                sha_result = _run_git_command(
                    ctx.deps.workspace_root,
                    sha_args,
                    timeout=ctx.deps.timeout_seconds,
                )
                commit_sha = sha_result.stdout.strip()
            except subprocess.CalledProcessError:
                commit_sha = "unknown"
            
            # Try to get annotated tag info
            show_args = ["show", tag_name, "--format=%an%x00%aI%x00%B", "--no-patch"]
            try:
                show_result = _run_git_command(
                    ctx.deps.workspace_root,
                    show_args,
                    timeout=ctx.deps.timeout_seconds,
                    check=False,
                )
                
                if show_result.returncode == 0 and "\x00" in show_result.stdout:
                    parts = show_result.stdout.strip().split("\x00")
                    tagger = parts[0] if len(parts) > 0 else None
                    date = parts[1] if len(parts) > 1 else None
                    message = parts[2] if len(parts) > 2 else None
                else:
                    tagger = None
                    date = None
                    message = None
            except subprocess.CalledProcessError:
                tagger = None
                date = None
                message = None
            
            tags.append(
                GitTagInfo(
                    name=tag_name,
                    ref=f"refs/tags/{tag_name}",
                    commit_sha=commit_sha,
                    message=message,
                    tagger=tagger,
                    date=date,
                )
            )
        
        log_tool_result("git_tag", success=True, tags=len(tags))
        return tags
    
    @agent.tool
    async def git_current_branch(
        ctx: RunContext[GitHistoryDeps],
    ) -> str:
        """Get the current Git branch name.
        
        Returns:
            Current branch name (e.g., "main", "develop")
            
        Raises:
            ValueError: If not on a branch (detached HEAD) or git fails
        """
        log_tool_call("git_current_branch")
        
        args = ["branch", "--show-current"]
        
        try:
            result = _run_git_command(
                ctx.deps.workspace_root,
                args,
                timeout=ctx.deps.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to get current branch: {e.stderr}")
        
        branch = result.stdout.strip()
        
        if not branch:
            raise ValueError("Not on a branch (detached HEAD state)")
        
        log_tool_result("git_current_branch", success=True, branch=branch)
        return branch
    
    @agent.tool
    async def git_diff(
        ctx: RunContext[GitHistoryDeps],
        ref1: GitRef = "HEAD",
        ref2: GitRef | None = None,
        file_path: FilePath | None = None,
        stat_only: bool = False,
    ) -> str:
        """Show changes between Git references.
        
        Compares two refs (or ref vs working tree if ref2 is None).
        
        Args:
            ref1: First Git reference (default: HEAD)
            ref2: Second Git reference (default: None = working tree)
            file_path: Limit diff to specific file
            stat_only: Only show file change statistics (not full diff)
            
        Returns:
            Diff output as string
            
        Raises:
            ValueError: If refs invalid or git fails
        """
        log_tool_call("git_diff", ref1=ref1, ref2=ref2, file_path=file_path)
        
        args = ["diff"]
        
        if stat_only:
            args.append("--stat")
        
        args.append(ref1)
        if ref2:
            args.append(ref2)
        
        if file_path:
            args.append("--")
            args.append(file_path)
        
        try:
            result = _run_git_command(
                ctx.deps.workspace_root,
                args,
                timeout=ctx.deps.timeout_seconds,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Git diff failed: {e.stderr}")
        
        diff_output = result.stdout
        
        log_tool_result("git_diff", success=True, bytes=len(diff_output))
        return diff_output
