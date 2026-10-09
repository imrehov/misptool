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
}
