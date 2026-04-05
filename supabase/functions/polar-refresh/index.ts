import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  // Mock Polar refresh - return mock daily data
  const today = new Date().toISOString().slice(0, 10)

  const mockData = {
    date: today,
    recovery_score: Math.floor(Math.random() * 40) + 60, // 60-100
    hrv_ms: Math.floor(Math.random() * 20) + 40, // 40-60 ms
    resting_hr: Math.floor(Math.random() * 10) + 50, // 50-60 bpm
    sleep_hours: Math.floor(Math.random() * 3) + 6, // 6-9 hours
    sleep_performance_pct: Math.floor(Math.random() * 20) + 80, // 80-100%
    daily_strain: Math.floor(Math.random() * 10) + 5, // 5-15
    nightly_recharge_status: 'good',
    ans_charge: Math.floor(Math.random() * 6) - 3 // -3 to +3
  }

  return new Response(JSON.stringify(mockData), {
    headers: { 'Content-Type': 'application/json' }
  })
})