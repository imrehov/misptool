export type EventState = {
  event_id: string
  info: string
  date: string
  timestamp: string
  publish_timestamp: string
  published: boolean
  threat_level_id: string
  analysis: string
  tag_names: string[]
  galaxy_tag_names: string[]
  attribute_count: number
  object_count: number
  score: number
  fingerprint: string
  misp_event_url: string
}

export type EventChange = {
  id?: number | null
  event_id: string
  change_type: string
  old_fingerprint: string | null
  new_fingerprint: string
  old_score: number | null
  new_score: number
  change_summary: string[]
  observed_at: string
}
