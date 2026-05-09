import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'authorization, content-type, apikey, x-client-info',
  'Access-Control-Max-Age': '86400',
}

serve(async (req: Request) => {
  // Handle preflight OPTIONS request
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { video_url, duration, music_url, text_overlay } = await req.json()

    if (!video_url) {
      throw new Error('video_url is required')
    }

    console.log(`Processing video: ${video_url}`)
    console.log(`Duration: ${duration}s`)

    // Call your Render API
    const RENDER_API_URL = Deno.env.get('RENDER_API_URL') || 'https://nexabot-video-api.onrender.com'
    
    const response = await fetch(`${RENDER_API_URL}/assemble`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'User-Agent': 'Supabase-Edge-Function'
      },
      body: JSON.stringify({
        topic: "edge_function",
        video_url: video_url,
        duration: duration,
        quality: "standard",
        music: music_url,
        text_overlay: text_overlay
      })
    })

    const result = await response.json()

    return new Response(
      JSON.stringify({
        success: true,
        video_url: result.video_url,
        message: "Video processed successfully",
        duration: result.duration
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        },
      }
    )
  } catch (error) {
    console.error('Error:', error.message)
    
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders
        },
      }
    )
  }
})
