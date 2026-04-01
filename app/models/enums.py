import enum


class SourceType(str, enum.Enum):
    HTML = "html"
    PDF = "pdf"
    HTML_PLUS_PDF = "html+pdf"
    UNKNOWN = "unknown"


class ArtifactType(str, enum.Enum):
    HTML = "html"
    JSON = "json"
    PDF = "pdf"


class FragmentType(str, enum.Enum):
    PARAGRAPH = "paragraph"
    BULLET = "bullet"
    TABLE_ROW = "table_row"
    CAPTION = "caption"


class SynonymSource(str, enum.Enum):
    MANUAL = "manual"
    EXTRACTED = "extracted"
    EXTERNAL = "external"


class RelationType(str, enum.Enum):
    EXPLICIT_ALTERNATIVE_SAME_LINE = "explicit_alternative_same_line"
    SAME_LINE_OPTION = "same_line_option"
    SWITCH_IF_INTOLERANCE = "switch_if_intolerance"
    SWITCH_IF_FAILURE = "switch_if_failure"
    LATER_LINE_ONLY = "later_line_only"
    ADD_ON_ONLY = "add_on_only"
    COMBINATION_ONLY = "combination_only"
    DIFFERENT_POPULATION = "different_population"
    NO_SUBSTITUTION_SIGNAL = "no_substitution_signal"


class ReviewStatus(str, enum.Enum):
    AUTO = "auto"
    REVIEWED = "reviewed"
    REJECTED = "rejected"


class PipelineStage(str, enum.Enum):
    DISCOVERY = "discovery"
    PROBE = "probe"
    FETCH = "fetch"
    NORMALIZE = "normalize"
    EXTRACT = "extract"
    SCORE = "score"
    REINDEX = "reindex"


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScopeType(str, enum.Enum):
    GLOBAL = "global"
    DISEASE = "disease"
    SPECIALTY = "specialty"
