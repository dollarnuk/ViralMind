class ViralMindError(Exception):
    """Base exception for the project."""
    pass

class DownloadError(ViralMindError):
    """Raised when video download fails."""
    pass

class AnalysisError(ViralMindError):
    """Raised when video analysis fails."""
    pass

class CroppingError(ViralMindError):
    """Raised when video cropping fails."""
    pass

class TaskError(ViralMindError):
    """Raised for task-related failures."""
    pass
