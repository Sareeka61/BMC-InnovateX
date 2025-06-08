import React, { useState, useRef, useEffect } from 'react';
import * as tf from '@tensorflow/tfjs';
import * as cocoSsd from '@tensorflow-models/coco-ssd';

function App() {
  const [video, setVideo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [model, setModel] = useState(null);
  const [counts, setCounts] = useState({
    car: 0,
    truck: 0,
    ambulance: 0,
    person: 0,
    other: 0
  });
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    // Load the COCO-SSD model
    const loadModel = async () => {
      try {
        const loadedModel = await cocoSsd.load();
        setModel(loadedModel);
      } catch (error) {
        console.error('Error loading model:', error);
      }
    };
    loadModel();
  }, []);

  const handleVideoUpload = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('video/')) {
      alert('Please upload a valid video file');
      return;
    }

    // Validate file size (max 100MB)
    if (file.size > 100 * 1024 * 1024) {
      alert('File size should be less than 100MB');
      return;
    }

    const videoUrl = URL.createObjectURL(file);
    setVideo(videoUrl);
    setCounts({
      car: 0,
      truck: 0,
      ambulance: 0,
      person: 0,
      other: 0
    });
  };

  const processVideo = async () => {
    if (!video || !model) return;

    setIsProcessing(true);
    const videoElement = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    videoElement.onloadeddata = async () => {
      canvas.width = videoElement.videoWidth;
      canvas.height = videoElement.videoHeight;
    };

    const detectObjects = async () => {
      if (videoElement.paused || videoElement.ended) {
        setIsProcessing(false);
        return;
      }

      // Draw the current video frame
      ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

      // Detect objects
      const predictions = await model.detect(canvas);
      
      // Reset counts
      const newCounts = {
        car: 0,
        truck: 0,
        ambulance: 0,
        person: 0,
        other: 0
      };

      // Draw bounding boxes and count objects
      predictions.forEach(prediction => {
        const [x, y, width, height] = prediction.bbox;
        
        // Draw bounding box
        ctx.strokeStyle = '#00ff00';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, width, height);

        // Draw label
        ctx.fillStyle = '#00ff00';
        ctx.font = '16px Arial';
        ctx.fillText(
          `${prediction.class} (${Math.round(prediction.score * 100)}%)`,
          x, y > 20 ? y - 5 : y + 20
        );

        // Update counts
        switch (prediction.class) {
          case 'car':
            newCounts.car++;
            break;
          case 'truck':
            newCounts.truck++;
            break;
          case 'person':
            newCounts.person++;
            break;
          default:
            newCounts.other++;
        }
      });

      setCounts(newCounts);
      requestAnimationFrame(detectObjects);
    };

    videoElement.play();
    detectObjects();
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <div className="divide-y divide-gray-200">
              <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                <h1 className="text-3xl font-bold text-center mb-8">Vehicle Detection</h1>
                
                <div className="mb-4">
                  <input
                    type="file"
                    accept="video/*"
                    onChange={handleVideoUpload}
                    className="block w-full text-sm text-gray-500
                      file:mr-4 file:py-2 file:px-4
                      file:rounded-full file:border-0
                      file:text-sm file:font-semibold
                      file:bg-blue-50 file:text-blue-700
                      hover:file:bg-blue-100"
                  />
                </div>

                {video && (
                  <div className="space-y-4">
                    <video
                      ref={videoRef}
                      src={video}
                      className="w-full rounded-lg shadow-lg"
                      controls
                    />
                    <canvas
                      ref={canvasRef}
                      className="w-full rounded-lg shadow-lg"
                    />
                    <button
                      onClick={processVideo}
                      disabled={isProcessing}
                      className={`w-full py-2 px-4 rounded-lg text-white font-semibold ${
                        isProcessing
                          ? 'bg-gray-400 cursor-not-allowed'
                          : 'bg-blue-600 hover:bg-blue-700'
                      }`}
                    >
                      {isProcessing ? 'Processing...' : 'Start Detection'}
                    </button>
                  </div>
                )}

                <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                  <h2 className="text-xl font-semibold mb-2">Detection Counts:</h2>
                  <div className="grid grid-cols-2 gap-2">
                    <p>Cars: {counts.car}</p>
                    <p>Trucks: {counts.truck}</p>
                    <p>Humans: {counts.person}</p>
                    <p>Others: {counts.other}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App; 