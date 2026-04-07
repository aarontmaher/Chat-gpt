import "@supabase/functions-js/edge-runtime.d.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
}

type DayAggregate = {
  date: string
  hrvSum: number
  hrvCount: number
  rhrSum: number
  rhrCount: number
  sleepHours: number
  activeEnergyKcal: number
  stepCount: number
}

type AppleHealthDay = {
  date: string
  hrv_ms: number | null
  resting_hr: number | null
  sleep_hours: number | null
  active_energy_kcal: number | null
  step_count: number | null
  source: string
}

const MAX_HISTORY_DAYS_IN_RESPONSE = 180

function parseDateKey(raw: string): string | null {
  if (!raw) return null
  const ts = Date.parse(raw)
  if (Number.isNaN(ts)) {
    const fallback = String(raw).slice(0, 10)
    return /^\d{4}-\d{2}-\d{2}$/.test(fallback) ? fallback : null
  }
  return new Date(ts).toISOString().slice(0, 10)
}

function attr(tag: string, key: string): string {
  const rx = new RegExp(`${key}="([^"]*)"`)
  const m = tag.match(rx)
  return m ? m[1] : ""
}

function ensureDay(days: Map<string, DayAggregate>, key: string): DayAggregate {
  const existing = days.get(key)
  if (existing) return existing
  const created: DayAggregate = {
    date: key,
    hrvSum: 0,
    hrvCount: 0,
    rhrSum: 0,
    rhrCount: 0,
    sleepHours: 0,
    activeEnergyKcal: 0,
    stepCount: 0,
  }
  days.set(key, created)
  return created
}

function applyRecordTag(days: Map<string, DayAggregate>, recordTag: string) {
  const type = attr(recordTag, "type")
  if (!type) return
  const startRaw = attr(recordTag, "startDate") || attr(recordTag, "creationDate")
  const endRaw = attr(recordTag, "endDate") || startRaw
  const dateKey = parseDateKey(startRaw)
  if (!dateKey) return

  const valueRaw = attr(recordTag, "value")
  const value = Number(valueRaw)
  const day = ensureDay(days, dateKey)

  if (type.includes("HeartRateVariabilitySDNN") && Number.isFinite(value)) {
    day.hrvSum += value
    day.hrvCount += 1
    return
  }
  if (type.includes("RestingHeartRate") && Number.isFinite(value)) {
    day.rhrSum += value
    day.rhrCount += 1
    return
  }
  if (type.includes("ActiveEnergyBurned") && Number.isFinite(value)) {
    day.activeEnergyKcal += value
    return
  }
  if (type.includes("StepCount") && Number.isFinite(value)) {
    day.stepCount += Math.round(value)
    return
  }
  if (type.includes("SleepAnalysis")) {
    const sleepVal = String(valueRaw || "").toLowerCase()
    if (sleepVal.includes("asleep")) {
      const startTs = Date.parse(startRaw)
      const endTs = Date.parse(endRaw)
      if (Number.isFinite(startTs) && Number.isFinite(endTs) && endTs > startTs) {
        day.sleepHours += (endTs - startTs) / 3600000
      }
    }
  }
}

function processRecordTagsChunk(days: Map<string, DayAggregate>, chunk: string): string {
  let cursor = 0
  while (true) {
    const start = chunk.indexOf("<Record", cursor)
    if (start === -1) return ""
    const end = chunk.indexOf("/>", start)
    if (end === -1) return chunk.slice(start)
    const tag = chunk.slice(start, end + 2)
    applyRecordTag(days, tag)
    cursor = end + 2
  }
}

async function parseAppleXmlFile(file: File): Promise<{ latest: AppleHealthDay; history: AppleHealthDay[]; day_count: number }> {
  const days = new Map<string, DayAggregate>()
  const reader = file.stream().getReader()
  const decoder = new TextDecoder()
  let carry = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    carry += decoder.decode(value, { stream: true })
    carry = processRecordTagsChunk(days, carry)
    if (carry.length > 2048) {
      carry = carry.slice(-2048)
    }
  }
  carry += decoder.decode()
  processRecordTagsChunk(days, carry)

  const keys = Array.from(days.keys()).sort()
  if (!keys.length) {
    throw new Error("no_daily_data")
  }
  const history = keys.map((key) => {
    const day = days.get(key) as DayAggregate
    return {
      date: day.date,
      hrv_ms: day.hrvCount ? Math.round((day.hrvSum / day.hrvCount) * 10) / 10 : null,
      resting_hr: day.rhrCount ? Math.round((day.rhrSum / day.rhrCount) * 10) / 10 : null,
      sleep_hours: day.sleepHours > 0 ? Math.round(day.sleepHours * 100) / 100 : null,
      active_energy_kcal: day.activeEnergyKcal > 0 ? Math.round(day.activeEnergyKcal) : null,
      step_count: day.stepCount > 0 ? day.stepCount : null,
      source: "apple_health_backend_import",
    } satisfies AppleHealthDay
  })
  const latestDay = history[history.length - 1]
  return {
    latest: latestDay,
    history,
    day_count: keys.length,
  }
}

function normalizeDaysFromJsonPayload(payload: unknown): AppleHealthDay[] {
  let items: any[] = []
  if (Array.isArray(payload)) {
    items = payload
  } else if (payload && typeof payload === "object" && Array.isArray((payload as any).daily)) {
    items = (payload as any).daily
  } else if (payload && typeof payload === "object" && Array.isArray((payload as any).data)) {
    items = (payload as any).data
  } else if (payload && typeof payload === "object") {
    items = [payload]
  }
  const history = items
    .filter((item) => item && typeof item === "object" && item.date)
    .map((item) => ({
      date: String(item.date),
      hrv_ms: item.hrv_ms ?? null,
      resting_hr: item.resting_hr ?? item.resting_heart_rate ?? null,
      sleep_hours: item.sleep_hours ?? null,
      active_energy_kcal: item.active_energy_kcal ?? null,
      step_count: item.step_count ?? null,
      source: "apple_health_backend_import",
    } satisfies AppleHealthDay))
  if (!history.length) {
    throw new Error("invalid_json_payload")
  }
  history.sort((a, b) => a.date.localeCompare(b.date))
  return history
}

function buildUpsertPayload(day: AppleHealthDay, userId: string) {
  return {
    user_id: userId,
    date: String(day.date),
    provider: "apple_health",
    recovery_score: null,
    readiness_label: "unknown",
    hrv_ms: day.hrv_ms ?? null,
    resting_hr: day.resting_hr ?? null,
    sleep_hours: day.sleep_hours ?? null,
    sleep_performance_pct: null,
    daily_strain: day.active_energy_kcal != null
      ? Math.min(Number(day.active_energy_kcal) / 100, 21)
      : null,
    step_count: day.step_count ?? null,
    last_updated: new Date().toISOString(),
  }
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders })
  }
  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "method_not_allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }

  try {
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: req.headers.get("Authorization") ?? "" } } },
    )

    const { data: { user }, error: authError } = await supabase.auth.getUser()
    if (authError || !user) {
      return new Response(JSON.stringify({ error: "unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    const contentType = req.headers.get("content-type") || ""
    let latest: AppleHealthDay
    let historyDays: AppleHealthDay[]
    let dayCount = 1

    if (contentType.includes("multipart/form-data")) {
      const form = await req.formData()
      const uploaded = form.get("file")
      if (!(uploaded instanceof File)) {
        return new Response(JSON.stringify({ error: "file_required" }), {
          status: 400,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        })
      }
      const parsed = await parseAppleXmlFile(uploaded)
      latest = parsed.latest
      historyDays = parsed.history
      dayCount = parsed.day_count
    } else {
      const body = await req.json()
      historyDays = normalizeDaysFromJsonPayload(body?.raw_payload ?? body)
      latest = historyDays[historyDays.length - 1]
      dayCount = historyDays.length
    }

    const upsertPayload = historyDays.map((day) => buildUpsertPayload(day, user.id))

    const { error: upsertError } = await supabase
      .from("daily_metrics")
      .upsert(upsertPayload, { onConflict: "user_id,date,provider" })

    if (upsertError) {
      return new Response(JSON.stringify({ error: "daily_metrics_upsert_failed", details: upsertError.message }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      })
    }

    const historyDaysForResponse = historyDays.length > MAX_HISTORY_DAYS_IN_RESPONSE
      ? historyDays.slice(historyDays.length - MAX_HISTORY_DAYS_IN_RESPONSE)
      : historyDays

    return new Response(JSON.stringify({ ok: true, latest_day: latest, history_days: historyDaysForResponse, day_count: dayCount }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: (error as Error).message || "import_failed" }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    })
  }
})
