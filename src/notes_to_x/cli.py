"""CLI for running note processing pipelines."""

import json
import os
import sys
from datetime import datetime

import typer
from dotenv import dotenv_values, load_dotenv

from .pipeline.core import Context, Pipeline, configure_logging, get_logger
from .pipeline.core.config import load_pipeline_config
from .pipeline.stages.sources.folder import FolderSource


def _mask_sensitive_env_vars(env_dict: dict[str, str | None]) -> dict[str, str]:
    """Mask sensitive environment variables for logging."""
    sensitive_patterns = ["API_KEY", "SECRET", "PASSWORD", "TOKEN"]
    return {
        k: "***MASKED***" if any(pattern in k.upper() for pattern in sensitive_patterns) else (v or "")
        for k, v in env_dict.items()
    }


def _write_json_file(filepath: str, data: dict | list) -> None:
    """Write data to JSON file with consistent formatting."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


app = typer.Typer(
    name="notes-to-x",
    help="Transform notes using configurable LLM pipelines",
    add_completion=False,
)


@app.command()
def run(
    config_path: str = typer.Argument(..., help="Path to pipeline.yaml configuration file"),
    source: str = typer.Option(
        None,
        "--source",
        "-s",
        help="Path to source folder or file (overrides config)",
    ),
    output_dir: str = typer.Option(
        "./pipeline_output",
        "--output-dir",
        "-o",
        help="Output directory for results (default: ./pipeline_output)",
    ),
    env_file: str | None = typer.Option(
        None,
        "--env",
        "-e",
        help="Path to .env file (default: .env in config directory)",
    ),
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--no-fail-fast",
        help="Stop on first error (default: true)",
    ),
    verbose: bool = typer.Option(
        True,
        "--verbose/--quiet",
        "-v/-q",
        help="Print progress messages",
    ),
):
    """Run a pipeline configuration on your notes."""

    # Configure structured logging
    configure_logging(verbose=verbose, json_output=False)
    logger = get_logger(__name__)

    # Capture actual command that was run
    command_args = " ".join(sys.argv)
    logger.info("Starting pipeline run", command=command_args)

    # Load environment variables
    config_dir = os.path.dirname(os.path.abspath(config_path))
    if env_file:
        env_path = env_file
    else:
        env_path = os.path.join(config_dir, ".env")

    loaded_env_vars = {}
    if os.path.exists(env_path):
        logger.info("Loading environment file", path=env_path)
        load_dotenv(env_path)
        # Capture loaded env vars with proper parsing and masking
        env_dict = dotenv_values(env_path)
        loaded_env_vars = _mask_sensitive_env_vars(env_dict)
        logger.debug("Environment variables loaded", count=len(loaded_env_vars))

    # Load pipeline configuration
    try:
        logger.info("Loading pipeline configuration", config_path=config_path)

        # Pass all environment variables as template variables
        template_vars = dict(os.environ)
        config = load_pipeline_config(config_path, variables=template_vars)
        logger.debug("Pipeline configuration loaded successfully", stages=len(config.get("stages", [])))

    except Exception as e:
        logger.error("Failed to load pipeline config", error=str(e), config_path=config_path)
        typer.echo(f"Error loading pipeline config: {e}", err=True)
        raise typer.Exit(1) from e

    # Create initial contexts from source
    contexts: list[Context] = []
    if source:
        # Override source from command line
        source_path = os.path.abspath(source)

        if os.path.isfile(source_path):
            # Single file
            contexts = [Context.from_file_path(source_path)]
            logger.info("Processing single file", path=source_path)
        elif os.path.isdir(source_path):
            # Directory - use FolderSource to collect files
            folder_source = FolderSource(
                {
                    "path": source_path,
                    "extensions": [".md", ".txt"],
                    "recursive": True,
                }
            )
            contexts = folder_source.generate()
            logger.info("Source files collected", count=len(contexts), source_path=source_path)
        else:
            typer.echo(f"Source not found: {source_path}", err=True)
            raise typer.Exit(1)
    else:
        # Try to get source from config or use default
        typer.echo("Error: --source is required", err=True)
        typer.echo("Specify a source folder or file with: --source notes/", err=True)
        raise typer.Exit(1)

    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_output_dir = os.path.join(output_dir, timestamp)
    os.makedirs(run_output_dir, exist_ok=True)

    # Create and run pipeline
    execution_start = datetime.now()
    try:
        pipeline = Pipeline.from_config(
            config,
            fail_fast=fail_fast,
            verbose=verbose,
        )

        logger.info(
            "Starting pipeline execution",
            stages=len(pipeline.stages),
            contexts=len(contexts),
            fail_fast=fail_fast,
        )

        # Change to config directory so relative paths work
        original_cwd = os.getcwd()
        os.chdir(config_dir)

        try:
            result_contexts = pipeline.execute(contexts)
            execution_end = datetime.now()
            execution_duration = (execution_end - execution_start).total_seconds()
            logger.info("Pipeline execution completed", duration_seconds=execution_duration)

            # Count errors and warnings
            error_count = sum(1 for ctx in result_contexts if ctx.has_errors)
            warning_count = sum(1 for ctx in result_contexts if ctx.has_warnings)

            # Collect all errors and warnings
            all_errors = []
            all_warnings = []
            for ctx in result_contexts:
                all_errors.extend(ctx.meta.errors)
                all_warnings.extend(ctx.meta.warnings)

            # Extract user-facing output (results only)
            user_output = []
            for ctx in result_contexts:
                for result in ctx.note.results:
                    if isinstance(result, dict):
                        # Add file and date info if not already present
                        if "file" not in result:
                            result["file"] = ctx.file.name
                        if "date" not in result and ctx.note.date:
                            result["date"] = ctx.note.date
                    user_output.append(result)

            # Write output.json (user-facing results)
            output_json_path = os.path.join(run_output_dir, "output.json")
            _write_json_file(output_json_path, user_output)
            logger.debug("Wrote output file", path=output_json_path, items=len(user_output))

            # Write result.json (full execution metadata)
            result_json = {
                "config": {
                    "command": command_args,
                    "timestamp": execution_start.isoformat(),
                    "duration_seconds": execution_duration,
                    "config_path": config_path,
                    "source": source,
                    "output_dir": run_output_dir,
                    "environment_variables": loaded_env_vars,
                },
                "execution_summary": {
                    "total_contexts": len(result_contexts),
                    "errors": error_count,
                    "warnings": warning_count,
                    "pipeline_stages": len(pipeline.stages),
                },
                "execution_results": [ctx.to_dict() for ctx in result_contexts],
                "errors": all_errors,
                "warnings": all_warnings,
            }

            result_json_path = os.path.join(run_output_dir, "result.json")
            _write_json_file(result_json_path, result_json)
            logger.debug("Wrote result file", path=result_json_path)

            # Log summary
            logger.info(
                "Pipeline run completed successfully",
                processed_contexts=len(result_contexts),
                duration_seconds=execution_duration,
                errors=error_count,
                warnings=warning_count,
                output_dir=run_output_dir,
            )

            if verbose:
                typer.echo("\n✓ Pipeline completed successfully!")
                typer.echo(f"  Processed: {len(result_contexts)} contexts")
                typer.echo(f"  Duration: {execution_duration:.2f}s")
                if error_count:
                    typer.echo(f"  Errors: {error_count}")
                if warning_count:
                    typer.echo(f"  Warnings: {warning_count}")
                typer.echo(f"\n📁 Output directory: {run_output_dir}")
                typer.echo(f"  - output.json: User-facing results ({len(user_output)} items)")
                typer.echo("  - result.json: Full execution details")

        finally:
            os.chdir(original_cwd)

    except RuntimeError as e:
        logger.error("Pipeline execution failed", error=str(e), exc_info=True)
        typer.echo(f"\n✗ Pipeline failed: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        logger.error("Unexpected error during pipeline execution", error=str(e), exc_info=True)
        typer.echo(f"\n✗ Unexpected error: {e}", err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise typer.Exit(1) from e


@app.command()
def list_stages():
    """List all available pipeline stages."""
    from .pipeline.core import get_stage_info, list_stages

    typer.echo("Available pipeline stages:\n")

    for kind in list_stages():
        info = get_stage_info(kind)
        typer.echo(f"  {kind}")
        typer.echo(f"    Class: {info['class']}")
        if info["docstring"]:
            # First line of docstring
            first_line = info["docstring"].strip().split("\n")[0]
            typer.echo(f"    {first_line}")
        typer.echo()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
