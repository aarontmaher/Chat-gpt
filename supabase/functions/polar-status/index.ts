import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  // Mock Polar status - return connected with mock data
  const mockStatus = {
    connected: true,
    last_sync_at: new Date().toISOString(),
    latest_date: new Date().toISOString().slice(0, 10),
    status_text: 'Mock Polar connection active',
    provider: 'polar'
  }

  return new Response(JSON.stringify(mockStatus), {
    headers: { 'Content-Type': 'application/json' }
  })
})