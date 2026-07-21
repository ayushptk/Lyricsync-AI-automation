import { NextResponse } from 'next/server';

export async function GET(request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  
  // Simulate polling a job status
  // In a real app, we would query Redis/BullMQ or our database
  
  return NextResponse.json({ 
    jobId: id,
    status: "completed",
    progress: 100,
    result: {
      projectId: "mock-123",
      stems: {
        vocals: "https://mock-url.com/vocals.wav",
        melody: "https://mock-url.com/melody.wav"
      },
      lyrics: [
        { text: "I said, ooh, I'm blinded by the lights", start: 2.1, end: 4.5 },
        { text: "No, I can't sleep until I feel your touch", start: 4.8, end: 8.2 }
      ]
    }
  });
}
