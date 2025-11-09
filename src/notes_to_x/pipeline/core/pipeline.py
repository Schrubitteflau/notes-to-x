"""Pipeline execution engine."""

import logging
from typing import Any, Dict, List
from .context import Context
from .stage import Stage, get_stage

logger = logging.getLogger(__name__)


class Pipeline:
    """
    Pipeline executor that flows contexts through stages.

    The pipeline handles:
    - Sequential stage execution
    - 1:N context splits (segmentation)
    - Error accumulation (resilient mode)
    - Stage finalization
    """

    def __init__(
        self,
        stages: List[Stage],
        fail_fast: bool = True,
        verbose: bool = True
    ):
        """
        Initialize pipeline with configured stages.

        Args:
            stages: List of stage instances
            fail_fast: If True, stop on first error. If False, continue and collect errors.
                      Default is True to ensure errors are caught early.
            verbose: If True, print progress messages
        """
        self.stages = stages
        self.fail_fast = fail_fast
        self.verbose = verbose

    def execute(self, contexts: List[Context]) -> List[Context]:
        """
        Execute pipeline on initial contexts.

        Args:
            contexts: Initial contexts (usually from source stage)

        Returns:
            Final contexts after all stages

        Raises:
            RuntimeError: If fail_fast=True and any stage raises an error
        """
        if not contexts:
            if self.verbose:
                logger.warning("No contexts to process")
            return []

        current_contexts = contexts

        for i, stage in enumerate(self.stages, 1):
            stage_name = stage.name
            if self.verbose:
                logger.info(f"\n[Stage {i}/{len(self.stages)}] {stage_name}")
                logger.info(f"  Input: {len(current_contexts)} context(s)")

            try:
                current_contexts = self._execute_stage(stage, current_contexts)

                # Check if any context has errors
                if self.fail_fast:
                    contexts_with_errors = [ctx for ctx in current_contexts if ctx.has_errors]
                    if contexts_with_errors:
                        error_details = []
                        for ctx in contexts_with_errors:
                            for error in ctx.meta.errors:
                                error_details.append(f"{error['stage']}: {error['message']}")

                        error_msg = f"Stage '{stage_name}' produced errors:\n  " + "\n  ".join(error_details[:3])
                        if len(error_details) > 3:
                            error_msg += f"\n  ... and {len(error_details) - 3} more errors"

                        raise RuntimeError(error_msg)

                if self.verbose:
                    logger.info(f"  Output: {len(current_contexts)} context(s)")

            except RuntimeError:
                # Re-raise RuntimeError from error checking above
                raise
            except Exception as e:
                error_msg = f"Stage '{stage_name}' failed: {e}"

                if self.fail_fast:
                    raise RuntimeError(error_msg) from e

                # Add error to all contexts and continue
                for ctx in current_contexts:
                    ctx.add_issue(error_msg, stage_name, severity="error", exception=str(e))

                if self.verbose:
                    logger.error(f"  ✗ Error: {error_msg}")

        # Finalize all stages (for cleanup/aggregation)
        for stage in self.stages:
            try:
                stage.finalize()
            except Exception as e:
                if self.verbose:
                    logger.error(f"  ✗ Finalize error in {stage.name}: {e}")

        return current_contexts

    def _execute_stage(self, stage: Stage, contexts: List[Context]) -> List[Context]:
        """
        Execute a single stage on all contexts.

        Handles both 1:1 transforms and 1:N splits.

        Args:
            stage: Stage to execute
            contexts: Input contexts

        Returns:
            Output contexts (may be more than input if stage splits)
        """
        results = []

        for ctx in contexts:
            # Mark context as processed by this stage
            ctx.mark_processed_by(stage.name)

            # Execute stage
            result = stage.execute(ctx)

            # Handle 1:N splits (segmentation)
            if isinstance(result, list):
                results.extend(result)
            else:
                results.append(result)

        return results

    @classmethod
    def from_config(cls, config: Dict[str, Any], **kwargs) -> 'Pipeline':
        """
        Create pipeline from configuration dictionary.

        Args:
            config: Pipeline configuration with 'pipeline' key containing stage definitions
            **kwargs: Additional pipeline options (fail_fast, verbose)

        Returns:
            Configured Pipeline instance

        Example config:
            {
                "pipeline": [
                    {"kind": "load.markdown", "options": {}},
                    {"kind": "segment.by_title", "options": {"level": 1}}
                ]
            }
        """
        pipeline_config = config.get("pipeline", [])

        stages = []
        for stage_def in pipeline_config:
            kind = stage_def["kind"]
            options = stage_def.get("options", {})

            stage = get_stage(kind, options)
            stages.append(stage)

        return cls(stages, **kwargs)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get pipeline execution summary.

        Returns:
            Dictionary with pipeline metadata
        """
        return {
            "total_stages": len(self.stages),
            "stages": [
                {
                    "name": stage.name,
                    "class": stage.__class__.__name__,
                }
                for stage in self.stages
            ],
            "fail_fast": self.fail_fast,
        }
