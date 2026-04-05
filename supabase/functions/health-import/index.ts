import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      { global: { headers: { Authorization: req.headers.get("Authorization")! } } }
    );

    const { data: { user }, error: authError } = await supabaseClient.auth.getUser();
    if (authError || !user) {
      return new Response(JSON.stringify({ error: "Unauthorized" }), {
        status: 401,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Parse request body
    const body = await req.json();
    const { provider, import_mode, raw_payload } = body;

    if (!provider || !import_mode || !raw_payload) {
      return new Response(
        JSON.stringify({ error: "Missing provider, import_mode, or raw_payload" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Store raw import record
    const { data: importRecord, error: importError } = await supabaseClient
      .from("provider_imports")
      .insert({
        user_id: user.id,
        provider,
        import_mode,
        raw_payload,
        status: "pending",
        imported_by: "user_upload",
      })
      .select()
      .single();

    if (importError) {
      return new Response(JSON.stringify({ error: importError.message }), {
        status: 400,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    // Normalize daily metrics from raw payload
    // Assume raw_payload is an array or object with daily records
    let dailyRecords: any[] = [];
    let recordCount = 0;
    let dateRangeStart = null;
    let dateRangeEnd = null;

    if (Array.isArray(raw_payload)) {
      dailyRecords = raw_payload;
    } else if (raw_payload.daily && Array.isArray(raw_payload.daily)) {
      dailyRecords = raw_payload.daily;
    } else if (raw_payload.data && Array.isArray(raw_payload.data)) {
      dailyRecords = raw_payload.data;
    } else {
      // Single record
      dailyRecords = [raw_payload];
    }

    // Build normalized metrics
    const metricsToInsert = dailyRecords
      .filter((r: any) => r.date)
      .map((record: any) => {
        const date = record.date; // Assume YYYY-MM-DD format
        if (!dateRangeStart || date < dateRangeStart) dateRangeStart = date;
        if (!dateRangeEnd || date > dateRangeEnd) dateRangeEnd = date;

        return {
          user_id: user.id,
          date,
          provider,
          recovery_score: record.recovery_score ?? null,
          readiness_label: record.readiness_label ?? null,
          hrv_ms: record.hrv_ms ?? null,
          resting_hr: record.resting_hr ?? null,
          sleep_hours: record.sleep_hours ?? null,
          sleep_performance_pct: record.sleep_performance_pct ?? null,
          daily_strain: record.daily_strain ?? null,
          step_count: record.step_count ?? null,
          import_id: importRecord.id,
        };
      });

    recordCount = metricsToInsert.length;

    // Upsert daily metrics (deduplicate by user_id, date, provider)
    if (metricsToInsert.length > 0) {
      const { error: metricsError } = await supabaseClient
        .from("daily_metrics")
        .upsert(metricsToInsert, { onConflict: "user_id,date,provider" });

      if (metricsError) {
        console.error("Metrics insert error:", metricsError);
        // Update import as partial/failed
        await supabaseClient
          .from("provider_imports")
          .update({ status: "partial", error_message: metricsError.message })
          .eq("id", importRecord.id);

        return new Response(
          JSON.stringify({
            error: "Failed to normalize metrics",
            details: metricsError.message,
          }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
      }
    }

    // Update provider_connections
    const { error: connError } = await supabaseClient
      .from("provider_connections")
      .upsert(
        {
          user_id: user.id,
          provider,
          connection_mode: import_mode,
          status: "manual_import",
          last_sync_at: new Date().toISOString(),
          sync_failed_count: 0,
        },
        { onConflict: "user_id,provider" }
      );

    if (connError) {
      console.error("Connection update error:", connError);
    }

    // Mark import as processed
    await supabaseClient
      .from("provider_imports")
      .update({
        status: "processed",
        record_count: recordCount,
        date_range_start: dateRangeStart,
        date_range_end: dateRangeEnd,
        processed_at: new Date().toISOString(),
      })
      .eq("id", importRecord.id);

    return new Response(
      JSON.stringify({
        ok: true,
        import_id: importRecord.id,
        record_count: recordCount,
        date_range: { start: dateRangeStart, end: dateRangeEnd },
        connection_status: "manual_import",
      }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Error:", error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
