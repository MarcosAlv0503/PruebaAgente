export interface ResolutionMethodStats {
  deterministic: number;
  lightLlm: number;
  heavyLlm: number;
}

export interface ConfidenceStats {
  avg: number | null;
  high: number;
  medium: number;
  low: number;
}

export interface TypeStat {
  type: string;
  total: number;
  unresolved: number;
}

export interface TopicStat {
  topic: string;
  count: number;
  percent: number;
}

export interface ReportStats {
  total: number;
  minDate: string | null;
  maxDate: string | null;
  resolutionMethod: ResolutionMethodStats;
  confidence: ConfidenceStats;
  typeStats: TypeStat[];
  topTopics: TopicStat[];
}
