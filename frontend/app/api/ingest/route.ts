import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // Simulate accepting a youtube URL or File and queuing a BullMQ job
    // Return a mock job ID
    
    return NextResponse.json({ 
      success: true, 
      jobId: "mock-job-123",
      message: "Processing started."
    });
    
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
