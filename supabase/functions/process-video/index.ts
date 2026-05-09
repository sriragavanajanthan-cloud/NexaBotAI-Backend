import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

interface VideoRequest {
  video_url: string
  duration: number
  music_url?: string
  text_overlay?: string
}

serve(async (req: Request) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      },
    })
  }

  try {
    const { video_url, duration, music_url, text_overlay }: VideoRequest = await req.json()

    if (!video_url) {
      throw new Error('video_url is required')
    }

    console.log(`Processing video: ${video_url}`)
    console.log(`Duration: ${duration}s`)

    // Call your Render API to process the video
    const RENDER_API_URL = Deno.env.get('RENDER_API_URL') || 'https://nexabot-video-api.onrender.com'
    
    const response = await fetch(`${RENDER_API_URL}/assemble`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: "edge_function_video",
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
          'Access-Control-Allow-Origin': '*',
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
          'Access-Control-Allow-Origin': '*',
        },
      }
    )
  }
})
